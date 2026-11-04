"""Materials and the item stock ledger (v0.31.1, phase 1 of the materials and building work).

The world's materials and their physics live in data/*.json, loaded and checked at start. Crow never
sees these numbers: he learns what a material is like by handling and testing it.

His stock is a ledger of lots, each its own thing: what it is, how much, how good, what condition, how
wet, how warm, and where it came from. Mass is conserved in every change. The old totals stay exactly
as they were: state['materials'] is still his wood in kg and state['stone'] his stone in kg, and any
code that changes them directly is reconciled into the ledger (added as a plain lot, or taken from the
oldest first), the same way the food larder works. Reading the ledger never changes his life.
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent / 'data'
FAMILY_TOTAL = {'wood': 'materials', 'stone': 'stone'}   # which old total each family is kept in step with
PLAIN = {'wood': 'mixed_wood', 'stone': 'stone'}         # what an unexplained difference in a total is taken to be
REQUIRED = {'id': str, 'family': str, 'density': (int, float), 'tensile': (int, float), 'compressive': (int, float),
            'bending': (int, float), 'hardness': (int, float), 'toughness': (int, float), 'flammability': (int, float),
            'conductivity': (int, float), 'water_uptake': (int, float), 'workability': (int, float),
            'decay_per_year': (int, float), 'colour': str, 'texture': str, 'sound': str}
UNIT = ('toughness', 'flammability', 'water_uptake', 'workability', 'decay_per_year')
_MATERIALS = None


def validate(data):
    """Raise ValueError on anything malformed: a missing or mistyped field, a duplicate id, a value out of range."""
    if not isinstance(data, dict) or not isinstance(data.get('materials'), list) or not data['materials']:
        raise ValueError('materials.json needs a non-empty "materials" list')
    seen = set()
    for m in data['materials']:
        if not isinstance(m, dict):
            raise ValueError('each material must be an object')
        for key, kind in REQUIRED.items():
            if key not in m or not isinstance(m[key], kind) or isinstance(m[key], bool):
                raise ValueError(f'material {m.get("id", "?")}: field {key!r} missing or the wrong type')
        if m['id'] in seen:
            raise ValueError(f'material {m["id"]!r} is listed twice')
        seen.add(m['id'])
        if m['density'] <= 0 or not 0 <= m['hardness'] <= 10:
            raise ValueError(f'material {m["id"]}: density or hardness out of range')
        for key in UNIT:
            if not 0 <= m[key] <= 1:
                raise ValueError(f'material {m["id"]}: {key} must be between 0 and 1')
        if m.get('melt') is not None and not isinstance(m['melt'], (int, float)):
            raise ValueError(f'material {m["id"]}: melt must be a number or null')
    for family, plain in PLAIN.items():
        if plain not in seen:
            raise ValueError(f'the plain {family} material {plain!r} must exist')
    return {m['id']: m for m in data['materials']}


def load(folder=None):
    global _MATERIALS
    path = Path(folder or DATA) / 'materials.json'
    found = validate(json.loads(path.read_text()))
    if folder is None:
        _MATERIALS = found
    return found


def all_materials():
    return _MATERIALS if _MATERIALS is not None else load()


def get(material):
    return all_materials()[material]


def family(material):
    return all_materials().get(material, {}).get('family')


# ---- The stock ledger ----

def _lot(state, material, kg, form='loose', quality=.5, condition=1., moisture=None, source=''):
    ledger = state['stock']
    lot = {'id': ledger['next_id'], 'material': material, 'form': form, 'mass_kg': round(float(kg), 3),
           'quality': round(quality, 2), 'condition': round(condition, 2),
           'moisture': moisture if moisture is not None else round(get(material)['water_uptake'] * .3, 2),
           'temperature': None, 'made_at': state.get('clock', {}).get('iso', ''), 'source': source}
    ledger['next_id'] += 1
    ledger['lots'].append(lot)
    return lot


def ensure(state):
    """Create the ledger once from what he already has (one plain lot of wood, one of stone), then keep it in step.
    Safe to run on every load: a second run changes nothing."""
    if 'stock' not in state:
        state['stock'] = {'lots': [], 'next_id': 1}
        for fam, key in FAMILY_TOTAL.items():
            kg = float(state.get(key, 0) or 0)
            if kg > 1e-6:
                _lot(state, PLAIN[fam], kg, source='what he already had when the ledger began')
        state['crafting_version'] = 1
    reconcile(state)
    return state['stock']


def total_key(material):
    """Which old total a material is kept in: any wood in his wood total; plain stone in his stone total.
    Flint, clay, ore and the rest have no old total; they live only in the ledger."""
    if family(material) == 'wood':
        return 'materials'
    return 'stone' if material == 'stone' else None


def _family_lots(lots, fam):
    return [l for l in lots if total_key(l['material']) == FAMILY_TOTAL[fam]]


def reconcile(state):
    """Keep each old total and the ledger in step. A total that grew without a lot gets a plain lot; one that
    shrank is taken from the oldest lots of that family first. Mass is never created or lost here."""
    lots = state['stock']['lots']
    for fam, key in FAMILY_TOTAL.items():
        total = round(float(state.get(key, 0) or 0), 3)
        have = round(sum(l['mass_kg'] for l in _family_lots(lots, fam)), 3)
        diff = round(total - have, 3)
        if diff > 1e-3:
            _lot(state, PLAIN[fam], diff, source='added to his stock without a record of what it was')
        elif diff < -1e-3:
            _take(state, fam, -diff, by_family=True, touch_total=False)
    state['stock']['lots'] = [l for l in lots if l['mass_kg'] > 1e-3]


def add(state, material, kg, **props):
    """Add a lot, keeping the old total in step. Returns the lot."""
    ensure(state)
    lot = _lot(state, material, kg, **props)
    key = total_key(material)
    if key:
        state[key] = round(float(state.get(key, 0) or 0) + kg, 2)
    return lot


def _take(state, what, kg, by_family=False, touch_total=True):
    lots = state['stock']['lots']
    match = (lambda l: total_key(l['material']) == FAMILY_TOTAL[what]) if by_family else (lambda l: l['material'] == what)
    taken, need = [], kg
    for l in sorted([l for l in lots if match(l)], key=lambda l: l['id']):
        if need <= 1e-6:
            break
        got = min(l['mass_kg'], need)
        l['mass_kg'] = round(l['mass_kg'] - got, 3)
        need = round(need - got, 3)
        taken.append((l['material'], round(got, 3)))
    state['stock']['lots'] = [l for l in lots if l['mass_kg'] > 1e-3]
    if touch_total:
        for material, got in taken:
            key = total_key(material)
            if key:
                state[key] = round(max(0., float(state.get(key, 0) or 0) - got), 2)
    return taken


def take(state, material, kg):
    """Take up to kg of one material, oldest lots first, keeping the old total in step. Returns [(material, kg)]."""
    ensure(state)
    return _take(state, material, kg)


def view(state):
    """His stock as it is, read-only: a copy of the lots, with any part of an old total not yet in the ledger shown
    as a plain lot. Never changes his life."""
    lots = [dict(l) for l in state.get('stock', {}).get('lots', [])]
    for fam, key in FAMILY_TOTAL.items():
        diff = round(float(state.get(key, 0) or 0) - sum(l['mass_kg'] for l in _family_lots(lots, fam)), 3)
        if diff > 1e-3:
            lots.append({'id': None, 'material': PLAIN[fam], 'form': 'loose', 'mass_kg': diff, 'quality': .5,
                         'condition': 1., 'moisture': None, 'temperature': None, 'made_at': '', 'source': 'not yet recorded'})
    return lots


def totals(state):
    """Kilograms of each material he holds (read-only)."""
    out = {}
    for l in view(state):
        out[l['material']] = round(out.get(l['material'], 0) + l['mass_kg'], 3)
    return out
