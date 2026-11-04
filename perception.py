"""What he can make out around him (v0.35.0, mapping phase 2): seeing, hearing and noticing like a person.

From where he stands and which way he faces: about 120 degrees of clear view ahead, what is right beside him felt
and glimpsed all round, and sounds from any side. Walls and solid things block the line of sight; darkness, rain
and mist shorten it; a lit window or a fire shows from far off at night. Near things come with a detail, things
across the way with their kind, far things only as a gist.

Of everything in view he notices a few, as anyone would: what is big or close, what moves, what bears on how his
body is (cold draws the eye to light and warmth, thirst to water, hunger to food), and what bears on what he means
to do. The rest is still there to be noticed if he looks. Each thing carries a hidden handle so he can pick it by
his own phrase ("the tall oak ahead of me and to my left"); he never sees an id, a coordinate or a number.

Deterministic for a given moment (the time-lapse twin repeats it) and read-only: it never changes his life.
"""
import hashlib
import math

import layout
import spatial_words as sw

VIEW = 60          # half of the clear field of view, degrees
GLIMPSE = 3.0      # metres: what is right beside him is noticed whichever way he faces
NOTICE = {'local': 4, 'wide': 8}
BUDGET = {'local': 600, 'wide': 1500}
LIT_AT_NIGHT = {'library': 'light in the window of the reading cabin', 'internet_cafe': 'the lit windows of the café'}
WARM = {'library', 'internet_cafe', 'trading_post'}
FOOD = {'food_store', 'berry_patch', 'trading_post'}
WATER = {'spring', 'spring_pool'}
SKIP_OBJECTS = {'cabin_bed'}
SKIP_ITEMS = {'floor', 'roof', 'wall'}


def _roll(*parts):
    return int(hashlib.sha1('|'.join(map(str, parts)).encode()).hexdigest()[:6], 16) / 0xFFFFFF


def observer(state):
    """(x, z, heading) of his eyes: inside the building he is in, in bed if he lies there, else where he stands."""
    loc = state.get('location', 'cabin')
    place = layout.get()['places'].get(loc, {})
    if loc in ('shop', 'cafe', 'library') and 'inside' in place:
        return tuple(place['inside'])
    if loc == 'cabin' and state.get('in_bed') and state.get('action') in ('rest', 'sleep') and 'inside' in place:
        return tuple(place['inside'])
    pos = state.get('position')
    if isinstance(pos, dict) and 'x' in pos:
        return pos['x'], pos['z'], pos.get('heading', 0.)
    x, z = layout.stand(loc)
    return x, z, layout.facing(loc)


# ---- What there is to see ----

def _blockers(state):
    """Footprints (x0, z0, x1, z1, owner) of everything solid and tall enough to hide what is behind it."""
    out = []
    for it in layout.get()['items']:
        if it['blocks'] == 'solid' and it['kind'] != 'water':
            x, z, w, d = layout.footprint(it)
            out.append((x - w / 2, z - d / 2, x + w / 2, z + d / 2, it['id']))
    for o in state.get('built_world', {}).get('objects', {}).values():
        for p in o.get('parts', []):
            if p.get('height', 0) >= 1.2 and p.get('y', 0) - p.get('height', 0) / 2 < 1.5 and 'roof' not in p.get('id', ''):
                x, z = o['x'] + p['x'], o['z'] + p['z']
                out.append((x - p['width'] / 2, z - p['depth'] / 2, x + p['width'] / 2, z + p['depth'] / 2, o['id']))
    return out


def _clear(blockers, x, z, tx, tz, own):
    """Is the line from his eyes to the thing free of anything solid (other than the thing itself)? An exact
    segment-and-box test, so even a thin wall hides what is behind it."""
    d = math.hypot(tx - x, tz - z)
    if d < 1.2:
        return True
    ux, uz = (tx - x) / d, (tz - z) / d
    ax, az = x + ux * .5, z + uz * .5            # from just in front of his eyes...
    bx, bz = tx - ux * .6, tz - uz * .6          # ...to just short of the thing itself
    lo_x, hi_x, lo_z, hi_z = min(ax, bx), max(ax, bx), min(az, bz), max(az, bz)
    for x0, z0, x1, z1, owner in blockers:
        if owner == own or x1 < lo_x or x0 > hi_x or z1 < lo_z or z0 > hi_z:
            continue
        t0, t1, ok = 0., 1., True
        for p, q in ((-(bx - ax), ax - x0), (bx - ax, x1 - ax), (-(bz - az), az - z0), (bz - az, z1 - az)):
            if abs(p) < 1e-12:
                if q < 0:
                    ok = False
                    break
                continue
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                ok = False
                break
        if ok:
            return False
    return True


def _things(state, doy):
    """Everything there is to see, as (handle, kind, x, z, size, near words, far words, tags)."""
    import ecology
    out = []
    world = state.get('built_world', {})
    for o in world.get('objects', {}).values():
        if not o.get('parts') or o['id'] in SKIP_OBJECTS:
            continue
        size = max((p.get('y', 0) + p.get('height', 0) / 2 for p in o['parts']), default=.5)
        name = o['name'].lower()
        detail = (o.get('details') or [''])[0].rstrip('.')
        near = f'the {name}' + (f' ({detail[0].lower() + detail[1:]})' if detail and len(detail) < 90 else '')
        out.append((o['id'], o.get('kind', 'object'), o['x'], o['z'], size, near, f'the {name}', set()))
    for it in layout.get()['items']:
        if it['kind'] in SKIP_ITEMS:
            continue
        out.append((it['id'], it['kind'], it['x'], it['z'], it.get('h', 1), it['look'], it['look'].split(',')[0], set()))
    species = state.get('ecology', {}).get('tree_species', {})
    for t in world.get('trees', {}).values():
        sp = species.get(t['id'], 'tree')
        if t['stage'] == 'standing':
            near = f'a {sw.height(t["height"])} {sp} with ' + ecology.leaf_state(sp, doy)
            far = f'a {sw.height(t["height"])} {sp}'
        elif t['stage'] == 'young':
            near = far = f'a young {sp} I planted'
        else:
            near = far = f'the stump of a felled {sp}' + (' and its timber' if t.get('stock') else '')
        out.append((t['id'], 'tree', t['x'], t['z'], t.get('height', 1), near, far, set()))
    for p in state.get('ecology', {}).get('plants', []):
        if p.get('host'):
            continue   # ivy, fungi and the like grow on a tree and are seen when he looks closely
        out.append((p['id'], 'plant', p['x'], p['z'], .8, f'a patch of {p["species"]}', f'low {ecology.PLANT_KIND.get(p["species"], "plants").split()[0]}s', set()))
    try:
        import resources
        for n in world.get('resources', {}).values():
            if n['stock'] > 0:
                look = resources.look(state, n).split('. ')[0].rstrip('.')
                out.append((n['id'], 'ground', n['x'], n['z'], .3, look[0].lower() + look[1:], look[0].lower() + look[1:], set()))
    except Exception:
        pass
    try:
        import handwork
        for h in handwork.view(state):
            words = 'my fire, burning' if h['lit'] and not h.get('covered') else 'my covered fire, smoking through the earth' if h['lit'] \
                else 'my heap' if h['kg'] else 'grey ash where my fire was'
            out.append((h['id'], 'fire' if h['lit'] else 'heap', h['x'], h['z'], .6, words, words, {'lit'} if h['lit'] else set()))
    except Exception:
        pass
    return out


def _animals(state, daylight):
    import ecology, birds, wildlife
    out = []
    try:
        for b in birds.where(state, ecology, daylight):
            if b['mode'] in ('roost', 'air'):
                continue
            look = next((x['look'] for x in birds.BIRDS if x['id'] == b['id']), 'a small bird')
            label = b.get('label') or ''
            label = '' if any(c.isdigit() for c in label) else label   # a perch the world names by its position is just where it is
            out.append((b['id'], 'bird', b['x'], b['z'], .2, f'a {look}' + (f', {label}' if label else ''), 'a bird', {'moving'}))
    except Exception:
        pass
    try:
        for d in wildlife.where(state, ecology, daylight):
            out.append((d['id'], 'animal', d['x'], d['z'], 1.2, f'a {d["look"]}, {d["doing"]}', 'a large animal', {'moving'}))
    except Exception:
        pass
    return out


# ---- Noticing ----

def _needs(state):
    b = state.get('body', {})
    return {'cold': b.get('chill', 0) > .15, 'thirst': b.get('hydration', 100) < 65,
            'hunger': b.get('reserve', 100) < 65 and b.get('stomach', 20) < 8, 'sleepy': b.get('sleep_debt', 0) > 4}


def _range(state):
    import senses
    day = state.get('daylight', 1)
    w = senses.weather(state)
    r = 45. if day >= .35 else 20. if day >= .12 else (8. if state.get('possessions', {}).get('lantern') else 3.5)
    if w.get('rain') in ('rain', 'heavy rain'):
        r *= .7
    if w.get('mist'):
        r = min(r, 15.)
    return r


def view(state, aperture=None, wide=False, want='', at=None, keep_far=False):
    """What he can make out now: a list of {'handle', 'phrase', 'kind', 'score'}, most noticeable first.
    aperture: degrees each side of straight ahead he is taking in (None: the ordinary view; 180: looking all round)."""
    import datetime as _dt
    try:
        doy = _dt.datetime.fromisoformat(state['clock']['iso']).timetuple().tm_yday
    except (KeyError, ValueError, TypeError):
        doy = 355
    x, z, heading = at or observer(state)
    half = VIEW if aperture is None else aperture
    reach = _range(state)
    dark = state.get('daylight', 1) < .12
    needs = _needs(state)
    want_words = {w for w in str(want or state.get('current_intention', '')).lower().replace(',', ' ').split() if len(w) > 3}
    blockers = _blockers(state)
    inside = {o['id'] for o in state.get('built_world', {}).get('objects', {}).values() if o.get('kind') in ('building', 'structure')
              and any(p.get('id') == 'floor' and abs(x - o['x'] - p['x']) < p['width'] / 2 and abs(z - o['z'] - p['z']) < p['depth'] / 2
                      for p in o.get('parts', []))}
    seen, far_trees = [], []
    for handle, kind, tx, tz, size, near, far, tags in _things(state, doy) + _animals(state, state.get('daylight', 1)):
        if handle in inside:
            continue   # the room he is in is around him, not a thing in view
        d = math.hypot(tx - x, tz - z)
        rel = sw.relative(heading, x, z, tx, tz)
        lit = 'lit' in tags or (dark and handle in LIT_AT_NIGHT)
        if d > (60 if lit else reach) or (abs(rel) > half and d > GLIMPSE):
            continue
        if d > 15 and size < 1.5 and not lit:
            continue   # small things far off are not made out
        if not _clear(blockers, x, z, tx, tz, handle):
            continue
        if kind == 'tree' and d > 15 and not keep_far and not (want_words and want_words & set(far.split())):
            far_trees.append(handle)
            continue   # the trees of the wood further off are seen as the wood, not one by one
        if dark and handle in LIT_AT_NIGHT:
            words = LIT_AT_NIGHT[handle]
        else:
            words = near if d < 6 else far
        score = (math.sqrt(max(size, .1)) + 1) / (1 + d / 3)
        if 'moving' in tags:
            score += .6
        if lit:
            score += 1.5
        if needs['cold'] and (lit or handle in WARM or kind == 'fire'):
            score += 2.5
        if needs['thirst'] and handle in WATER:
            score += 2.5
        if needs['hunger'] and handle in FOOD:
            score += 2.5
        if want_words and want_words & set(words.lower().split()):
            score += 2
        score += _roll(state.get('clock', {}).get('iso', '')[:15], handle) * .4
        seen.append({'handle': handle, 'kind': kind, 'words': words, 'where': sw.where(heading, x, z, tx, tz), 'd': d, 'score': score})
    seen.sort(key=lambda s: -s['score'])
    taken, out = {}, []
    for s in seen:
        phrase = f"{s['words']}, {s['where']}"
        if phrase in taken:
            phrase += ' (another)' if phrase + ' (another)' not in taken else ' (yet another)'
        taken[phrase] = s['handle']
        out.append({'handle': s['handle'], 'phrase': phrase, 'kind': s['kind'], 'score': round(s['score'], 2), 'd': s['d']})
    view.far_trees = len(far_trees)
    return out


def lines(state, wide=False):
    """The few things he notices, each on a line, within his budget; then one line of gist. Read-only."""
    noticed = view(state, wide=wide)
    n, budget = NOTICE['wide' if wide else 'local'], BUDGET['wide' if wide else 'local']
    out, used = [], 0
    for s in noticed:
        if len(out) >= n:
            break
        line = s['phrase'][0].upper() + s['phrase'][1:] + '.'
        if used + len(line) > budget:
            break
        out.append(line)
        used += len(line)
    trees_far = getattr(view, 'far_trees', 0)
    if state.get('daylight', 1) < .12:
        gist = 'Beyond that it is too dark to make anything out.'
    elif trees_far > 4:
        gist = 'Further off, the trees of the wood stand all round.'
    else:
        gist = ''
    if gist and used + len(gist) <= budget + 80:
        out.append(gist)
    return out


def handles(state, kinds=None, aperture=180, at=None, limit=24, test=None):
    """{his phrase: handle} for what he can make out looking all round, nearest first (for picking a thing by his
    own words instead of by an id). at: (x, z, heading) to look from somewhere else he is about to go."""
    seen = [s for s in view(state, aperture=aperture, at=at, keep_far=True) if (kinds is None or s['kind'] in kinds) and (test is None or test(s['handle']))]
    seen.sort(key=lambda s: s['d'])
    return {s['phrase']: s['handle'] for s in seen[:limit]}
