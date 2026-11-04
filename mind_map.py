"""His remembered map (v0.36.0, mapping phase 3): places and landmarks as he has known them, never coordinates.

Built only from what he has perceived and done, never from the world's layout: the things he noticed around him
become landmarks he remembers by their look; the places he has been carry what he found there (warm by a stove,
water to drink, food to eat or buy). Memory is not perfect:

- it grows sharper with visits and handling, and fades with disuse (a landmark not seen for weeks is forgotten);
- it can be out of date: when the world changes (a tree felled, a thing moved) the old memory stands until he sees
  it again, and then he notices the difference ("the tall oak I remembered is a stump now");
- places he has never been, and things he never noticed, are not in it at all.

Things come back to mind on cue, as they do for anyone: by what he can see now, by how his body is (cold brings back
where he has been warm, thirst where he has drunk, hunger where he has eaten or bought food), and by what he means
to do. Recall is first-person memory, never an instruction, and only ever of what he has experienced.

update() is the only writer (after each finished activity); recall() and view() are read-only.
"""
import math
from datetime import datetime

import perception

KEEP = 120            # landmarks held at most; the faintest go first
HALF_LIFE_DAYS = 12   # an unvisited memory fades to half in this time
FORGET = .06          # below this a landmark is gone from memory
NEED_WORDS = {
    'warm': lambda p: f'it being warm {p}',
    'water': lambda p: f'drinking {p}',
    'food': lambda p: f'food to be had {p}',
}
PLACE_WORDS = {'cabin': 'in my cabin', 'shop': "in the trading post, by Edda's stove", 'cafe': 'in the café',
               'library': 'in the reading cabin', 'workbench': 'at the workbench', 'range': 'at the archery range',
               'woods': 'in the woods', 'garden': 'in my garden', 'spring': 'at the spring basin'}
WARM_FROM = 15.   # felt degrees: somewhere he was warm without bed or work to thank for it


def ensure(state):
    m = state.setdefault('mind_map', {'version': 1, 'landmarks': {}, 'places': {}, 'changes': []})
    m.setdefault('changes', [])
    return m


def _now(state):
    try:
        return datetime.fromisoformat(state['clock']['iso'])
    except (KeyError, ValueError, TypeError):
        return None


def _age_days(state, iso):
    now = _now(state)
    try:
        return max(0., (now - datetime.fromisoformat(iso)).total_seconds() / 86400) if now else 0.
    except (ValueError, TypeError):
        return 0.


def strength(state, entry):
    """How clearly he remembers it now: built up by visits, fading with time since he last saw it."""
    return entry.get('conf', .3) * .5 ** (_age_days(state, entry.get('last', '')) / HALF_LIFE_DAYS)


def _short(phrase):
    """'a tall oak with bare branches, behind me, a short way off' -> 'a tall oak with bare branches' (where it was is
    not kept as words: from elsewhere 'behind me' would be wrong)."""
    return phrase.split(', ahead of me')[0].split(', behind me')[0].split(', to my')[0].split(', within reach')[0]


# ---- The one writer ----

def update(state, action=None, felt=None):
    """After an activity: what he noticed becomes remembered; the place keeps what he found there; old memories
    that no longer match what he sees are noticed as changed; the faintest are forgotten."""
    m = ensure(state)
    iso = (state.get('clock') or {}).get('iso', '')
    loc = state.get('location', 'cabin')
    place = m['places'].setdefault(loc, {'first': iso, 'visits': 0, 'warm': 0, 'water': 0, 'food': 0})
    place['visits'] += 1
    place['last'] = iso
    if felt is not None and felt >= WARM_FROM and action not in ('sleep',) and not (action == 'rest' and state.get('in_bed')):
        place['warm'] += 1
    if action == 'drink':
        m['places'].setdefault('spring', {'first': iso, 'visits': 0, 'warm': 0, 'water': 0, 'food': 0})
        m['places']['spring'].update(water=m['places']['spring']['water'] + 1, last=iso)
    if action == 'eat':
        place['food'] += 1
    if action == 'trade' and any('Bought' in str(l.get('text', '')) and str(l.get('at', ''))[:13] == iso[:13]
                                 for l in state.get('trading', {}).get('ledger', [])[-3:]):
        place['food'] += 1
    for s in perception.view(state)[:8]:
        words = _short(s['phrase'])
        old = m['landmarks'].get(s['handle'])
        if old and old['words'] != words and old['kind'] in ('tree', 'object', 'building', 'heap', 'fire'):
            m['changes'] = (m['changes'] + [{'at': iso, 'text': f"{old['words'][0].upper() + old['words'][1:]} I remembered is {words} now."}])[-6:]
        entry = m['landmarks'].setdefault(s['handle'], {'first': iso, 'visits': 0, 'conf': .2, 'kind': s['kind'], 'place': loc})
        entry.update(words=words, last=iso, place=loc, conf=round(min(1., strength(state, entry) + .15), 3))
        entry['visits'] += 1
    # Forget what has faded away; keep the clearest within what one mind holds.
    alive = {k: v for k, v in m['landmarks'].items() if strength(state, v) >= FORGET}
    if len(alive) > KEEP:
        alive = dict(sorted(alive.items(), key=lambda kv: -strength(state, kv[1]))[:KEEP])
    m['landmarks'] = alive
    return m


def seed(state):
    """Once: what his existing life already shows he knows, at low confidence. Nothing he never experienced is added."""
    m = ensure(state)
    if m.get('seeded'):
        return m
    places = {'trade': 'shop', 'talk': 'shop', 'browse': 'cafe', 'read': 'library', 'eat': 'cabin', 'sleep': 'cabin',
              'rest': 'cabin', 'craft': 'workbench', 'practise': 'range', 'explore': 'woods', 'garden': 'garden'}
    for mem in state.get('memories', []):
        if mem.get('kind') != 'experience':
            continue
        a, iso = mem.get('action'), mem.get('at', '')
        loc = places.get(a)
        if a == 'drink':
            loc = 'spring'
        if not loc:
            continue
        p = m['places'].setdefault(loc, {'first': iso, 'visits': 0, 'warm': 0, 'water': 0, 'food': 0})
        p['visits'] += 1
        p['last'] = iso
        hour = int(iso[11:13]) if len(iso) > 13 and iso[11:13].isdigit() else 12
        if loc in ('cafe', 'library') or (loc == 'shop' and 7 <= hour < 19):
            p['warm'] += 1   # those rooms have stoves; he was in them
        if a == 'drink':
            p['water'] += 1
        if a == 'eat' or (a == 'trade' and 'Bought' in str(mem.get('event', '')) and ('bread' in str(mem.get('event', '')) or 'food' in str(mem.get('event', '')))):
            p['food'] += 1
    try:
        import resources
        for ident, label in resources.known(state).items():
            m['landmarks'].setdefault(ident, {'first': '', 'last': '', 'visits': 1, 'conf': .25, 'kind': 'ground', 'place': 'woods', 'words': label})
    except Exception:
        pass
    m['seeded'] = True
    return m


# ---- Read-only ----

def recall(state, wide=False, want=''):
    """What comes back to him about places, on cue: first-person memory, never advice. Read-only."""
    m = state.get('mind_map') or {}
    places = m.get('places', {})
    b = state.get('body', {})
    here = state.get('location')
    out = []
    cues = []
    if b.get('chill', 0) > .15:
        cues.append('warm')
    if b.get('hydration', 100) < 65:
        cues.append('water')
    if b.get('reserve', 100) < 65 and b.get('stomach', 20) < 8:
        cues.append('food')
    for need in cues:
        known = sorted(((k, v) for k, v in places.items() if v.get(need) and k != here), key=lambda kv: -kv[1][need])
        for k, v in known[:1 if not wide else 2]:
            out.append('I remember ' + NEED_WORDS[need](PLACE_WORDS.get(k, 'there')) + '.')
    words = {w for w in str(want or state.get('current_intention', '')).lower().replace(',', ' ').split() if len(w) > 4}
    if words:
        for k, v in sorted(m.get('landmarks', {}).items(), key=lambda kv: -strength(state, kv[1])):
            if words & set(v.get('words', '').lower().split()) and strength(state, v) >= .15:
                where = PLACE_WORDS.get(v.get('place'), '')
                out.append(f"I remember {v['words']}{' ' + where if where else ''}" + ('.' if strength(state, v) > .4 else ', though not clearly.'))
                if len(out) >= (3 if not wide else 6):
                    break
    budget = 600 if wide else 250
    kept, used = [], 0
    for line in out:
        if used + len(line) > budget:
            break
        kept.append(line)
        used += len(line)
    return kept


def changes(state):
    """Differences he has just noticed from what he remembered (shown once, in his next moment)."""
    m = state.get('mind_map') or {}
    iso = (state.get('clock') or {}).get('iso', '')
    return [c['text'] for c in m.get('changes', []) if _age_days(state, c['at']) < .25 and c['at'] <= iso]


def view(state):
    """For Jordan's owner-only panel: what he remembers and how clearly."""
    m = state.get('mind_map') or {}
    marks = sorted(((v.get('words', k), round(strength(state, v), 2), v.get('place', '')) for k, v in m.get('landmarks', {}).items()), key=lambda x: -x[1])
    return {'places': {k: {x: v.get(x, 0) for x in ('visits', 'warm', 'water', 'food')} for k, v in m.get('places', {}).items()},
            'landmarks': marks[:30]}
