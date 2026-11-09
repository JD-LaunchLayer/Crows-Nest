"""Animals beyond the birds' look (v0.26): a small herd of roe deer, birds that can come to trust him,
and what follows from hunting: a carcass, butchering, meat that spoils unless it is smoked.

Authored world life with rules, like the garden. Nothing tells Crow any of this exists or what to
do with it. He can notice the deer only by how they look and where they are, never by name. The
character sheets (species, diet, wariness, yields) are for Jordan and for the world's rules.

- Deer keep to the deeper woods, lying up by day and bedded at night, and come out to the edges
  and the grove around dawn and dusk. A hunt that goes near them spooks the herd for a few days.
- Fawns are born in early June to the does, while the herd is below what the woods hold.
- A hunt needs a bow and arrows he owns. Getting within bow range depends on the hour, his
  tiredness and whether the herd is already wary; the shot uses his archery practice. A shot
  can miss (the arrow may be lost), wound (he may or may not find the animal) or kill cleanly.
- A carcass must be cut up with his knife within about three cool days (one in summer) or it
  is lost. Cutting up gives fresh meat and a hide; fresh meat keeps a few days (foods.py),
  smoked meat for months. Smoking takes wood.
- Birds: each has a wariness. Being quietly about where they are builds a little trust; putting
  out food a bird eats builds more; hunting nearby sets it back; long absence lets it fade.
"""
import hashlib
import math
import random
from datetime import datetime

import foods

DEER_SHEET = {'species': 'Roe deer', 'diet': ['greens', 'fruit', 'browse'], 'wariness': .9,
              'carcass_kg': 18, 'meat_servings': 30, 'carcass_keeps_days': 3, 'herd_capacity': 8}
# What each food is to an animal's diet.
FOOD_DIET = {'provisions': {'scraps', 'seeds', 'fruit'}, 'berries': {'fruit'}, 'mixed vegetables': {'greens'},
             'salad leaves': {'greens'}, 'radishes': {'greens'}, 'potatoes': {'scraps'}, 'broad beans': {'seeds', 'greens'},
             'garlic': set(), 'onions': set(), 'venison': {'meat', 'scraps'}, 'smoked venison': {'meat', 'scraps'}}
SEGMENT_MIN = 30


def _h(*parts):
    return int(hashlib.sha1(':'.join(map(str, parts)).encode()).hexdigest()[:12], 16)


def _minutes(state):
    try:
        return datetime.fromisoformat(state['clock']['iso']).timestamp() / 60
    except (KeyError, ValueError, TypeError):
        return 0.


def _clock(state):
    try:
        return datetime.fromisoformat(state['clock']['iso'])
    except (KeyError, ValueError, TypeError):
        return datetime(2026, 11, 12, 12)


def _read(state):
    """The wildlife record for reading only: never written into his save by looking."""
    return state['wildlife'] if 'deer' in state.get('wildlife', {}) else ensure({'clock': state.get('clock', {})})


def ensure(state):
    w = state.setdefault('wildlife', {})
    w.setdefault('trust', {})
    w.setdefault('carcasses', [])
    w.setdefault('next_deer', 6)
    w.setdefault('hunts', 0)
    w.setdefault('butchered', 0)
    w.setdefault('spooked_until', 0.)
    if 'deer' not in w:
        w['deer'] = [{'id': 'deer-1', 'role': 'buck', 'alive': True}, {'id': 'deer-2', 'role': 'doe', 'alive': True},
                     {'id': 'deer-3', 'role': 'doe', 'alive': True}, {'id': 'deer-4', 'role': 'doe', 'alive': True},
                     {'id': 'deer-5', 'role': 'young', 'alive': True, 'born': _clock(state).year - 1}]
    return w


def _look(d, doy, year):
    winter = doy >= 280 or doy < 120
    coat = 'greyish-brown' if winter else 'reddish-brown'
    if d['role'] == 'young' and d.get('born') == year and doy < 240:
        return f'small {"reddish-brown" if doy < 240 else coat} animal on long thin legs, with rows of white spots along its back'
    if d['role'] == 'young' and d.get('born', 0) >= year - 1:
        return f'young slender {coat} animal on long thin legs, smaller than the others, with large ears and a pale patch on its rump'
    base = f'slender {coat} animal on long thin legs, with large ears, a black nose and a pale patch on its rump'
    if d['role'] == 'buck':
        if 120 <= doy < 290:
            return base + ', and short upright antlers with three points each'
        if 290 <= doy < 330:
            return base + ', and two small knobs on its head'
        return base + ', and short new antlers covered in soft fuzzy skin'
    return base


def herd_area(state, ecology, daylight, minutes=None):
    w = _read(state)
    m = _minutes(state) if minutes is None else minutes
    seg = int(m // SEGMENT_MIN)
    hour = _clock(state).hour
    if daylight < .12:
        return 'deeper_woods', 'bedded down'
    if m / 1440 < w['spooked_until']:
        return 'deeper_woods', 'standing alert'
    if daylight < .6 or hour < 9 or hour >= 15:             # dawn and dusk: out to the edges to feed
        area, doing = ['woodland_edge', 'grove', 'woodland_edge', 'deeper_woods'][_h('herd', seg) % 4], 'browsing'
    else:
        area, doing = (('deeper_woods', 'lying down') if _h('herd', seg, 'day') % 5 else ('grove', 'browsing'))
    return _wander(state, area, doing)


def _wander(state, area, doing):
    """Some days the herd is not on its usual round. Night bedding and a spook stay as they are."""
    import senses
    if senses.world_seed(state) is None or doing == 'bedded down':
        return area, doing
    places = ['woodland_edge', 'grove', 'deeper_woods']
    if area not in places:
        return area, doing
    roll = _h('wander', senses.world_seed(state), _clock(state).timetuple().tm_yday) % 4
    if roll == 0:
        return area, doing
    return places[(places.index(area) + roll) % 3], doing


def where(state, ecology, daylight, minutes=None):
    """Where each living deer is at a moment on Crow's clock."""
    w = _read(state)
    m = _minutes(state) if minutes is None else minutes
    seg = int(m // SEGMENT_MIN)
    area, doing = herd_area(state, ecology, daylight, m)
    a = ecology.AREAS[area]
    ang = (_h('herd', seg, 'ang') % 628) / 100
    r = a.get('r', 0) * .5 if 'r' in a else a['r_min'] + (a['r_max'] - a['r_min']) * ((_h('herd', seg, 'r') % 100) / 100)
    cx, cz = a['x'] + math.cos(ang) * r, a['z'] + math.sin(ang) * r
    doy, year = _clock(state).timetuple().tm_yday, _clock(state).year
    out = []
    for i, d in enumerate(x for x in w['deer'] if x['alive']):
        ox = ((_h(d['id'], seg, 'x') % 100) / 100 - .5) * 8
        oz = ((_h(d['id'], seg, 'z') % 100) / 100 - .5) * 8
        act = doing if doing != 'browsing' else ['browsing', 'grazing', 'browsing', 'standing with its head up'][_h(d['id'], seg) % 4]
        out.append({'id': d['id'], 'role': d['role'], 'area': area, 'x': round(cx + ox, 2), 'z': round(cz + oz, 2),
                    'doing': act, 'look': _look(d, doy, year), 'heading': round((_h(d['id'], seg, 'h') % 628) / 100, 2),
                    'small': d['role'] == 'young' and d.get('born') == year})
    return out


def facts(state, ecology, area, daylight):
    if daylight < .08:
        return []
    out = []
    for d in where(state, ecology, daylight):
        if ecology.in_area(area, d['x'], d['z']) and d['doing'] != 'bedded down':
            out.append((d['id'], f"A {d['look']} is {d['doing']} near ({d['x']:.0f}, {d['z']:.0f})."))
    return out


def view(state, ecology, daylight):
    return [{k: d[k] for k in ('id', 'role', 'x', 'z', 'doing', 'heading', 'small')} for d in where(state, ecology, daylight)]


# ---- Time passing ----
def advance(state):
    """Births in early June, carcasses going off, trust fading slowly. Returns plain notes of what was lost."""
    w = ensure(state)
    now = _clock(state)
    day = _minutes(state) / 1440
    doy = now.timetuple().tm_yday
    if 152 <= doy <= 170 and w.get('births_year') != now.year:
        w['births_year'] = now.year
        alive = [d for d in w['deer'] if d['alive']]
        for d in [d for d in alive if d['role'] == 'doe']:
            if len([x for x in w['deer'] if x['alive']]) >= DEER_SHEET['herd_capacity']:
                break
            if _h(d['id'], now.year) % 10 < 7:
                w['deer'].append({'id': f"deer-{w['next_deer']}", 'role': 'young', 'alive': True, 'born': now.year})
                w['next_deer'] += 1
        for d in w['deer']:                                 # last year's young are grown
            if d['alive'] and d['role'] == 'young' and d.get('born', now.year) <= now.year - 2:
                d['role'] = 'doe' if _h(d['id']) % 2 else 'buck'
    import garden
    lost = []
    for c in list(w['carcasses']):
        keeps = DEER_SHEET['carcass_keeps_days'] * (1.2 - .85 * garden.warmth(doy))
        if day - c['killed_day'] > keeps:
            w['carcasses'].remove(c)
            lost.append(c)
            w.setdefault('spoiled', []).append({'what': 'carcass', 'at': now.isoformat()})
    last = w.get('trust_day', day)
    if day - last >= 1:
        for k in w['trust']:
            w['trust'][k] = round(max(0., w['trust'][k] - .004 * (day - last)), 4)
        w['trust_day'] = day
    w.setdefault('trust_day', day)
    return lost


def carcass_view(state):
    w = _read(state)
    day = _minutes(state) / 1440
    return [f"the carcass of a {c['look'].split(',')[0]} (about {c['kg']} kg), hanging beside the cabin, "
            f"killed {max(0, round((day - c['killed_day']) * 24))} hours ago" for c in w['carcasses']]


# ---- Hunting ----
def hunt(state, ecology, area, daylight, fatigue, seed):
    w = ensure(state)
    owned = state.setdefault('possessions', {})
    if not owned.get('hunting_bow'):
        return {'success': False, 'text': 'He has no bow to hunt with.'}
    if not owned.get('arrows'):
        return {'success': False, 'text': 'He has no arrows.'}
    rng = random.Random(seed)
    w['hunts'] += 1
    place = ecology.AREAS[area]['name']
    _set_back_birds(state, area, .08)
    if daylight < .08:
        return {'success': False, 'text': f'Walked quietly through {place} with the bow, but it was too dark to make out anything to shoot at.'}
    now = _minutes(state)
    seen = None
    for k in range(4):                                     # over the two hours he is out
        here = [d for d in where(state, ecology, daylight, now + k * 30) if ecology.in_area(area, d['x'], d['z'])
                and d['doing'] != 'bedded down']
        if here:
            seen = rng.choice(here)
            break
    if not seen:
        return {'success': False, 'text': f'Walked quietly through {place} with the bow for two hours. No animal came within sight.'}
    dawn_dusk = 'browsing' in seen['doing'] or 'grazing' in seen['doing']
    spooked = now / 1440 < w['spooked_until']
    p = .4 + (.2 if dawn_dusk else 0) - .25 * min(1., fatigue) - (.3 if spooked else 0) - (.15 if daylight < .3 else 0)
    who = seen['look'].split(',')[0]
    w['spooked_until'] = max(w['spooked_until'], now / 1440 + 2)
    if rng.random() > p:
        dist = 40 + rng.randint(0, 40)
        return {'success': False, 'text': f'Crept towards a {who} that was {seen["doing"]} in {place}. At about {dist} m it '
                                          f'lifted its head, gave a short harsh bark and bounded away; the others went with it. No shot.'}
    hours = state.get('practical', {}).get('archery_hours', .5 * state.get('skills', {}).get('archery', 0))
    spread = 40 / (1 + math.sqrt(hours)) * (1 + fatigue * .6) * 1.5 * (1.6 if daylight < .3 else 1)
    dist_cm = math.hypot(rng.gauss(0, spread), rng.gauss(0, spread))
    yards = 18 + rng.randint(0, 12)
    owned['arrows'] -= 1
    if dist_cm > 25:
        kept = rng.random() < .5
        if kept:
            owned['arrows'] += 1
        return {'success': False, 'text': f'Got within about {yards} m of a {who} and shot. The arrow missed and the animal '
                                          f'bounded away. ' + ('He found the arrow afterwards.' if kept else 'The arrow was not found.')}
    deer = next(d for d in w['deer'] if d['id'] == seen['id'])
    if dist_cm > 12:
        found = rng.random() < (.55 if daylight >= .3 else .3)
        if not found:
            if rng.random() < .5:
                deer['alive'] = False
                deer['died'] = state.get('clock', {}).get('iso', '')
            return {'success': False, 'text': f'Shot a {who} at about {yards} m. The arrow struck too far back; the animal ran. '
                                              f'He followed spots of blood into the trees until they gave out. It was not found.'}
        text = (f'Shot a {who} at about {yards} m. The arrow struck too far back and it ran; he followed the blood for a long '
                f'way and found it lying dead.')
    else:
        text = f'Shot a {who} at about {yards} m. The arrow went in just behind the shoulder; it ran a short way and fell.'
    owned['arrows'] += 1
    deer['alive'] = False
    deer['died'] = state.get('clock', {}).get('iso', '')
    w['spooked_until'] = max(w['spooked_until'], now / 1440 + 3)
    _set_back_birds(state, area, .07)
    w['carcasses'].append({'id': deer['id'], 'look': seen['look'], 'kg': DEER_SHEET['carcass_kg'] - (8 if seen['small'] else 0),
                           'killed_day': now / 1440, 'small': seen['small']})
    return {'success': True, 'text': text + f' He carried it back to the cabin (about {DEER_SHEET["carcass_kg"] - (8 if seen["small"] else 0)} kg) and the arrow with it.'}


def butcher(state, knife_condition):
    w = ensure(state)
    if not w['carcasses']:
        return {'success': False, 'text': 'There is no carcass to cut up.'}
    c = w['carcasses'].pop(0)
    practice = min(1., w['butchered'] / 3)
    servings = round(DEER_SHEET['meat_servings'] * (.5 if c.get('small') else 1) * (.6 + .4 * practice) * (.7 + .3 * knife_condition))
    w['butchered'] += 1
    foods.add(state, 'venison', servings)
    owned = state.setdefault('possessions', {})
    owned['hide'] = owned.get('hide', 0) + 1
    rough = '' if practice >= 1 else ' It was slow, messy work and some meat was spoiled in the cutting.'
    return {'success': True, 'text': f'Gutted, skinned and cut up the carcass with the knife beside the cabin: about {servings} servings '
                                     f'of fresh meat went into the provisions chest, and the hide was rolled up.' + rough}


def preserve(state):
    fresh = sum(l['servings'] for l in foods.larder(state) if l['food'] == 'venison')
    if fresh <= 0:
        return {'success': False, 'text': 'There is no fresh meat to smoke.'}
    wood = state.get('materials', 0)
    n = min(fresh, wood * 6, 30)
    if n < 1:
        return {'success': False, 'text': 'There is not enough wood for a smoking fire.'}
    used = round(n / 6, 1)
    state['materials'] = round(wood - used, 2)
    foods.take(state, 'venison', n)
    foods.add(state, 'smoked venison', n)
    return {'success': True, 'text': f'Kept a low, smoky wood fire going beside the cabin and hung {n:g} servings of fresh meat over it '
                                     f'until it was dark and dry, using {used:g} kg of wood.'}


# ---- Birds and trust ----
def _set_back_birds(state, area, by):
    import birds
    w = ensure(state)
    for b in birds.BIRDS:
        if area in b['areas']:
            w['trust'][b['id']] = round(max(0., w['trust'].get(b['id'], 0.) - by), 4)


def presence(state, ecology, area, daylight):
    """Being quietly about where birds are: a little trust for the ones that are there."""
    import birds
    w = ensure(state)
    looks = {b['id']: b for b in birds.BIRDS}
    for ident, _ in birds.facts(state, ecology, area, daylight):
        b = looks[ident]
        w['trust'][ident] = round(min(1., w['trust'].get(ident, 0.) + .012 * (1 - b['wariness'])), 4)


LEVELS = [(.15, 'watched the {food} from {perch} and did not come down'),
          (.35, 'came a little closer and watched the {food} from a few metres off'),
          (.6, 'came down once he had been still a while, took some of the {food} and flew off with it'),
          (.85, 'came down to the {food} a couple of metres from him and fed'),
          (1.01, 'took {food} from his hand')]


def put_out_food(state, ecology, area, food, daylight):
    import birds
    w = ensure(state)
    have = foods.kinds(state)
    food = food if food in have else (have[0] if have else '')
    if not food:
        return {'success': False, 'text': 'He has no food to put out.'}
    foods.take(state, food, .25)
    name = foods.FOODS[food]['name']
    place = ecology.AREAS[area]['name']
    if daylight < .12:
        return {'success': True, 'text': f'Put a little {name} down in {place} in the dark and waited quietly. Nothing came to it.'}
    eats = FOOD_DIET.get(food, set())
    lines = []
    present = {i: label for i, label in ((x['id'], x['label']) for x in birds.where(state, ecology, daylight)) if label}
    for b in birds.BIRDS:
        if area not in b['areas'] and not (area == 'clearing' and w['trust'].get(b['id'], 0) >= .7):
            continue
        if b['id'] not in present and _h(b['id'], _minutes(state) // 30, 'comes') % 3:
            continue
        if not eats & set(b['diet']):
            if b['id'] in present:
                lines.append(f'A {b["look"]} was about, but paid the food no attention.')
            continue
        t = w['trust'].get(b['id'], 0.)
        fed = w.setdefault('last_fed', {})
        if _minutes(state) - fed.get(b['id'], -1e9) >= 12 * 60:   # trust builds over days, not by repetition in one sitting
            t = round(min(1., t + .08 * (1 - b['wariness'])), 4)
            fed[b['id']] = _minutes(state)
        w['trust'][b['id']] = t
        how = next(text for top, text in LEVELS if t < top)
        lines.append(f'A {b["look"]} ' + how.format(food=name, perch=present.get(b['id'], 'nearby').replace('on ', 'its perch on ', 1)) + '.')
    if not lines:
        lines.append('Nothing came to it while he waited.')
    return {'success': True, 'text': f'Put a little {name} down in {place} and waited quietly nearby. ' + ' '.join(lines[:4])}


def sheet():
    """The full character sheet, for Jordan (tools/wildlife_sheet.py)."""
    import birds
    return {'birds': [{k: b[k] for k in ('id', 'species', 'look', 'diet', 'wariness', 'areas', 'habits')} for b in birds.BIRDS],
            'deer': DEER_SHEET, 'foods': foods.FOODS, 'food_to_diet': {k: sorted(v) for k, v in FOOD_DIET.items()}}
