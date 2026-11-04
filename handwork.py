"""Working things with his hands (v0.32.0 phase 2a; v0.33.0 phase 2b of the materials and building work).

Phase 2a: pile, strike, feed, heat, dry. Phase 2b: press, wet, cover, take, rub.

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

- press: squeeze and work something in his hands into a shape he describes, optionally working something else into it.
- wet: pour water from the spring basin on something.
- cover: heap something (earth, most usefully) over a heap or fire.
- take: take back up what lies in a heap.
- rub: rub one thing against another for a while.

Clay works only at the right dampness, cracks if dried too fast, bursts in a fire if not dry, and changes for good if
held long enough in a fire; grit worked into it cracks less. A fire smothered under enough earth smoulders instead of
burning, and the wood under it turns slowly to light black lumps that burn hotter than wood. A steel edge rubbed on
ordinary stone, better wet, grows keener; struck on the glassy stone it chips a little. A sharp flake can cut him; a
hot thing picked up, or a hand put into a fire, burns him. Cuts and burns heal by themselves (life.py).

A fire burns its wood (about 1.5 kg an hour), warms anyone beside it, smokes indoors, and goes out when the wood is
gone; rain falling on a fire in the open can put it out. Practice makes striking and knapping surer. Mass is
conserved, except what a fire burns, which goes up as smoke and leaves a little ash.
"""
import hashlib
from datetime import datetime

VERBS = ['pile', 'strike', 'feed', 'heat', 'dry', 'press', 'wet', 'cover', 'take', 'rub']
STEEL = {'axe': 'my axe', 'carving_knife': 'my carving knife'}
BURN_KG_PER_HOUR = 1.5
ASH_FRACTION = .01
CHAR_BURN_KG_PER_HOUR = .6     # the black lumps burn slower and hotter than wood
SMOULDER_KG_PER_HOUR = 1.     # wood turned under earth each hour
CHAR_YIELD = .25               # of the wood smothered, what is left as black lumps
CHARRED_ENDS = .03             # of the wood an open fire burns, what is left unburnt and black
HOT = 60                       # degrees: hotter than this burns a hand that holds it
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
    if lot.get('shape'):
        what = f'what I shaped from the grey-brown mud: "{lot["shape"]}"' + (', after the fire' if lot['material'] == 'fired_clay' else '') + \
               (', cracked' if lot.get('cracked') or lot.get('form') == 'cracked' else '')
    elif lot['material'] == 'fired_clay':
        what = 'hard broken pieces of the mud, from the fire' if lot.get('form') in ('broken shards', 'cracked') else 'the mud, hardened in the fire'
    elif lot['material'] == 'charcoal':
        what = 'black, light lumps from my covered fire' if 'covered' in src else 'charred ends from my fire'
    elif 'from heap' in src:
        what = 'what I took back from my heap: ' + lot.get('form', 'it')
    elif node:
        what = 'what I took from ' + resources.kinds()[node['kind']]['label']
    elif lot.get('form') == 'flakes':
        what = 'thin sharp flakes of the glassy stone'
    elif lot['material'] == 'mixed_wood':
        what = 'my wood'
    elif lot['material'] == 'stone':
        what = 'my stone'
    else:
        what = 'what I have of ' + lot.get('form', 'it')
    hot = ', still hot' if (lot.get('temperature') or 0) > HOT else ''
    return f'{what} ({lot["mass_kg"]:g} kg{hot})'


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
            out[('my covered fire' if hp['lit'] and hp.get('covered') else 'my fire' if hp['lit'] else 'my heap') + (' here' if sum(1 for x in ensure(state)['heaps'] if x['place'] == loc) == 1 else f' ({hp["id"]})')] = hp['id']
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
    burnt = _too_hot(state, lot)
    if burnt:
        return burnt
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
    return {'success': True, 'text': f'Piled {sum(g for _, g in taken):g} kg of {words} {where}.' + _sharp(state, lot), 'heap': heap['id']}


def _too_hot(state, lot):
    """Picking up something still hot burns the hand that does it; he lets go and nothing else happens."""
    import life
    t = lot.get('temperature') or 0
    if t <= HOT:
        return None
    life.injure(state, 'burn', 'fingers', min(.45, .08 + t / 1500))
    return {'success': False, 'text': 'Took hold of it, but it was still hot: it burned my fingers and I dropped it at once.'}


def _sharp(state, lot):
    """Handling thin sharp flakes now and then nicks a finger, less with practice."""
    import life
    if lot.get('form') != 'flakes' or _roll(state, 'nick', lot['id']) >= .3 - .2 * _skill(state, 'knapping'):
        return ''
    life.injure(state, 'cut', 'fingers', .12)
    return ' One of the flakes nicked my finger as I handled them.'


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
    for thing in (a, b):
        if thing[0] == 'lot':
            burnt = _too_hot(state, _lot(state, thing[1]))
            if burnt:
                return burnt
    pair = {ma, mb}
    _practise(state, 'striking', .08)
    if 'steel' in pair and max(ha, hb) >= 6.5:   # the glassy stone bites the steel a little each time
        tool = a[1] if a[0] == 'tool' else b[1]
        cond = state.setdefault('tool_condition', {})
        cond[tool] = round(max(.2, cond.get(tool, 1.) - .004), 4)
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
            import life
            if r < .1 * (1 - skill):
                life.injure(state, 'cut', 'thumb', .35)
                return {'success': True, 'text': 'Struck the glassy stone with the other: a thin, dark flake sprang off and sliced deep into my thumb. It bled freely for a while before it stopped.'}
            life.injure(state, 'cut', 'thumb', .06)
            return {'success': True, 'text': 'Struck the glassy stone with the other: a thin, dark flake sprang off. Its edge is so sharp it drew a bead of blood from my thumb.'}
        if r < .75:
            return {'success': True, 'text': 'Struck the glassy stone with the other: the blow jarred my hand and a few crumbs of white rind fell away.'}
        kg = round(min(lot['mass_kg'], .05), 3)
        _take_lot(state, lot, kg)
        materials.add(state, lot['material'], kg, form='broken pieces', quality=.1, source='shattered from ' + str(lot['id']))
        return {'success': True, 'text': 'Struck the glassy stone with the other: it cracked across into blunt, broken lumps.'}
    for thing, other, m in ((a, b, ma), (b, a, mb)):
        if m == 'fired_clay':
            lot = _lot(state, thing[1])
            ho = _hardness(state, other)[0]
            if ho >= 4 and _roll(state, 'ceramic', lot['id'], lot['mass_kg']) < .3:
                lot['form'] = 'broken shards'
                lot.pop('shape', None)
                return {'success': True, 'text': 'Struck it against the other: it rang once and broke into sharp-edged pieces.'}
            return {'success': True, 'text': f'Struck it against the other: {materials.get("fired_clay")["sound"]}. It held.'}
    sound = materials.get(ma)['sound'] if ma != 'steel' else materials.get(mb)['sound'] if mb != 'steel' else 'a ringing clang'
    return {'success': True, 'text': f'Struck one against the other: {sound}, a jar up my arm. Nothing else happened.'}


def feed(state, heap_id, what, kg):
    lot = _lot(state, what)
    heap = _heap(state, heap_id)
    if not heap or not lot:
        return {'success': False, 'text': 'He did not have that to hand.'}
    burnt = _too_hot(state, lot)
    if burnt:
        return burnt
    got = _take_lot(state, lot, max(.1, float(kg or 1.5)))
    for material, g in got:
        heap['layers'].append({'material': material, 'form': lot.get('form', 'loose'), 'kg': g, 'moisture': lot.get('moisture') or 0.})
    if heap['lit'] and heap.get('covered'):
        return {'success': True, 'text': f'Pushed {sum(g for _, g in got):g} kg in at the edge of the earth; the smoke thickened a little.'}
    if heap['lit']:
        import life
        sting = ''
        if _roll(state, 'singe', heap['id'], lot['id']) < .12 * (1 - _skill(state, 'fire')):
            life.injure(state, 'burn', 'hand', .15)
            sting = ' A flame licked the back of my hand as I reached in.'
        return {'success': True, 'text': (f'Laid {sum(g for _, g in got):g} kg more on the fire. It smoked, then the flames took hold of it.' if (lot.get('moisture') or 0) > .3
                else f'Laid {sum(g for _, g in got):g} kg more on the fire, and it burns up brighter.') + sting}
    return {'success': True, 'text': f'Added {sum(g for _, g in got):g} kg to the heap.' + _sharp(state, lot)}


def heat(state, heap_id, what, minutes):
    lot = _lot(state, what)
    heap = _heap(state, heap_id)
    if not heap or not lot:
        return {'success': False, 'text': 'He did not have that to hand.'}
    if not heap['lit']:
        return {'success': False, 'text': 'Held it over the heap, but there was no fire in it; nothing changed.'}
    if heap.get('covered'):
        return {'success': False, 'text': 'The fire is under the earth; there was no flame to hold it in, only warm ground and seeping smoke.'}
    if lot['material'] == 'clay':
        return _fire_clay(state, lot, heap, minutes)
    before = lot.get('moisture') or 0.
    lot['moisture'] = round(max(0., before - .004 * minutes), 3)
    lot['temperature'] = (700 if _hot_fire(heap) else 400) if minutes >= 20 else 150
    dried = ' and the damp steamed off it' if before - lot['moisture'] > .05 else ''
    return {'success': True, 'text': f'Held it in the fire for about {round(minutes)} minutes: it grew too hot to touch{dried}.'}


def dry(state, what, minutes):
    lot = _lot(state, what)
    if not lot:
        return {'success': False, 'text': 'He did not have that to hand.'}
    rate = .006 if lit_here(state) else .002 if state.get('location') == 'cabin' else (0 if _raining(state) else .0015)
    before = lot.get('moisture') or 0.
    lot['moisture'] = round(max(0., before - rate * minutes), 3)
    if lot['material'] == 'clay' and lot.get('shape') and rate >= .006 and before > .15 and not lot.get('cracked'):
        temper = sum((lot.get('temper') or {}).values()) / max(lot['mass_kg'], .01)
        if _roll(state, 'drycrack', lot['id'], minutes) < max(.05, .5 - 1.2 * min(temper, .3)):
            lot['cracked'] = True
            return {'success': True, 'text': 'Left it by the fire to dry: it lightened in colour, and fine cracks opened across it as it went.'}
    if rate == 0:
        return {'success': True, 'text': 'Left it out to dry, but the rain kept it wet.'}
    if before - lot['moisture'] < .02:
        return {'success': True, 'text': 'Left it to dry for a while; it feels much the same.'}
    return {'success': True, 'text': 'Left it to dry for a while; it feels lighter and drier than it did.'}


# ---- Phase 2b (v0.33.0): clay, earth over a fire, taking back, rubbing ----

def _char(heap):
    import materials
    return sum(l['kg'] for l in heap['layers'] if materials.family(l['material']) == 'char')


def _cover(heap):
    return sum(l['kg'] for l in heap['layers'] if l.get('cover'))


def _hot_fire(heap):
    """A fire with a good bed of the black lumps in it burns far hotter than wood alone."""
    return heap['lit'] and not heap.get('covered') and _char(heap) >= .5


def _temper(lot):
    return sum((lot.get('temper') or {}).values()) / max(lot['mass_kg'], .01)


def _fire_clay(state, lot, heap, minutes):
    """Clay in a fire: steam bursts it if it is damp; long enough in the heat changes it for good."""
    import materials
    skill = _skill(state, 'clay')
    _practise(state, 'clay', minutes / 120)
    damp = lot.get('moisture') or 0.
    lot['temperature'] = 700 if _hot_fire(heap) else 500
    if damp > .08 and _roll(state, 'burst', lot['id'], minutes) < min(.95, .45 + 4 * (damp - .08)):
        lot.update(material='fired_clay', form='broken shards', moisture=0., quality=.1)
        lot.pop('shape', None)
        lot['mass_kg'] = round(lot['mass_kg'] * (1 - damp), 3)
        return {'success': True, 'text': 'Put it in the fire. It hissed and steamed, then cracked sharply, and pieces of it burst apart in the heat. What came out is broken.'}
    lot['mass_kg'] = round(lot['mass_kg'] * (1 - damp), 3)
    lot['moisture'] = 0.
    if minutes < 40:
        return {'success': True, 'text': f'Held it in the fire for about {round(minutes)} minutes: it came out darker, dry and far too hot to touch.'}
    lot['mass_kg'] = round(lot['mass_kg'] * .96, 3)
    crack = max(.05, .45 - 1.0 * min(_temper(lot), .3) - .2 * skill + (.2 if lot.get('cracked') else 0))
    if _roll(state, 'firecrack', lot['id'], minutes) < crack:
        lot.update(material='fired_clay', form='cracked', quality=.2)
        return {'success': True, 'text': f'Held it in the fire for about {round(minutes)} minutes. It came out glowing at the edges and changed in colour, but with a crack running right across it.'}
    lot.update(material='fired_clay', form='fired', quality=round(min(1., .4 + .35 * skill + (.15 if _hot_fire(heap) else 0) + (.05 if lot.get('burnished') else 0)), 2))
    return {'success': True, 'text': f'Held it in the fire for about {round(minutes)} minutes. It came out glowing at the edges, far too hot to touch, and its colour has changed right through.'}


def press(state, what, shape, with_what=None, with_kg=0., kg=None):
    """Squeeze and work something in the hands into a shape he describes in his own words."""
    lot = _lot(state, what)
    if not lot:
        return {'success': False, 'text': 'He did not have that to hand.'}
    burnt = _too_hot(state, lot)
    if burnt:
        return burnt
    shape = ' '.join(str(shape or '').split())[:80] or 'a lump'
    if lot['material'] == 'sand':
        return {'success': True, 'text': 'Squeezed a handful: ' + ('it held its shape for a moment, then slumped and crumbled.' if (lot.get('moisture') or 0) > .1 else 'the dry grains ran out between my fingers.')}
    if lot['material'] != 'clay' or lot.get('shape') and lot['material'] != 'clay':
        return {'success': True, 'text': 'Pressed and worked it in my hands, but it would not take any shape; it stayed as it was.'}
    damp = lot.get('moisture') or 0.
    if damp < .12:
        return {'success': True, 'text': 'Tried to work it, but it was too dry: it crumbled and cracked apart in my hands and would not hold together.'}
    if damp > .5:
        return {'success': True, 'text': 'Tried to work it, but it was sloppy and wet: it stuck to my hands and slumped flat as soon as I let go.'}
    skill = _skill(state, 'clay')
    _practise(state, 'clay', .25)
    take = round(min(lot['mass_kg'], float(kg or lot['mass_kg'])), 3)
    import materials
    if take < lot['mass_kg'] - 1e-3:   # work only part of it: split it off into its own lot first
        part = materials.add(state, 'clay', take, form=lot.get('form', 'lumps'), quality=lot.get('quality', .5), moisture=damp, source=lot.get('source', ''))
        lot['mass_kg'] = round(lot['mass_kg'] - take, 3)
        lot = part
    temper, mixed = {}, ''
    other = _lot(state, with_what) if with_what else None
    if other and other['id'] != lot['id']:
        add = round(min(other['mass_kg'], float(with_kg or other['mass_kg'] * .25), lot['mass_kg']), 3)
        if add > 0:
            _take_lot(state, other, add)
            temper[other['material']] = add
            lot['mass_kg'] = round(lot['mass_kg'] + add, 3)
            lot['moisture'] = round(damp * (lot['mass_kg'] - add) / lot['mass_kg'] + (other.get('moisture') or 0) * add / lot['mass_kg'], 3)
            mixed = f' Worked {add:g} kg of the other in as I went; it feels grittier.' if materials.family(other['material']) in ('earth', 'stone') else \
                    f' Worked {add:g} kg of the other in as I went.'
    lot.update(form='pressed', shape=shape, quality=round(.3 + .5 * skill, 2))
    if temper:
        lot['temper'] = temper
    feel = ('It was a little stiff and cracked at the edges as I worked it. ' if lot['moisture'] < .18 else
            'It was soft and sticky and sagged a little as I worked it. ' if lot['moisture'] > .38 else 'It was cool and smooth and took the shape well. ')
    return {'success': True, 'text': f'Pressed and worked it into {shape}. ' + feel + 'It holds the marks of my fingers.' + mixed}


def wet(state, what, litres):
    """Pour water from the spring basin over something."""
    import materials
    lot = _lot(state, what)
    if not lot:
        if what and isinstance(what, str) and what in STEEL:
            return {'success': True, 'text': 'Poured water over the steel; it ran off and left it shining wet.'}
        return {'success': False, 'text': 'He did not have that to hand.'}
    water = state.get('provisions', {})
    litres = round(max(.05, min(2., float(litres or .3), water.get('water_litres', 0))), 2)
    if litres < .05:
        return {'success': False, 'text': 'The spring basin was empty; there was no water to pour.'}
    water['water_litres'] = round(water['water_litres'] - litres, 2)
    hot = (lot.get('temperature') or 0) > 100
    lot['temperature'] = None if hot else lot.get('temperature')
    m = materials.get(lot['material'])
    before = lot.get('moisture') or 0.
    if hot:
        lot['moisture'] = before
        return {'success': True, 'text': 'Poured water over it: it spat and hissed into steam, and it is cool enough to touch now.'}
    soak = min(litres, max(0., lot['mass_kg'] * (m['water_uptake'] - before)))
    lot['mass_kg'] = round(lot['mass_kg'] + soak, 3)
    lot['moisture'] = round(min(.8, (before * (lot['mass_kg'] - soak) + soak) / lot['mass_kg']), 3)
    if lot['material'] == 'fired_clay':
        return {'success': True, 'text': 'Poured water over it: it darkened, and the water soaked in only slowly and beaded on the surface. It stayed hard.'}
    if lot['material'] == 'clay' and lot.get('shape') and lot['moisture'] > .3:
        lot['form'] = 'lumps'
        lot.pop('shape', None)
        lot.pop('cracked', None)
        return {'success': True, 'text': 'Poured water over it: it softened and slumped back into sticky mud. The shape is gone.'}
    if lot['material'] == 'clay':
        return {'success': True, 'text': 'Poured water over it and worked it a little: it is softer and stickier now.'}
    if soak < .01:
        return {'success': True, 'text': 'Poured water over it; most of it ran straight off and it is only wet on the surface.'}
    return {'success': True, 'text': 'Poured water over it; it darkened and soaked some of it up.'}


def cover(state, heap_id, what, kg):
    """Heap something over a heap or fire. Earth enough over a burning fire smothers it to a smoulder."""
    import materials
    lot = _lot(state, what)
    heap = _heap(state, heap_id)
    if not heap or not lot:
        return {'success': False, 'text': 'He did not have that to hand.'}
    if materials.family(lot['material']) not in ('earth', 'stone', 'ore', 'ceramic'):
        return feed(state, heap_id, what, kg)
    burnt = _too_hot(state, lot)
    if burnt:
        return burnt
    got = _take_lot(state, lot, max(.1, float(kg or lot['mass_kg'])))
    for material, g in got:
        heap['layers'].append({'material': material, 'form': lot.get('form', 'loose'), 'kg': g, 'moisture': lot.get('moisture') or 0., 'cover': True})
    kg = sum(g for _, g in got)
    if not heap['lit']:
        return {'success': True, 'text': f'Heaped {kg:g} kg over the heap.'}
    fuel = _fuel(heap) + _char(heap)
    if fuel < .5:
        heap['lit'] = False
        heap['out_at'] = state['clock']['iso']
        return {'success': True, 'text': f'Heaped {kg:g} kg over the fire. It went out under it with a last puff of smoke.'}
    if _cover(heap) < max(.5, .15 * _fuel(heap)):
        return {'success': True, 'text': f'Heaped {kg:g} kg over the fire, but it was not enough to cover it; the flames burn up through it in places.'}
    heap['covered'] = True
    return {'success': True, 'text': f'Heaped {kg:g} kg over the fire until the flames were out of sight. Thin smoke seeps up through the earth, and it is warm to the hand.'}


def take(state, heap_id):
    """Take back up what lies in a heap. Reaching into a fire burns; what was just burning is still hot."""
    import life, materials
    heap = _heap(state, heap_id)
    if not heap:
        return {'success': False, 'text': 'There was no heap of his there.'}
    if heap['lit'] and not heap.get('covered'):
        life.injure(state, 'burn', 'hand', .3)
        return {'success': False, 'text': 'Reached into the burning fire and snatched my hand back at once: it is burned.'}
    if heap['lit']:   # a covered fire: the earth comes off, air reaches the wood, and it bursts into flame
        earth = [l for l in heap['layers'] if l.get('cover')]
        heap['layers'] = [l for l in heap['layers'] if not l.get('cover')]
        heap['covered'] = False
        for l in earth:
            lot = materials.add(state, l['material'], l['kg'], form=l['form'], moisture=l['moisture'], source=f'from heap {heap["id"]}')
            lot['temperature'] = 120
        life.injure(state, 'burn', 'fingers', .1)
        return {'success': True, 'text': 'Scraped the hot earth off the smouldering heap, scorching my fingers. As the air reached it, the glowing wood underneath burst into flame.'}
    if not heap['layers']:
        return {'success': False, 'text': 'There was only ash there; nothing to take up.'}
    hot = heap.get('out_at') and _hours_since(state, heap['out_at']) < 1
    groups = {}
    for l in heap['layers']:
        key = (l['material'], l['form'], bool(l.get('cover')))
        g = groups.setdefault(key, [0., 0.])
        g[0] += l['kg']
        g[1] = max(g[1], l['moisture'])
    words = []
    for (material, form, covered), (kg, damp) in groups.items():
        src = f'from heap {heap["id"]}' + (' (covered)' if heap.get('was_covered') and material == 'charcoal' else '')
        lot = materials.add(state, material, round(kg, 3), form=form, moisture=damp, source=src)
        if hot:
            lot['temperature'] = 150
        words.append(f'{kg:g} kg')
    heap['layers'] = []
    text = 'Took up everything from the heap (' + ', '.join(words) + ').'
    if hot:
        life.injure(state, 'burn', 'fingers', .15)
        text += ' It was still hot from the fire and scorched my fingers.'
    return {'success': True, 'text': text}


def _hours_since(state, iso):
    try:
        return (_now(state) - datetime.fromisoformat(iso)).total_seconds() / 3600
    except (ValueError, TypeError):
        return 99


def rub(state, a, b, minutes):
    """Rub one thing against another for a while: steel on ordinary stone, better wet, grows keener."""
    import materials
    ha, ma = _hardness(state, a)
    hb, mb = _hardness(state, b)
    if not ma or not mb or a == b:
        return {'success': False, 'text': 'He did not have that to hand.'}
    for thing in (a, b):
        if thing[0] == 'lot':
            burnt = _too_hot(state, _lot(state, thing[1]))
            if burnt:
                return burnt
    minutes = max(5., min(240., float(minutes or 20)))
    if 'steel' in (ma, mb) and ma != mb:
        tool = a[1] if a[0] == 'tool' else b[1]
        stone = _lot(state, (b if a[0] == 'tool' else a)[1])
        cond = state.setdefault('tool_condition', {})
        name = STEEL[tool].replace('my ', '')
        family = materials.family(stone['material'])
        h = materials.get(stone['material'])['hardness']
        if stone['material'] == 'fired_clay' or (family == 'stone' and 4 <= h < 6.5) or stone['material'] == 'sand':
            _practise(state, 'sharpening', minutes / 60)
            wet = (stone.get('moisture') or 0) > .05
            rate = (.004 if wet else .002) * (.6 if stone['material'] == 'sand' else 1) * (.7 + .3 * _skill(state, 'sharpening'))
            top = .85 + .1 * _skill(state, 'sharpening')
            before = cond.get(tool, 1.)
            cond[tool] = round(max(before, min(top, before + rate * minutes)), 4)
            import life
            how = 'the wet stone' if wet else 'the stone'
            if cond[tool] - before < .01:
                return {'success': True, 'text': f'Rubbed the {name} edge along {how} for a while; it looks much as it did. ' + life.tool_feel(state, tool)}
            return {'success': True, 'text': f'Rubbed the {name} edge along {how} for a while; grey paste gathered on it, and the edge brightened. ' + life.tool_feel(state, tool)}
        if h >= 6.5:
            cond[tool] = round(max(.2, cond.get(tool, 1.) - .01), 4)
            return {'success': True, 'text': f'Rubbed the {name} edge on the glassy stone: it skated and scraped, and left fine scratches along the steel.'}
        return {'success': True, 'text': f'Rubbed the {name} against it for a while; nothing changed but a smear on the steel.'}
    la, lb = (_lot(state, t[1]) if t[0] == 'lot' else None for t in (a, b))
    fa, fb = materials.family(ma), materials.family(mb)
    if fa == fb == 'wood':
        _practise(state, 'friction', minutes / 60)
        return {'success': True, 'text': 'Rubbed the two pieces of wood hard together: my palms grew hot, the wood darkened and smelled scorched, and a little brown dust gathered. No ember came.'}
    for lot, other in ((la, lb), (lb, la)):
        if lot and other and lot['material'] == 'clay' and lot.get('shape') and materials.get(other['material'])['hardness'] >= 4 \
                and .1 < (lot.get('moisture') or 0) < .25:
            lot['burnished'] = True
            return {'success': True, 'text': 'Rubbed the half-dry shape with the stone: its surface grew close and smooth, with a faint shine.'}
        if lot and lot['material'] == 'clay':
            return {'success': True, 'text': 'Rubbed them together: the soft mud smeared and left a brown film.'}
    if fa == fb == 'stone' or {fa, fb} <= {'stone', 'ore', 'ceramic'}:
        return {'success': True, 'text': 'Rubbed one against the other: a gritty scraping, and a little pale dust; the rubbed faces are a touch smoother.'}
    return {'success': True, 'text': 'Rubbed one against the other for a while; nothing much changed.'}


def _rain(state):
    import senses
    return senses.weather(state)['rain']


def _raining(state):
    return bool(_rain(state))


def advance(state, hours):
    """Fires burn their wood and go out; rain can put out a fire in the open."""
    import materials
    _cool(state, hours)
    for heap in ensure(state)['heaps']:
        if not heap['lit']:
            continue
        if heap.get('covered'):
            # Smothered: the wood chars slowly under the earth instead of burning away; rain cannot reach it.
            turn = SMOULDER_KG_PER_HOUR * hours
            made = 0.
            for layer in heap['layers']:
                if turn <= 0:
                    break
                if materials.family(layer['material']) in ('wood', 'fibre'):
                    got = min(layer['kg'], turn)
                    layer['kg'] = round(layer['kg'] - got, 3)
                    made += got * (CHAR_YIELD if materials.family(layer['material']) == 'wood' else 0)
                    turn -= got
            if made:
                heap['layers'].append({'material': 'charcoal', 'form': 'black lumps', 'kg': round(made, 3), 'moisture': 0.})
            heap['layers'] = [l for l in heap['layers'] if l['kg'] > 1e-3]
            heap['was_covered'] = True
            if _fuel(heap) + _tinder(heap)[0] < .05:
                heap['lit'] = False
                heap['covered'] = False
                heap['out_at'] = state.get('clock', {}).get('iso', '')
            continue
        burn = BURN_KG_PER_HOUR * hours
        for layer in heap['layers']:
            if burn <= 0:
                break
            if materials.family(layer['material']) in ('wood', 'fibre'):
                got = min(layer['kg'], burn)
                layer['kg'] = round(layer['kg'] - got, 3)
                heap['ash_kg'] = round(heap['ash_kg'] + got * ASH_FRACTION, 3)
                heap['burnt_kg'] = round(heap.get('burnt_kg', 0) + got * (materials.family(layer['material']) == 'wood'), 3)
                burn -= got
        char = CHAR_BURN_KG_PER_HOUR * hours * (1 if burn > 0 else .3)   # the lumps glow away under and after the wood
        for layer in heap['layers']:
            if char <= 0:
                break
            if materials.family(layer['material']) == 'char':
                got = min(layer['kg'], char)
                layer['kg'] = round(layer['kg'] - got, 3)
                heap['ash_kg'] = round(heap['ash_kg'] + got * .03, 3)
                char -= got
        heap['layers'] = [l for l in heap['layers'] if l['kg'] > 1e-3]
        rain = None if heap['place'] == 'cabin' else _rain(state)
        douse = {'drizzle': .3, 'rain': .6, 'heavy rain': .9}.get(rain, 0)   # chance an hour of it puts the fire out
        rained_out = douse and _roll(state, 'rain', heap['id'], round(_fuel(heap), 2)) < min(.95, douse * hours)
        if _fuel(heap) + _tinder(heap)[0] + _char(heap) < .05 or rained_out:
            heap['lit'] = False
            heap['out_at'] = state.get('clock', {}).get('iso', '')
            ends = round(heap.get('burnt_kg', 0) * CHARRED_ENDS, 3)   # an open fire leaves a few black, unburnt ends
            if ends >= .02:
                heap['layers'].append({'material': 'charcoal', 'form': 'charred ends', 'kg': ends, 'moisture': 0.})
            heap['burnt_kg'] = 0.


def _cool(state, hours):
    """Hot things cool toward the air: most of the heat is gone within the hour."""
    import math
    for lot in state.get('stock', {}).get('lots', []):
        t = lot.get('temperature')
        if t:
            t = 15 + (t - 15) * math.exp(-hours / .35)
            lot['temperature'] = None if t < 35 else round(t)


def view(state):
    """For drawing heaps and fires in the world (Jordan's view)."""
    return [{'id': h['id'], 'x': h['x'], 'z': h['z'], 'lit': h['lit'], 'kg': round(sum(l['kg'] for l in h['layers']), 2),
             'ash': h['ash_kg'], 'covered': bool(h.get('covered'))} for h in ensure(state)['heaps'] if h['layers'] or h['lit'] or h['ash_kg']]


def line_here(state):
    """What he sees of a heap or fire where he is, plainly (for his scene)."""
    out = []
    for h in ensure(state)['heaps']:
        if h['place'] != state.get('location'):
            continue
        if h['lit'] and h.get('covered'):
            out.append('My fire smoulders here under a mound of earth; thin smoke seeps out of it.')
        elif h['lit']:
            out.append('My fire is burning here' + (', smoking under the roof' if h['place'] == 'cabin' else '') + '.')
        elif h['layers'] and all(l['form'] == 'charred ends' for l in h['layers']):
            out.append('A patch of grey ash lies where my fire burned, with a few black, charred ends of wood in it.')
        elif h['layers']:
            out.append('My heap is here, unlit.')
        elif h['ash_kg']:
            out.append('A patch of grey ash and charred ends lies where my fire burned.')
    return ' '.join(out)
