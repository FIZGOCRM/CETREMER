from datetime import datetime
import importlib
import json
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch
import subprocess
from django.test import SimpleTestCase


class DeploymentJobsTests(SimpleTestCase):
    def module(self,name):
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError:
            self.fail(f'Deployment operational module is missing: {name}')

    def test_initial_afternoon_tick_runs_each_job_once(self):
        jobs=self.module('deploy.jobs')
        self.assertEqual(jobs.due_jobs(datetime(2026,11,17,14,22),{}),[
            ('run_daily_notifications','2026-11-17'),('run_live_reminders','2026-11-17T14:15'),('backup','2026-11-17')])

    def test_completed_slot_is_not_repeated(self):
        jobs=self.module('deploy.jobs')
        state={'run_daily_notifications':'2026-11-17','run_live_reminders':'2026-11-17T14:15','backup':'2026-11-17'}
        self.assertEqual(jobs.due_jobs(datetime(2026,11,17,14,29),state),[])
        self.assertEqual(jobs.due_jobs(datetime(2026,11,17,14,30),state),[('run_live_reminders','2026-11-17T14:30')])

    def test_one_timeout_does_not_starve_other_jobs(self):
        jobs=self.module('deploy.jobs')
        self.assertTrue(hasattr(jobs,'run_pending'),'A failed job must be isolated from subsequent work')
        def runner(command,timeout):
            if 'run_daily_notifications' in command:
                raise subprocess.TimeoutExpired(command,timeout)
            return subprocess.CompletedProcess(command,0)
        state={}
        jobs.run_pending(datetime(2026,11,17,14,22),state,runner=runner)
        self.assertNotIn('run_daily_notifications',state)
        self.assertEqual(state['run_live_reminders'],'2026-11-17T14:15')
        self.assertEqual(state['backup'],'2026-11-17')

    def test_incomplete_backup_is_not_published(self):
        backup=self.module('deploy.backup_bundle')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            db=root/'live.sqlite3'
            sqlite3.connect(db).close()
            (root/'media').mkdir()
            with patch('deploy.backup_bundle.shutil.copytree',side_effect=OSError('simulated disk error')):
                with self.assertRaises(OSError):
                    backup.create_bundle(db,root/'media',root/'snapshot',{})
            self.assertFalse((root/'snapshot').exists(),'An incomplete recovery folder must not be published')
            self.assertFalse(list(root.glob('.partial-*')))

    def test_low_disk_space_prevents_new_backup(self):
        backup=self.module('deploy.backup_bundle')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            db=root/'live.sqlite3'
            sqlite3.connect(db).close()
            (root/'media').mkdir()
            with patch('deploy.backup_bundle.shutil.disk_usage',return_value=__import__('collections').namedtuple('Usage','total used free')(100,99,1)):
                with self.assertRaises(OSError):
                    backup.create_bundle(db,root/'media',root/'snapshot',{})
            self.assertFalse((root/'snapshot').exists())

    def test_retention_only_prunes_own_completed_snapshots(self):
        backup=self.module('deploy.backup_bundle')
        self.assertTrue(hasattr(backup,'prune_completed'))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            foreign=root/'unrelated'
            foreign.mkdir()
            for number in range(16):
                p=root/f'202611{number+1:02}T000000000000Z'
                p.mkdir()
                (p/'manifest.json').write_text(json.dumps({'kind':'gomut-backup-v1'}))
            backup.prune_completed(root,keep=14)
            self.assertTrue(foreign.exists())
            self.assertEqual(len(list(root.glob('*/manifest.json'))),14)

    def test_backup_includes_consistent_database_uploads_and_keys(self):
        backup=self.module('deploy.backup_bundle')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            db=root/'live.sqlite3'
            connection=sqlite3.connect(db)
            connection.execute('create table sample(value text)')
            connection.execute("insert into sample values ('persistent')")
            connection.commit()
            connection.close()
            media=root/'media'
            media.mkdir()
            (media/'private.pdf').write_bytes(b'%PDF')
            result=backup.create_bundle(db,media,root/'snapshot',{'SECRET_KEY':'test-only','FIELD_ENCRYPTION_KEY':'test-only'})
            restored=sqlite3.connect(result/'db.sqlite3')
            self.assertEqual(restored.execute('select value from sample').fetchall(),[('persistent',)])
            self.assertEqual(restored.execute('pragma integrity_check').fetchone(),('ok',))
            restored.close()
            self.assertEqual((result/'media/private.pdf').read_bytes(),b'%PDF')
            self.assertEqual(json.loads((result/'keys.json').read_text())['FIELD_ENCRYPTION_KEY'],'test-only')
            with self.assertRaises(FileExistsError):
                backup.create_bundle(db,media,result,{})
