"""The one world layout (v0.34.0, mapping phase 1b): the fixed scenery both his world and the 3D view are built from.

data/world_layout.json holds the green, the lanes, the square, his cabin's walls, the range target, the spring's pool,
the pebbles on the grass, where he stands at each place, the named landmarks and the ecology regions. Before this,
the same places were written out separately in about eight files and did not quite agree, and some scenery (the lanes,
the pond, the cabin walls) existed only on screen. Now the server and the 3D view read the same file, so what Jordan
sees is what is there for Crow.

Trees, placed objects, raw-material places, heaps and animals stay in his save (they change); they are looked up
alongside this. Crow never sees any of these numbers. Reading never changes anything.
"""
import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parent / 'data' / 'world_layout.json'
BLOCKS = ('solid', 'low', 'passable')
_LAYOUT = None


def validate(data):
    """Raise ValueError on anything malformed."""
    if not isinstance(data, dict) or data.get('version') != 1:
        raise ValueError('world_layout.json: version 1 expected')
    for key in ('body_radius', 'bounds', 'places', 'doors', 'landmarks', 'regions', 'green', 'ring_lane', 'square', 'lanes', 'items', 'pebbles'):
        if key not in data:
            raise ValueError(f'world_layout.json: {key!r} missing')
    for name, p in data['places'].items():
        if len(p.get('stand', [])) != 2 or not p.get('words'):
            raise ValueError(f'place {name}: needs a stand point and words')
    seen = set()
    for item in data['items']:
        for key in ('id', 'kind', 'x', 'z', 'blocks', 'look'):
            if key not in item:
                raise ValueError(f'item {item.get("id", "?")}: {key!r} missing')
        if item['id'] in seen:
            raise ValueError(f'item {item["id"]!r} is listed twice')
        if item['blocks'] not in BLOCKS:
            raise ValueError(f'item {item["id"]}: blocks must be one of {BLOCKS}')
        if 'r' not in item and not ('w' in item and 'd' in item):
            raise ValueError(f'item {item["id"]}: needs a radius or a width and depth')
        seen.add(item['id'])
    for lane in data['lanes']:
        if len(lane.get('points', [])) < 2 or lane.get('width', 0) <= 0:
            raise ValueError(f'lane {lane.get("name", "?")}: needs two points and a width')
    return data


def get():
    global _LAYOUT
    if _LAYOUT is None:
        _LAYOUT = validate(json.loads(DATA.read_text()))
    return _LAYOUT


def body_radius():
    return get()['body_radius']


def stand(place):
    """Where he stands at a place (x, z); the middle of the green for a name that is not a place."""
    p = get()['places'].get(place)
    return tuple(p['stand']) if p else (0., 0.)


def place_spots():
    return {k: list(p['stand']) for k, p in get()['places'].items()}


def footprint(item):
    """(x, z, width, depth) of an item; a round one as its bounding square."""
    if 'r' in item:
        return item['x'], item['z'], 2 * item['r'], 2 * item['r']
    return item['x'], item['z'], item['w'], item['d']


def solids():
    """Footprints of everything fixed that nothing can stand or be put inside: walls, the target, the pool."""
    return [footprint(i) for i in get()['items'] if i['blocks'] == 'solid']


def landmarks():
    return {k: tuple(v) for k, v in get()['landmarks'].items()}


def regions():
    return {k: dict(v) for k, v in get()['regions'].items()}


def region_of(x, z, reach=4.):
    """The place whose standing spot is nearest (x, z), if he is within reach of it; otherwise None."""
    best = min(get()['places'].items(), key=lambda kv: math.hypot(kv[1]['stand'][0] - x, kv[1]['stand'][1] - z))
    return best[0] if math.hypot(best[1]['stand'][0] - x, best[1]['stand'][1] - z) <= reach else None


# ---- His position (v0.34.0) ----

def ensure_position(state):
    """Give him a real position, worked out from where he already is. Additive; a second run changes nothing."""
    if state.get('spatial_version') == 1 and isinstance(state.get('position'), dict):
        return state['position']
    place = state.get('location', 'cabin')
    x, z = stand(place)
    state['position'] = {'x': float(x), 'z': float(z), 'heading': facing(place), 'since': state.get('clock', {}).get('iso', '')}
    state['spatial_version'] = 1
    return state['position']


def destinations(state):
    """Places he can walk to, named as he would name them. Only where he has been, or where he is now.
    The names carry no coordinates."""
    mind = (state.get('mind_map') or {}).get('places', {})
    here = state.get('location')
    places = get()['places']
    keys = set(mind)
    if here in places:
        keys.add(here)
    out = {}
    for key in keys:
        p = places.get(key)
        if p:
            out[p['words']] = (key, float(p['stand'][0]), float(p['stand'][1]))
    if 'spring' in mind and 'the spring' in landmarks():
        x, z, _r = landmarks()['the spring']
        out['the spring'] = ('spring', float(x), float(z))
    return out


def follow(state):
    """His position follows his place when he arrives somewhere new. While he is still on the path (walking), he
    stays where he was, out in the weather, until he arrives. Where he already is stays put."""
    pos = ensure_position(state)
    if state.get('walking'):
        return pos
    place = state.get('location', 'cabin')
    if region_of(pos['x'], pos['z']) == place:
        return pos
    x, z = stand(place)
    pos.update(x=float(x), z=float(z), heading=facing(place), since=state.get('clock', {}).get('iso', ''))
    return pos


def facing(place):
    """Which way he faces at a place's usual spot: as the layout says (into the woods, towards the target), or else
    into the middle of the clearing."""
    p = get()['places'].get(place, {})
    if 'facing' in p:
        return p['facing']
    x, z = stand(place)
    return _facing(x, z)


def _facing(x, z):
    """Facing into the middle of the clearing, as he does at every place's usual spot (radians, 0 = north)."""
    return round(math.atan2(-x, z), 3) if (x or z) else 0.
