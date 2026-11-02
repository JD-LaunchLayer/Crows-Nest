"""What each food is worth to his body, and how long it keeps (v0.26).

A character sheet for food. The numbers are authored world properties and are never shown
to Crow: he sees what a food is and how many servings he has, and he feels the rest. A
serving of something filling keeps hunger away for longer than a serving of something light.

- fill: how much one serving gives his stomach (and, as it digests, his reserve). The old
  single "serving" was 22; a light handful of berries is far less, a plate of venison more.
- keeps: days it stays good in cool weather (None: keeps for months). Warm weather
  shortens it; fresh meat in summer lasts a day or two.

The larder is a list of lots (what, how many servings, when it goes off). provisions['pantry']
stays as the total, so everything that reads the total still works; if anything changes the
total directly, the difference is reconciled as plain provisions (or taken from the oldest).
"""
from datetime import datetime

FOODS = {
    'provisions':      {'name': 'bread, cheese and dried fruit', 'fill': 22, 'keeps': None},
    'berries':         {'name': 'wild fruit', 'fill': 9, 'keeps': 2},
    'mixed vegetables': {'name': 'mixed vegetables', 'fill': 15, 'keeps': 10},
    'salad leaves':    {'name': 'salad leaves', 'fill': 5, 'keeps': 4},
    'radishes':        {'name': 'radishes', 'fill': 5, 'keeps': 10},
    'potatoes':        {'name': 'potatoes', 'fill': 26, 'keeps': 120},
    'broad beans':     {'name': 'broad beans', 'fill': 20, 'keeps': 7},
    'garlic':          {'name': 'garlic', 'fill': 4, 'keeps': 150},
    'onions':          {'name': 'onions', 'fill': 10, 'keeps': 120},
    'venison':         {'name': 'fresh meat', 'fill': 34, 'keeps': 5},
    'smoked venison':  {'name': 'smoked meat', 'fill': 30, 'keeps': 120},
}


def today(state):
    """Crow's day number on his own calendar (fractional)."""
    try:
        return datetime.fromisoformat(state['clock']['iso']).timestamp() / 86400
    except (KeyError, ValueError, TypeError):
        return 0.


def _doy(state):
    try:
        return datetime.fromisoformat(state['clock']['iso']).timetuple().tm_yday
    except (KeyError, ValueError, TypeError):
        return 200


def keeps_days(state, food):
    days = FOODS.get(food, FOODS['provisions'])['keeps']
    if days is None:
        return None
    import garden
    w = garden.warmth(_doy(state))      # 0 midwinter .. 1 midsummer
    return days * (1.3 - .9 * w) if food in ('venison', 'berries', 'salad leaves', 'broad beans') else days


def larder(state):
    prov = state['provisions']
    lots = prov.setdefault('larder', [])
    total = round(sum(l['servings'] for l in lots), 2)
    diff = round(prov.get('pantry', 0) - total, 2)
    if diff > .001:          # added directly as plain provisions (older code, Jordan's orders, old saves)
        lots.insert(0, {'food': 'provisions', 'servings': diff, 'spoils_at': None})
    elif diff < -.001:       # taken directly: from the oldest first
        take(state, None, -diff, lots=lots)
    prov['pantry'] = round(sum(l['servings'] for l in lots), 2)
    return lots


def add(state, food, servings):
    lots = larder(state)
    days = keeps_days(state, food)
    lots.append({'food': food, 'servings': round(servings, 2), 'spoils_at': None if days is None else round(today(state) + days, 3)})
    state['provisions']['pantry'] = round(sum(l['servings'] for l in lots), 2)


def take(state, food, servings, lots=None):
    """Take servings of one food (or any, oldest first). Returns [(food, servings)] taken."""
    lots = larder(state) if lots is None else lots
    out, need = [], servings
    for l in sorted([l for l in lots if food in (None, '', l['food'])], key=lambda l: (l['spoils_at'] is None, l['spoils_at'] or 0)):
        if need <= 1e-9:
            break
        got = min(l['servings'], need)
        l['servings'] = round(l['servings'] - got, 3)
        need -= got
        out.append((l['food'], got))
    lots[:] = [l for l in lots if l['servings'] > 1e-3]
    state['provisions']['pantry'] = round(sum(l['servings'] for l in lots), 2)
    return out


def advance(state):
    """Food past its time goes off and is thrown out. Returns what spoiled."""
    lots = larder(state)
    now = today(state)
    gone = [l for l in lots if l['spoils_at'] is not None and now >= l['spoils_at']]
    if gone:
        lots[:] = [l for l in lots if l not in gone]
        state['provisions']['pantry'] = round(sum(l['servings'] for l in lots), 2)
        log = state['provisions'].setdefault('spoiled', [])
        log += [{'food': l['food'], 'servings': l['servings'], 'at': state.get('clock', {}).get('iso', '')} for l in gone]
        del log[:-20]
    return gone


def _lots(state):
    """The larder as it is, without changing anything (reading must never rewrite his saved life)."""
    prov = state['provisions']
    lots = list(prov.get('larder', []))
    diff = round(prov.get('pantry', 0) - sum(l['servings'] for l in lots), 2)
    if diff > .001:
        lots.insert(0, {'food': 'provisions', 'servings': diff, 'spoils_at': None})
    return lots


def view(state):
    """What he can see in the chest: what each thing is, how much, and whether it is going off."""
    now = today(state)
    out = {}
    for l in _lots(state):
        name = FOODS.get(l['food'], FOODS['provisions'])['name']
        if l['spoils_at'] is not None and l['spoils_at'] - now < 1:
            name += ' (starting to go off)'
        out[name] = round(out.get(name, 0) + l['servings'], 2)
    return out


def kinds(state):
    return sorted({l['food'] for l in _lots(state) if l['servings'] > 1e-3})


def fill(food):
    return FOODS.get(food, FOODS['provisions'])['fill']
