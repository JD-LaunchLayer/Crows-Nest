"""Print the world's character sheet for birds, deer and foods (for Jordan; Crow never sees this).

    python3 tools/wildlife_sheet.py            the sheet
    python3 tools/wildlife_sheet.py --live     also how much each bird trusts him and the herd now (reads the save, never writes)
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import wildlife

sheet = wildlife.sheet()
print('BIRDS (Crow only ever sees the look)')
for b in sheet['birds']:
    print(f"  {b['id']:8} {b['species']:20} wariness {b['wariness']:.2f}  eats {', '.join(b['diet'])}\n           looks like: {b['look']}")
d = sheet['deer']
print(f"\nDEER: {d['species']}, wariness {d['wariness']}, eats {', '.join(d['diet'])}; carcass about {d['carcass_kg']} kg, "
      f"about {d['meat_servings']} servings of meat; a carcass keeps about {d['carcass_keeps_days']} cool days; the woods hold {d['herd_capacity']}")
print('\nFOODS (fill per serving; the old single serving was 22)')
for k, f in sheet['foods'].items():
    print(f"  {f['name']:32} fill {f['fill']:>3}   keeps {('months' if f['keeps'] is None else str(f['keeps']) + ' cool days')}")
if '--live' in sys.argv:
    save = ROOT / 'crow-save.json'
    state = json.loads(save.read_text())
    w = state.get('wildlife', {})
    print('\nNOW: herd', sum(x['alive'] for x in w.get('deer', [])), 'alive; hunts', w.get('hunts', 0), '; carcasses', len(w.get('carcasses', [])))
    for k, t in sorted(w.get('trust', {}).items(), key=lambda kv: -kv[1]):
        print(f'  {k:8} trust {t:.2f}')
