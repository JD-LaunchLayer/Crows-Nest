"""Owner-triggered fixed-repository update; no commands or paths accepted over HTTP."""
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ORIGINS = {
    'https://github.com/JD-LaunchLayer/Crows-Nest.git',
    'https://github.com/JD-LaunchLayer/Crows-Nest',
    'git@github.com:JD-LaunchLayer/Crows-Nest.git',
}
ACTIVE = {'checking','backing_up','pulling','restarting'}
STATUS_FILE = 'crow-update-status.json'


def git(root, *args):
    env=os.environ.copy();env['GIT_TERMINAL_PROMPT']='0'
    result=subprocess.run(['git',*args],cwd=root,capture_output=True,text=True,timeout=120,env=env)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or 'Git command failed').strip()[-1800:])
    return result.stdout.strip()


def backup_life(root):
    root=Path(root)
    destination=root/'backups'/datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    items=list(root.glob('crow-save*.json'))
    items += [root/n for n in ['crow-events.jsonl','crow-reading','crow-config.json'] if (root/n).exists()]
    destination.mkdir(parents=True,exist_ok=False)
    for p in items:
        if p.is_dir():shutil.copytree(p,destination/p.name)
        else:shutil.copy2(p,destination/p.name)
    return str(destination.relative_to(root))


def save_status(root, status):
    target=Path(root)/STATUS_FILE;temp=target.with_suffix('.tmp')
    temp.write_text(json.dumps(status,indent=2));temp.replace(target)


def load_status(root):
    try:
        result=json.loads((Path(root)/STATUS_FILE).read_text())
        return result if isinstance(result,dict) else {'status':'idle'}
    except (OSError,ValueError):return {'status':'idle'}


def update_checkout(root, report, allowed_origins=ORIGINS):
    """Call from a paused/saved app. Return a verified update result or raise.

    allowed_origins is injectable only by local tests, never by a web request.
    """
    root=Path(root).resolve()
    report(status='checking',message='Checking the Crow checkout…')
    if Path(git(root,'rev-parse','--show-toplevel')).resolve()!=root:
        raise RuntimeError('Crow must run from the root of its Git checkout.')
    if git(root,'symbolic-ref','--short','HEAD')!='main':
        raise RuntimeError('Updates require the main branch. Local work has been preserved.')
    if git(root,'remote','get-url','origin') not in allowed_origins:
        raise RuntimeError('Origin is not the configured Crows-Nest repository. No code was downloaded.')
    if git(root,'status','--porcelain','--untracked-files=no'):
        raise RuntimeError('Tracked source files have local edits. No changes were overwritten.')
    before=git(root,'rev-parse','HEAD')
    report(status='backing_up',message='Backing up Crow’s saved life…',before=before)
    backup=backup_life(root)
    report(status='pulling',message='Downloading a fast-forward update…',backup=backup,before=before)
    # Explicit fixed remote/branch; no executable parameters are supplied by the client.
    git(root,'pull','--ff-only','origin','main')
    after=git(root,'rev-parse','HEAD')
    return {'before':before,'after':after,'backup':backup,'changed':before!=after}
