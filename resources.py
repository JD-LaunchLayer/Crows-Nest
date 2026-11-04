"""Raw materials in his woods (v0.31.2, phase 1 of the materials and building work).

Clay by the spring, reeds, sand where the water runs off, a patch of flax, stinging plants and flint at the
woodland edge, a wet hollow with iron in the deeper woods, and copper and tin farthest out. Placed once from
a fixed seed (data/resources.json) beside everything already there, never moved, renumbered or regenerated.

He comes across them only by looking (observe and explore show what is there, by look and season, never
by name), and can gather from what he has seen. Taking reduces the place's stock; plants grow back in
their season, clay seeps back very slowly, stone and ore do not return. What he takes becomes lots in
his stock ledger, with its own dampness and where it came from. Reading never changes anything.
"""
import hashlib
import json
import math
import random
from datetime import datetime
from pathlib import Path

DATA = Path(__file__).resolve().parent / 'data' / 'resources.json'
SEASON = {12: 'winter', 1: 'winter', 2: 'winter', 3: 'spring', 4: 'spring', 5: 'spring', 6: 'summer', 7: 'summer',
          8: 'summer', 9: 'autumn', 10: 'autumn', 11: 'autumn'}
_KINDS = None


def kinds():
    global _KINDS
    if _KINDS is None:
        _KINDS = validate(json.loads(DATA.read_text()))
    return _KINDS


def validate(data):
    import materials, ecology
    mats = materials.all_materials()
    out = {}
    for r in data.get('resources', []):
        for key in ('kind', 'material', 'count', 'area', 'stock', 'regrow', 'grows', 'by_hand', 'form', 'label', 'looks', 'taken'):
            if key not in r:
                raise ValueError(f'resource {r.get("kind", "?")}: {key!r} missing')
        if r['kind'] in out:
            raise ValueError(f'resource {r["kind"]!r} is listed twice')
        if r['material'] not in mats:
            raise ValueError(f'resource {r["kind"]}: no material {r["material"]!r}')
        if r['area'] not in ecology.AREAS:
            raise ValueError(f'resource {r["kind"]}: no area {r["area"]!r}')
        if not r['looks'] or '{kg}' not in r['taken'] or r['by_hand'] <= 0:
            raise ValueError(f'resource {r["kind"]}: looks, taken text or by_hand is wrong')
        out[r['kind']] = r
    if not out:
        raise ValueError('resources.json lists nothing')
    return out


def _rng(*parts):
    return random.Random(int(hashlib.sha256('|'.join(map(str, parts)).encode()).hexdigest()[:12], 16))


def _place(r, i, taken):
    """A spot for the i-th node of a kind: near its point, or in its distance band, clear of anything already there."""
    rng = _rng('resource-v1', r['kind'], i)
    for _ in range(200):
        if 'near' in r:
            a, d = rng.uniform(0, 2 * math.pi), rng.uniform(0, r.get('spread', 2))
            x, z = r['near'][0] + d * math.cos(a), r['near'][1] + d * math.sin(a)
        elif 'ring' in r:
            a, d = rng.uniform(0, 2 * math.pi), rng.uniform(*r['ring'])
            x, z = d * math.cos(a), d * math.sin(a)
        else:
            a, d = rng.uniform(0, 2 * math.pi), rng.uniform(18, 29)   # the woodland edge band
            x, z = d * math.cos(a), d * math.sin(a)
        if all((x - tx) ** 2 + (z - tz) ** 2 > 2.5 ** 2 for tx, tz in taken):
            return round(x, 1), round(z, 1)
    return round(x, 1), round(z, 1)


def ensure(state):
    """Place every node once. Existing trees, objects and ids are never touched; a second run changes nothing."""
    world = state['built_world']
    nodes = world.setdefault('resources', {})
    if world.get('resources_added'):
        return nodes
    taken = [(t['x'], t['z']) for t in world.get('trees', {}).values()] + \
            [(o['x'], o['z']) for o in world.get('objects', {}).values() if 'x' in o]
    for kind, r in kinds().items():
        for i in range(r['count']):
            x, z = _place(r, i, taken)
            taken.append((x, z))
            lo, hi = r['stock']
            cap = round(_rng('stock', kind, i).uniform(lo, hi), 1)
            nid = f'res-{kind}-{i + 1}'
            nodes.setdefault(nid, {'id': nid, 'kind': kind, 'material': r['material'], 'x': x, 'z': z, 'stock': cap, 'capacity': cap})
    world['resources_added'] = True
    world['revision'] = world.get('revision', 0) + 1
    return nodes


def _when(state):
    try:
        return datetime.fromisoformat(state['clock']['iso'])
    except (KeyError, ValueError, TypeError):
        return datetime(2026, 12, 19, 12)


def look(state, node):
    r = kinds()[node['kind']]
    looks = r['looks']
    text = looks.get('any') or looks.get(SEASON[_when(state).month], '')
    if node['stock'] < .05 * node['capacity']:
        text += ' Little of it is left there now.'
    return text


def facts(state, ecology, area, daylight):
    """What can be seen of them in an area: by look and season, never named. Nothing in the dark."""
    if daylight < .12:
        return []
    return [(n['id'], look(state, n)) for n in state['built_world'].get('resources', {}).values()
            if ecology.in_area(area, n['x'], n['z']) and n['stock'] > 0]


def known(state):
    """Places he has actually seen (recorded when he looked), each by his own way of naming it."""
    seen = state.get('ecology', {}).get('recorded', {})
    return {n['id']: kinds()[n['kind']]['label'] for n in state['built_world'].get('resources', {}).values() if n['id'] in seen}


def gather(state, node_id):
    """Take what his hands can in one session. Returns a world result; the material becomes lots in his stock."""
    import materials
    node = state['built_world'].get('resources', {}).get(node_id)
    if not node or node_id not in known(state):
        return {'success': False, 'text': 'He did not find that place.'}
    r = kinds()[node['kind']]
    if state.get('daylight', 1) < .12 and not state.get('possessions', {}).get('lantern'):
        return {'success': False, 'text': f'It was too dark to find {r["label"]}, and nothing was gathered.'}
    kg = round(min(node['stock'], r['by_hand']), 1)
    if kg <= 0:
        return {'success': False, 'text': f'Went to {r["label"]}, but there is none left to take there now.'}
    node['stock'] = round(node['stock'] - kg, 2)
    materials.add(state, r['material'], kg, form=r['form'], moisture=r.get('moisture'), source=node_id)
    state['built_world']['revision'] = state['built_world'].get('revision', 0) + 1
    return {'success': True, 'text': r['taken'].replace('{kg}', f'{kg:g}'), 'resource': node_id, 'kg': kg}


def advance(state, hours):
    """Plants grow back in their months; clay seeps back very slowly; stone and ore never return."""
    month = _when(state).month
    for n in state['built_world'].get('resources', {}).values():
        r = kinds()[n['kind']]
        if r['regrow'] > 0 and month in r['grows'] and n['stock'] < n['capacity']:
            n['stock'] = round(min(n['capacity'], n['stock'] + r['regrow'] * hours / 24), 3)


def view(state):
    """For drawing them in the world (Jordan's view): where each is, what kind, and how much is left."""
    return [{'id': n['id'], 'kind': n['kind'], 'x': n['x'], 'z': n['z'], 'left': round(n['stock'] / max(n['capacity'], 1e-6), 2),
             'season': SEASON[_when(state).month]} for n in state['built_world'].get('resources', {}).values()]
