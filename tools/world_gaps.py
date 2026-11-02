#!/usr/bin/env python3
"""Where Crow looked for more than the world holds, most repeated first. Read-only.

    cd ~/Crows-Nest && python3 tools/world_gaps.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORDS = {'seen_all': 'Had seen everything about', 'not_found': 'Looked for something not there',
         'not_here': 'Looked in the wrong place for', 'unanswered': 'Question not answered by the'}

save = ROOT / 'crow-save.json'
if not save.exists():
    raise SystemExit('Run this from your Crows-Nest folder, where crow-save.json lives.')
gaps = json.loads(save.read_text()).get('world_gaps', [])
if not gaps:
    print('He has not reached the edge of anything yet.')
for g in sorted(gaps, key=lambda g: (-g['times'], g.get('last', ''))):
    print(f"{g['times']:>3}×  {WORDS.get(g['kind'], g['kind'])} {g.get('target') or ''}  (last {g.get('last', '')[:16]})")
    for f in g.get('focuses', [])[-3:]:
        print(f'       “{f}”')
