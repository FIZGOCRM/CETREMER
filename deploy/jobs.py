"""One scheduler, a persistent checkpoint, and exclusive lock across restarts."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from zoneinfo import ZoneInfo


def due_jobs(now,state):
    day=now.strftime('%Y-%m-%d')
    slot=now.replace(minute=now.minute//15*15).strftime('%Y-%m-%dT%H:%M')
    result=[]
    if now.hour>=4 and state.get('run_daily_notifications')!=day:
        result.append(('run_daily_notifications',day))
    if state.get('run_live_reminders')!=slot:
        result.append(('run_live_reminders',slot))
    if (now.hour,now.minute)>=(4,15) and state.get('backup')!=day:
        result.append(('backup',day))
    return result


def run_pending(now,state,runner=subprocess.run):
    for name,stamp in due_jobs(now,state):
        command=[sys.executable,'-B','-m','deploy.backup_bundle'] if name=='backup' else [sys.executable,'-B','manage.py',name]
        print(f'{datetime.now(timezone.utc).isoformat()} START {name}',flush=True)
        try:
            result=runner(command,timeout=300)
            exit_code=result.returncode
        except (subprocess.TimeoutExpired,OSError):
            exit_code=124
        print(f'{datetime.now(timezone.utc).isoformat()} END {name} exit={exit_code}',flush=True)
        if exit_code==0:
            state[name]=stamp


def main():
    import fcntl
    os.umask(0o077)
    folder=Path('/data/run')
    checkpoint=folder/'jobs.json'
    lock=(folder/'scheduler.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=json.loads(checkpoint.read_text()) if checkpoint.exists() else {}
    zone=ZoneInfo('America/Campo_Grande')
    while True:
        run_pending(datetime.now(zone),state)
        temporary=checkpoint.with_suffix('.tmp')
        temporary.write_text(json.dumps(state),encoding='utf8')
        temporary.replace(checkpoint)
        time.sleep(30)


if __name__=='__main__':
    main()
