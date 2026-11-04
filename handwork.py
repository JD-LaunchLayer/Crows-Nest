"""Working things with his hands (v0.32.0, phase 2a of the materials and building work): pile, strike, feed, heat, dry.

Generic physical verbs on things he has to hand. Nothing here is named after what it might make, and nothing tells
him what to try: outcomes follow from the materials' hidden properties (data/materials.json), how dry they are,
what he strikes against what, his practice, and the weather, and he is told only what he sees, hears and feels.

- pile: put some of what he has into a heap where he is (outdoors or in his cabin).
- strike: hit one thing against another, optionally over a heap. Hard glassy stone against steel throws sparks; a
  spark in fine, dry plant stuff can smoulder and catch, and a heap with wood above it can become a fire. Struck
  with another stone, the glassy stone can lose thin, sharp flakes; ordinary stone only chips.
- feed: add wood to a heap or fire.
- heat: hold something in a fire for a while: it warms, and what is damp dries.
- dry: leave something by a fire, indoors, or in the open air for a while.

A fire burns its wood (about 1.5 kg an hour), warms anyone beside it, smokes indoors, and goes out when the wood is
gone; rain falling on a fire in the open can put it out. Practice makes striking and knapping surer. Mass is
conserved, except what a fire burns, which goes up as smoke and leaves a little ash.
"""
import hashlib
from datetime import datetime

VERBS = ['pile', 'strike', 'feed', 'heat', 'dry']
STEEL = {'axe': 'my axe', 'carving_knife': 'my carving knife'}
BURN_KG_PER_HOUR = 1.5
ASH_FRACTION = .01
SPOTS = {'cabin': (-10., -9.), 'workbench': (0., 9.), 'woods': (13., 8.), 'garden': (-9., -13.5), 'range': (8., -6.),
         'shop': (-3., -14.5), 'cafe': (9., -14.5), 'library': (-11., 4.)}


def ensure(state):
    h = state.setdefault('handwork', {'heaps': [], 'next_heap': 1, 'practice': {}})
    h.setdefault('practice', {})
    return h


def _now(state):
    try:
        return datetime.fromisoformat(state['clock']['iso'])
    except (KeyError, ValueError, TypeError):
        return datetime(2026, 12, 20, 12)


def _roll(state, *parts):
    """Deterministic chance in [0, 1) from the moment and what is involved (the time-lapse twin repeats it exactly)."""
    key = '|'.join([state.get('clock', {}).get('iso', '')] + [str(p) for p in parts])
    return int(hashlib.sha1(key.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _practise(state, family, hours):
    p = ensure(state)['practice']
    p[family] = round(p.get(family, 0) + hours, 3)
    return p[family]


def _skill(state, family):
    hours = ensure(state)['practice'].get(family, 0)
    return hours / (hours + 3)   # 0 at first, a half after three hours' practice, near 1 with long practice


# ---- What he has to hand, as he would think of it ----

def _lot_words(state, lot):
    import resources
    src = lot.get('source', '')
    node = state['built_world'].get('resources', {}).get(src)
    if node:
        what = 'what I took from ' + resources.kinds()[node['kind']]['label']
    elif lot.get('form') == 'flakes':
        what = 'thin sharp flakes of the glassy stone'
    elif lot['material'] == 'mixed_wood':
        what = 'my wood'
    elif lot['material'] == 'stone':
        what = 'my stone'
    else:
        what = 'what I have of ' + lot.get('form', 'it')
    return f'{what} ({lot["mass_kg"]:g} kg)'


def to_hand(state):
    """{words: ('lot', id) | ('tool', name)}: the things he holds, by how he knows them. Read-only."""
    import materials
    out = {}
    for lot in materials.view(state):
        if lot.get('id') is None or lot['mass_kg'] < .01:
            continue
        words = _lot_words(state, lot)
        out.setdefault(words, ('lot', lot['id']))
    for tool, words in STEEL.items():
        if state.get('tool_condition', {}).get(tool) is not None:
            out[words] = ('tool', tool)
    return out


def heaps_here(state):
    """{words: heap id} for heaps and fires where he is now."""
    loc = state.get('location')
    out = {}
    for hp in ensure(state)['heaps']:
        if hp['place'] == loc and (hp['layers'] or hp['lit']):
            out[('my fire' if hp['lit'] else 'my heap') + (' here' if sum(1 for x in ensure(state)['heaps'] if x['place'] == loc) == 1 else f' ({hp["id"]})')] = hp['id']
    return out


def _heap(state, hid):
    return next((h for h in ensure(state)['heaps'] if h['id'] == hid), None)


def lit_here(state):
    loc = state.get('location')
    return any(h['lit'] and h['place'] == loc for h in ensure(state)['heaps'])


def _lot(state, lid):
    return next((l for l in state.get('stock', {}).get('lots', []) if l['id'] == lid), None)


# ---- The verbs ----

def pile(state, what, kg):
    lot = _lot(state, what)
    if not lot:
        return {'success': False, 'text': 'He did not have that to hand.'}
    words = _lot_words(state, lot).split(' (')[0]
    taken = _take_lot(state, lot, max(.05, float(kg or lot['mass_kg'])))
    h = ensure(state)
    loc = state.get('location')
    heap = next((x for x in h['heaps'] if x['place'] == loc and not x['lit'] and x['layers']), None)
    if not heap:
        x, z = SPOTS.get(loc, (0., 0.))
        heap = {'id': f'heap-{h["next_heap"]}', 'place': loc, 'x': x, 'z': z, 'layers': [], 'lit': False, 'ash_kg': 0.,
                'lit_at': None, 'out_at': None}
        h['next_heap'] += 1
        h['heaps'].append(heap)
    for material, got in taken:
        heap['layers'].append({'material': material, 'form': lot.get('form', 'loose'), 'kg': got, 'moisture': lot.get('moisture') or 0.})
    where = 'on the floor of my cabin' if loc == 'cabin' else 'on the ground here'
    return {'success': True, 'text': f'Piled {sum(g for _, g in taken):g} kg of {words} {where}.', 'heap': heap['id']}


def _take_lot(state, lot, kg):
    """Take from this particular lot (not just the oldest of its kind), keeping the old totals in step."""
    import materials
    got = round(min(kg, lot['mass_kg']), 3)
    lot['mass_kg'] = round(lot['mass_kg'] - got, 3)
    key = materials.total_key(lot['material'])
    if key:
        state[key] = round(max(0., float(state.get(key, 0) or 0) - got), 2)
    state['stock']['lots'] = [l for l in state['stock']['lots'] if l['mass_kg'] > 1e-3]
    return [(lot['material'], got)]


def _hardness(state, thing):
    import materials
    kind, ident = thing
    if kind == 'tool':
        return 5.5, 'steel'
    lot = _lot(state, ident)
    return (materials.get(lot['material'])['hardness'], lot['material']) if lot else (0, None)


def _tinder(heap):
    """Fine, dry plant stuff in the heap: reed, flax and stinging-plant stems, light and dry enough to take a spark."""
    import materials
    fine = [l for l in heap['layers'] if materials.family(l['material']) == 'fibre']
    return sum(l['kg'] for l in fine), (min(l['moisture'] for l in fine) if fine else 1.)


def _fuel(heap):
    import materials
    return sum(l['kg'] for l in heap['layers'] if materials.family(l['material']) == 'wood')


def strike(state, a, b, heap_id=''):
    """Hit a against b (each ('lot', id) or ('tool', name)); over a heap if one is named."""
    import materials
    if a == b:
        return {'success': False, 'text': 'He cannot strike a thing against itself.'}
    ha, ma = _hardness(state, a)
    hb, mb = _hardness(state, b)
    if not ma or not mb:
        return {'success': False, 'text': 'He did not have that to hand.'}
    pair = {ma, mb}
    _practise(state, 'striking', .08)
    heap = _heap(state, heap_id) if heap_id else None
    rain = not state.get('location') == 'cabin' and _raining(state)
    if 'steel' in pair and (pair - {'steel'}) and materials.get(next(iter(pair - {'steel'})))['hardness'] >= 6.5:
        # Glassy stone against steel: sparks.
        if not heap:
            return {'success': True, 'text': 'Struck the stone hard against the steel: bright sparks jumped and died on the ground.'}
        tinder, damp = _tinder(heap)
        if heap['lit']:
            return {'success': True, 'text': 'Struck sparks over the fire; they vanished in the flames.'}
        if tinder < .02:
            return {'success': True, 'text': 'Struck sparks onto the heap: they landed on it, glowed for a moment and went out.'}
        if rain:
            return {'success': False, 'text': 'Struck sparks again and again into the heap, but the rain hissed on it and nothing would catch.'}
        chance = (.25 + .55 * _skill(state, 'fire')) * max(0., 1 - damp / .22)
        _practise(state, 'fire', .1)
        if _roll(state, 'spark', heap['id']) >= chance:
            return {'success': False, 'text': ('Struck sparks into the fine dry stems; one glowed red and smoked a little, then went out.'
                                               if damp < .12 else 'Struck sparks into the stems again and again; they smoked a little but would not catch. They feel damp.')}
        heap['lit'] = True
        heap['lit_at'] = state['clock']['iso']
        heap['out_at'] = None
        if _fuel(heap) < .2:
            return {'success': True, 'text': 'A spark caught in the dry stems: they smouldered, then burst into a little flame that ran through them and was gone in moments, leaving a curl of smoke.', 'heap': heap['id']}
        smoke = ' Smoke gathers under the roof and stings my eyes.' if heap['place'] == 'cabin' else ''
        return {'success': True, 'text': 'A spark caught in the dry stems: they smouldered, I blew on them, and a small flame climbed into the wood above. It crackles and gives off heat.' + smoke, 'heap': heap['id']}
    hard = lambda m: m != 'steel' and materials.get(m)['hardness'] >= 6.5
    glassy, other = (a, b) if hard(ma) else (b, a) if hard(mb) else (None, None)
    if glassy and other[0] == 'lot':
        # Stone on the glassy stone: knapping.
        lot = _lot(state, glassy[1])
        hours = _practise(state, 'knapping', .1)
        skill = _skill(state, 'knapping')
        r = _roll(state, 'knap', lot['id'], hours)
        if r < .3 + .5 * skill:
            kg = round(min(lot['mass_kg'], .03 + .05 * r), 3)
            _take_lot(state, lot, kg)
            materials.add(state, lot['material'], kg, form='flakes', quality=round(.3 + .6 * skill * r + .1, 2), source='struck from ' + str(lot['id']))
            return {'success': True, 'text': 'Struck the glassy stone with the other: a thin, dark flake sprang off. Its edge is so sharp it drew a bead of blood from my thumb.'}
        if r < .75:
            return {'success': True, 'text': 'Struck the glassy stone with the other: the blow jarred my hand and a few crumbs of white rind fell away.'}
        kg = round(min(lot['mass_kg'], .05), 3)
        _take_lot(state, lot, kg)
        materials.add(state, lot['material'], kg, form='broken pieces', quality=.1, source='shattered from ' + str(lot['id']))
        return {'success': True, 'text': 'Struck the glassy stone with the other: it cracked across into blunt, broken lumps.'}
    return {'success': True, 'text': 'Struck one against the other: a hard knock, a jar up my arm, and a little grit fell away. Nothing else happened.'}


def feed(state, heap_id, what, kg):
    lot = _lot(state, what)
    heap = _heap(state, heap_id)
    if not heap or not lot:
        return {'success': False, 'text': 'He did not have that to hand.'}
    got = _take_lot(state, lot, max(.1, float(kg or 1.5)))
    for material, g in got:
        heap['layers'].append({'material': material, 'form': lot.get('form', 'loose'), 'kg': g, 'moisture': lot.get('moisture') or 0.})
    if heap['lit']:
        return {'success': True, 'text': f'Laid {sum(g for _, g in got):g} kg more on the fire. It smoked, then the flames took hold of it.' if (lot.get('moisture') or 0) > .3
                else f'Laid {sum(g for _, g in got):g} kg more on the fire, and it burns up brighter.'}
    return {'success': True, 'text': f'Added {sum(g for _, g in got):g} kg to the heap.'}


def heat(state, heap_id, what, minutes):
    lot = _lot(state, what)
    heap = _heap(state, heap_id)
    if not heap or not lot:
        return {'success': False, 'text': 'He did not have that to hand.'}
    if not heap['lit']:
        return {'success': False, 'text': 'Held it over the heap, but there was no fire in it; nothing changed.'}
    before = lot.get('moisture') or 0.
    lot['moisture'] = round(max(0., before - .004 * minutes), 3)
    lot['temperature'] = 400 if minutes >= 20 else 150
    dried = ' and the damp steamed off it' if before - lot['moisture'] > .05 else ''
    return {'success': True, 'text': f'Held it in the fire for about {round(minutes)} minutes: it grew too hot to touch{dried}.'}


def dry(state, what, minutes):
    lot = _lot(state, what)
    if not lot:
        return {'success': False, 'text': 'He did not have that to hand.'}
    rate = .006 if lit_here(state) else .002 if state.get('location') == 'cabin' else (0 if _raining(state) else .0015)
    before = lot.get('moisture') or 0.
    lot['moisture'] = round(max(0., before - rate * minutes), 3)
    if rate == 0:
        return {'success': True, 'text': 'Left it out to dry, but the rain kept it wet.'}
    if before - lot['moisture'] < .02:
        return {'success': True, 'text': 'Left it to dry for a while; it feels much the same.'}
    return {'success': True, 'text': 'Left it to dry for a while; it feels lighter and drier than it did.'}


def _rain(state):
    import senses
    return senses.weather(state)['rain']


def _raining(state):
    return bool(_rain(state))


def advance(state, hours):
    """Fires burn their wood and go out; rain can put out a fire in the open."""
    import materials
    for heap in ensure(state)['heaps']:
        if not heap['lit']:
            continue
        burn = BURN_KG_PER_HOUR * hours
        for layer in heap['layers']:
            if burn <= 0:
                break
            if materials.family(layer['material']) in ('wood', 'fibre'):
                got = min(layer['kg'], burn)
                layer['kg'] = round(layer['kg'] - got, 3)
                heap['ash_kg'] = round(heap['ash_kg'] + got * ASH_FRACTION, 3)
                burn -= got
        heap['layers'] = [l for l in heap['layers'] if l['kg'] > 1e-3]
        rain = None if heap['place'] == 'cabin' else _rain(state)
        douse = {'drizzle': .3, 'rain': .6, 'heavy rain': .9}.get(rain, 0)   # chance an hour of it puts the fire out
        rained_out = douse and _roll(state, 'rain', heap['id'], round(_fuel(heap), 2)) < min(.95, douse * hours)
        if _fuel(heap) + _tinder(heap)[0] < .05 or rained_out:
            heap['lit'] = False
            heap['out_at'] = state.get('clock', {}).get('iso', '')


def view(state):
    """For drawing heaps and fires in the world (Jordan's view)."""
    return [{'id': h['id'], 'x': h['x'], 'z': h['z'], 'lit': h['lit'], 'kg': round(sum(l['kg'] for l in h['layers']), 2),
             'ash': h['ash_kg']} for h in ensure(state)['heaps'] if h['layers'] or h['lit'] or h['ash_kg']]


def line_here(state):
    """What he sees of a heap or fire where he is, plainly (for his scene)."""
    out = []
    for h in ensure(state)['heaps']:
        if h['place'] != state.get('location'):
            continue
        if h['lit']:
            out.append('My fire is burning here' + (', smoking under the roof' if h['place'] == 'cabin' else '') + '.')
        elif h['layers']:
            out.append('My heap is here, unlit.')
        elif h['ash_kg']:
            out.append('A patch of grey ash and charred ends lies where my fire burned.')
    return ' '.join(out)
