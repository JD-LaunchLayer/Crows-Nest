"""What he can sense outdoors (v0.30.17): weather, warmth or cold, the sky, and the sounds of the wood.

Plain perceptions only, never feelings: whether he likes a clear frosty night or a warm afternoon
is his to find out. Day and night are given equally much to notice. Everything is worked out from
his own date and hour (south-east England), so it is the same each time it is read and nothing is
saved: reading it never changes his life.

- Weather comes day by day: some days dry, some wet (more often in late autumn and winter), and
  rain on a wet day falls for some hours, not all of them. Mist gathers on still, cold mornings.
- Warmth follows the season and the hour, and clear skies make warm days warmer and nights colder.
  Frost forms on clear nights near freezing. He feels it as warm, mild, chilly, cold, not as numbers.
- The sky: the sun by day; by night the moon (its phase from the real calendar, up for part of the
  night) and the stars when the sky is clear.
- Sounds by time and season, described as heard, with no names he has not learned.
"""
import hashlib
import math
import random
from datetime import datetime


def _rng(*parts):
    seed = int(hashlib.sha256('|'.join(str(p) for p in parts).encode()).hexdigest()[:12], 16)
    return random.Random(seed)


def _when(state):
    try:
        dt = datetime.fromisoformat(state['clock']['iso'])
    except (KeyError, ValueError, TypeError):
        dt = datetime(2026, 12, 18, 12)
    return dt, dt.timetuple().tm_yday, dt.hour + dt.minute / 60


def weather(state):
    """The weather now: sky, rain, wind, mist, frost and temperature (degrees, kept to himself)."""
    dt, doy, hour = _when(state)
    day = _rng('day', dt.date().isoformat())
    month = dt.month
    wet_chance = .5 if month in (10, 11, 12, 1) else .4 if month in (2, 3, 9) else .3
    wet = day.random() < wet_chance
    sky_day = day.choice(['clear', 'clear', 'cloudy', 'overcast']) if not wet else day.choice(['cloudy', 'overcast', 'overcast'])
    wind = day.choice(['still', 'breeze', 'breeze', 'windy']) if not wet else day.choice(['breeze', 'windy', 'windy'])
    # Rain falls for part of a wet day: one or two spells of a few hours.
    raining = None
    if wet:
        for spell in range(day.choice([1, 1, 2])):
            start, length = day.uniform(0, 24), day.uniform(2, 7)
            heavy = day.choice(['drizzle', 'rain', 'rain', 'heavy rain'])
            if (hour - start) % 24 < length:
                raining = heavy
    sky = 'overcast' if raining else sky_day
    # Temperature: season, hour, cloud and the day's own warmth or chill.
    seasonal = 11 - 6.5 * math.cos(2 * math.pi * (doy - 20) / 365)
    swing = {'clear': 5., 'cloudy': 3., 'overcast': 1.8}[sky]
    temp = seasonal + swing * math.cos(2 * math.pi * (hour - 15) / 24) + day.uniform(-3, 3) - (1 if raining else 0)
    mist = wind == 'still' and sky != 'overcast' and temp < 8 and (hour < 10 or hour > 20) and not raining
    frost = sky == 'clear' and temp < 1.5 and (hour < 10 or hour > 18) and not raining
    return {'sky': sky, 'rain': raining, 'wind': wind, 'mist': mist, 'frost': frost, 'temp': round(temp, 1)}


def _warmth(t):
    return ('bitterly cold' if t < -2 else 'freezing cold' if t < 2 else 'cold' if t < 6 else 'chilly' if t < 10
            else 'mild' if t < 15 else 'pleasantly warm' if t < 20 else 'warm' if t < 25 else 'hot')


def moon(state):
    """Phase from the real calendar (days since a known new moon), and whether it is up: it rises later
    each day, so a full moon is up all night and a new moon is up by day."""
    dt, _, hour = _when(state)
    age = ((dt.timestamp() - datetime(2000, 1, 6, 18, 14).timestamp()) / 86400) % 29.530588
    frac = age / 29.530588
    lit = (1 - math.cos(2 * math.pi * frac)) / 2
    transit = (12 + frac * 24.8) % 24
    up = min((hour - transit) % 24, (transit - hour) % 24) < 6
    shape = ('no moon to speak of' if lit < .04 else 'a thin crescent moon' if lit < .3 else 'a half moon' if lit < .65
             else 'a nearly full moon' if lit < .95 else 'a full moon')
    return {'up': up and lit >= .04, 'shape': shape}


def _sounds(state, w, dark, indoors=False):
    dt, doy, hour = _when(state)
    r = _rng('sound', dt.date().isoformat(), int(hour))
    month = dt.month
    if w['rain']:
        where = 'on the roof' if indoors else 'on the leaves around me'
        return [f'{w["rain"]} pattering {where}' if w['rain'] != 'heavy rain' else f'heavy rain drumming {where}']
    pool = []
    if w['wind'] == 'windy':
        pool.append('wind roaring through the bare branches' if month in (11, 12, 1, 2, 3) else 'wind rushing through the leaves')
    if dark:
        pool += ['a long, wavering hoot from the trees', 'an answering sharp call further off']
        if month in (12, 1, 2):
            pool.append('a harsh scream somewhere in the dark wood')
        if month in (6, 7, 8):
            pool.append('a soft whirring of moths near the cabin')
        if w['wind'] == 'still':
            pool += ['a deep quiet, with only the spring trickling', 'twigs cracking as something moves in the dark']
    else:
        dawn = abs(hour - 7.5) < 1.5 if month in (11, 12, 1) else abs(hour - 5.5) < 1.5
        if dawn and month in (3, 4, 5, 6):
            pool.append('birds singing all at once from every tree')
        if month in (10, 11, 12, 1, 2):
            pool += ['a single small bird singing a thin, sweet song from a bush', 'harsh cawing from the tall trees',
                     'dry leaves rustling as a small animal turns them over']
        if month in (2, 3, 4):
            pool.append('a rapid drumming on wood from somewhere in the trees')
        if month in (4, 5, 6):
            pool.append('a two-note call repeating far away in the wood')
        if month in (5, 6, 7, 8):
            pool += ['bees and insects humming in the warm air', 'birds chattering in the leaves']
        pool += ['a soft cooing from high in a tree', 'the spring trickling into its basin']
    return r.sample(pool, k=min(2, len(pool)))


def outside(state):
    """One or two sentences: what he can sense of the weather, sky and wood, from where he is."""
    w = weather(state)
    dark = state.get('daylight', 1) < .12
    indoors = state.get('location') in ('cabin', 'library', 'cafe', 'shop', 'workbench')
    feel = _warmth(w['temp'])
    parts = []
    if w['rain']:
        parts.append(f"It's {feel} and {w['rain']} is falling" + (', blown by the wind' if w['wind'] == 'windy' else '') + '.')
    elif dark:
        m = moon(state)
        if w['sky'] == 'clear':
            sky = 'the sky is clear and full of stars' + (f', with {m["shape"]}' if m['up'] else '')
        elif w['sky'] == 'cloudy':
            sky = 'clouds hide most of the stars' + (f'; {m["shape"]} shows between them' if m['up'] else '')
        else:
            sky = 'low cloud hides the sky, and it is very dark'
        parts.append(f"It's a {feel} night; {sky}.")
    else:
        sky = {'clear': 'the sun is out', 'cloudy': 'the sun comes and goes behind clouds', 'overcast': 'the sky is grey'}[w['sky']]
        parts.append(f"It's {feel}; {sky}" + (' and the wind is up' if w['wind'] == 'windy' else ' and a breeze moves the branches' if w['wind'] == 'breeze' else '') + '.')
    if w['frost']:
        parts.append('Frost whitens the grass.')
    elif w['mist']:
        parts.append('Mist hangs low over the clearing.')
    if w['temp'] < 6 and not indoors:
        parts.append('My breath shows in the air.')
    if indoors and inside_line(state):
        parts.append(inside_line(state))
    if state.get('location') == 'shop':
        parts.append(edda_line(state))
    heard = _sounds(state, w, dark, indoors)
    if heard:
        parts.append(('From inside I can hear ' if indoors else 'I can hear ') + ' and '.join(heard) + '.')
    return ' '.join(parts)


def stove_lit(state):
    """Is his stove burning (v0.30.19)? It burns until the wood he put in is gone."""
    try:
        return bool(state.get('stove_until')) and datetime.fromisoformat(state['clock']['iso']) < datetime.fromisoformat(state['stove_until'])
    except (KeyError, ValueError, TypeError):
        return False


WARM_INSIDE = {'cafe': 'It is warm in here from the stove.', 'library': 'It is warm in here from the stove.'}


def felt_temp(state, action=None):
    """How warm it is where he is, in degrees (kept to himself). Sleeping is under the covers in his bed, which is
    warm; the cabin has no fire and is open on its south side, so it is barely warmer than outside; the cafe and the
    reading cabin have stoves; Edda's post is warm while she is there by day."""
    w = weather(state)
    _, _, hour = _when(state)
    loc = state.get('location')
    t = w['temp']
    if action == 'sleep' or (action == 'rest' and state.get('in_bed') and loc == 'cabin'):
        return max(18., t)   # under the covers (and no cooler than the night)
    # v0.31.3: on a cold day a stove warms a room; on a hot day a roof's shade keeps it a little cooler than outside.
    if loc in ('cafe', 'library'):
        return 19. if t < 17 else t - 2
    if loc == 'shop' and 7 <= hour < 19:
        return 17. if t < 15 else t - 2
    if loc == 'shop':   # v0.36.11: at night her stove is banked low, not out: cool, but out of the wind and far from freezing
        return max(t + 2., 12.) if t < 14 else t - 2
    import handwork
    if handwork.lit_here(state):   # v0.32.0: beside his own fire
        return max(17., t) if loc == 'cabin' else max(15., t + 8)
    if loc == 'cabin' and stove_lit(state):
        return max(16., t)   # warm through, though the open south side lets some of it out
    if loc in ('cabin', 'shop'):
        return t + 2. if t < 14 else t - 2.
    return w['temp'] - (2 if w['wind'] == 'windy' else 0) - (2 if w['rain'] else 0)


# v0.34.5: Edda as he sees her: an elf woman behind her counter, and what her hands are busy with at this hour.
EDDA_LOOK = ('Edda is behind her counter: a tall elf woman, older than me, her chestnut hair in a long braid with grey '
             'at the temples, a moss-green shawl over a rust-brown dress and a worn leather apron')
EDDA_BUSY = {(5, 9): 'stoking the stove and opening the shutters', (9, 12): 'writing slowly in her ledger, her pen scratching',
             (12, 14): 'eating a heel of bread and cheese at the end of the counter', (14, 17): 'sorting seed packets into their trays',
             (17, 20): 'sweeping round the stove and banking it up', (20, 24): 'counting the day\'s coins by lamplight',
             (0, 5): 'dozing in her chair by the banked stove, a blanket over her knees'}


def edda_line(state):
    _, _, hour = _when(state)
    busy = next(v for (a, b), v in EDDA_BUSY.items() if a <= hour < b)
    return f'{EDDA_LOOK}; she is {busy}.'


def inside_line(state):
    """Indoors: what the room itself is like for warmth, plainly."""
    loc = state.get('location')
    _, _, hour = _when(state)
    if loc in WARM_INSIDE:
        return WARM_INSIDE[loc]
    if loc == 'shop' and 7 <= hour < 19:
        return "It is warm in the post from Edda's stove."
    if loc == 'shop':
        return "Edda's stove is banked low for the night: the post is cool, but out of the wind and much warmer than outside."
    if loc == 'cabin' and stove_lit(state):
        return 'The stove is burning, and the cabin is warm.'
    if loc == 'cabin':
        t = felt_temp(state)
        if t < 12 and state.get('possessions', {}).get('stove'):
            return ('Inside my cabin it is almost as ' + _warmth(t) + ' as outside: the stove is cold, and the open south '
                    'side lets the air in. Under the covers, my bed is the warm place here.')
        if t < 12:
            return ('Inside my cabin it is almost as ' + _warmth(t) + ' as outside: there is no fire, and the open south '
                    'side lets the air in. Under the covers, my bed is the warm place here.')
    return ''
