"""Copy an existing local Crow life into this checkout without overwriting data."""
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parent
source = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) == 2 else None
if source is None or not source.is_dir():
    raise SystemExit('Usage: python3 migrate_save.py /path/to/old/crow-world')
if source == root:
    raise SystemExit('Source and destination are the same folder; nothing to migrate.')
items = list(source.glob('crow-save*.json'))
items += [source / n for n in ['crow-events.jsonl', 'crow-reading', 'crow-config.json'] if (source / n).exists()]
if not (source / 'crow-save.json').exists():
    raise SystemExit('No crow-save.json found. Check the old project folder.')
conflicts = [p.name for p in items if (root / p.name).exists()]
if conflicts:
    raise SystemExit('No files copied; destination already contains: ' + ', '.join(conflicts))
for p in items:
    if p.is_dir():
        shutil.copytree(p, root / p.name)
    else:
        shutil.copy2(p, root / p.name)
print('Copied local life data. The original folder is unchanged.')
