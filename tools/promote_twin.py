#!/usr/bin/env python3
"""Make the time-lapse twin's life the main Crow's life, after a full backup.

    python3 tools/promote_twin.py

Stop the real Crow first (Ctrl+C in his window). This:
1. backs up the real save, event log and reading archive to backups/before-twin-<time>/;
2. copies the twin's save, event log and reading archive into the real folder;
3. keeps the twin's calendar as his own clock (he continues from the twin's date);
4. records an event saying his life continued from the twin, so the history is honest.

Anything the real Crow lived after the twin was copied stays only in that backup.
"""
import json
import shutil
import socket
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def crow_running(port=8765):
    with socket.socket() as s:
        s.settimeout(.5)
        return s.connect_ex(('127.0.0.1', port)) == 0


def promote(real, twin, at=None, confirm=True):
    at = at or datetime.now().astimezone()
    tsave = json.loads((twin / 'crow-save.json').read_text())
    meta = tsave.pop('twin', None)
    if not meta:
        raise SystemExit('That folder is not a time-lapse twin.')
    if confirm and input(f"Replace the real Crow's life with the twin's (twin clock {meta.get('virtual_now', '')[:16]})? "
                         "A backup is made first. Type yes: ").strip().lower() != 'yes':
        raise SystemExit('Nothing changed.')
    backup = real / 'backups' / f"before-twin-{at:%Y%m%d-%H%M%S}"
    backup.mkdir(parents=True)
    for name in ['crow-save.json', 'crow-events.jsonl', 'crow-config.json']:
        if (real / name).exists():
            shutil.copy2(real / name, backup / name)
    if (real / 'crow-reading').is_dir():
        shutil.copytree(real / 'crow-reading', backup / 'crow-reading')
    # His spending record is about the real world, not the twin's.
    real_save = json.loads((real / 'crow-save.json').read_text()) if (real / 'crow-save.json').exists() else {}
    tsave['model_spend'] = real_save.get('model_spend', tsave.get('model_spend'))
    virtual = meta.get('virtual_now') or meta['started_virtual']
    tsave['crow_clock'] = {'virtual': virtual, 'started_real': at.isoformat(), 'from_twin': True}
    tsave['paused'] = True
    note = {'id': tsave['next_memory_id'], 'at': virtual, 'day': tsave.get('day'), 'time': virtual[11:16], 'kind': 'note',
            'event': f"His life continued from the time-lapse twin (simulated {meta['started_virtual'][:10]} to {virtual[:10]}). "
                     f"Jordan chose to keep that life; the earlier real-time life is in {backup.name}.", 'reason': ''}
    tsave['next_memory_id'] += 1
    tsave['memories'].append(note)
    shutil.copy2(twin / 'crow-events.jsonl', real / 'crow-events.jsonl')
    with (real / 'crow-events.jsonl').open('a') as out:
        out.write(json.dumps(note, ensure_ascii=False) + '\n')
    if (twin / 'crow-reading').is_dir():
        shutil.copytree(twin / 'crow-reading', real / 'crow-reading', dirs_exist_ok=True)
    tmp = real / 'crow-save.tmp'
    tmp.write_text(json.dumps(tsave, indent=2, ensure_ascii=False))
    tmp.replace(real / 'crow-save.json')
    return backup


def main():
    twin = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path('~/crow-twin').expanduser()
    if crow_running():
        sys.exit('Crow is still running. Stop him with Ctrl+C in his window first.')
    backup = promote(ROOT, twin)
    print(f'Done. Backup of the previous life: {backup}. Start Crow again with python3 crow.py --lan.')


if __name__ == '__main__':
    main()
