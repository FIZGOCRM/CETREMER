"""Private consistent SQLite snapshot, media and recovery keys."""
import json
import os
from pathlib import Path
import shutil
import re
from datetime import datetime, timezone
from core.sqlite_backup import backup_database


def create_bundle(database, media, destination, keys):
    destination=Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    estimated=Path(database).stat().st_size+sum(p.stat().st_size for p in Path(media).rglob('*') if p.is_file())
    if shutil.disk_usage(destination.parent).free < estimated+2*1024**3:
        raise OSError('Backup refused: preserve at least 2 GiB of free space on the shared VPS disk.')
    staging=destination.with_name('.partial-'+destination.name)
    staging.mkdir(mode=0o700)
    try:
        backup_database(database,staging/'db.sqlite3')
        shutil.copytree(media,staging/'media')
        key_file=staging/'keys.json'
        with key_file.open('x',encoding='utf8') as stream:
            os.chmod(key_file,0o600)
            json.dump(keys,stream)
        (staging/'manifest.json').write_text(json.dumps({'kind':'gomut-backup-v1','created_utc':datetime.now(timezone.utc).isoformat(),'database':'db.sqlite3','media':'media','keys':'keys.json'}),encoding='utf8')
        staging.rename(destination)
    except BaseException:
        shutil.rmtree(staging)
        raise
    return destination


def prune_completed(root,keep=14):
    completed=[]
    for folder in Path(root).iterdir():
        if folder.is_symlink() or not folder.is_dir() or not re.fullmatch(r'\d{8}T\d{12}Z',folder.name):
            continue
        try:
            manifest=json.loads((folder/'manifest.json').read_text())
        except (OSError,ValueError):
            continue
        if manifest.get('kind')=='gomut-backup-v1':
            completed.append(folder)
    for folder in sorted(completed)[:-keep]:
        shutil.rmtree(folder)


def main():
    import fcntl
    os.umask(0o077)
    root=Path('/data/backups')
    lock=(root/'.backup.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for orphan in root.glob('.partial-*'):
        if orphan.is_dir() and not orphan.is_symlink():
            shutil.rmtree(orphan)
    destination=root/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    create_bundle(os.environ['DJANGO_DATABASE_PATH'],os.environ['DJANGO_MEDIA_ROOT'],destination,{name:os.environ[name] for name in ('SECRET_KEY','FIELD_ENCRYPTION_KEY')})
    prune_completed(root)
    print(f'Consistent backup created: {destination.name}; integrity_check=ok',flush=True)


if __name__=='__main__':
    main()
