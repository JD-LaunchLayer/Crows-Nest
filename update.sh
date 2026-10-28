#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo 'Tracked source files have local edits. Stopping so they are preserved.'
  exit 1
fi
python3 - <<'PY'
from pathlib import Path
from datetime import datetime
import shutil
root = Path.cwd()
backup = root / 'backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
items = list(root.glob('crow-save*.json'))
items += [root / n for n in ['crow-events.jsonl', 'crow-reading', 'crow-config.json'] if (root / n).exists()]
if items:
    backup.mkdir(parents=True)
    for p in items:
        if p.is_dir(): shutil.copytree(p, backup / p.name)
        else: shutil.copy2(p, backup / p.name)
    print('Local life data backed up to', backup.relative_to(root))
PY
git pull --ff-only
