"""Birds about the clearing: perched, on the ground or in the air, as wild birds in an English November are.

Authored world life, like the plants. Nothing names them or explains what they do. What can be noticed
is only how a bird looks and where it is; the same birds are drawn in the 3D view for watchers.

Where each bird is follows a fixed schedule from Crow's own clock (deterministic, so the server and
the browser agree): every few minutes it moves to another perch in its usual places, sometimes it is
in the air, and after dark it roosts out of sight in a tree.
"""
import hashlib
import math
from datetime import datetime

# Character sheet (v0.26). look: plain physical description, the only thing Crow can ever perceive.
# species, diet and wariness are for Jordan and for the world's rules; they never reach Crow.
# diet: what it will come down for (see wildlife.FOOD_DIET). wariness 0..1: how slowly it comes to trust someone.
# colours: body, wing, accent, beak (for drawing). size in metres.
BIRDS = [
    {'id': 'bird-1', 'species': 'European robin', 'diet': ['insects', 'scraps', 'fruit'], 'wariness': 0.3, 'look': 'small round brown bird with an orange-red face and breast', 'size': .14,
     'colours': ['#7a5a3c', '#6a4d33', '#d8642c', '#2b2b2b'], 'habits': ['ground', 'low', 'object'], 'areas': ['clearing', 'spring_side']},
    {'id': 'bird-2', 'species': 'Common blackbird', 'diet': ['fruit', 'insects', 'scraps'], 'wariness': 0.5, 'look': 'glossy all-black bird with an orange-yellow beak and a yellow eye-ring', 'size': .25,
     'colours': ['#141414', '#1d1d1d', '#141414', '#e7a52a'], 'habits': ['ground', 'low'], 'areas': ['woodland_edge', 'clearing']},
    {'id': 'bird-3', 'species': 'Common woodpigeon', 'diet': ['seeds', 'greens'], 'wariness': 0.65, 'look': 'plump grey bird with a white patch on the side of its neck and a pinkish breast', 'size': .32,
     'colours': ['#8b8f99', '#7b808a', '#c9a3a6', '#e0b06a'], 'habits': ['tree', 'roof', 'ground'], 'areas': ['woodland_edge', 'clearing', 'deeper_woods']},
    {'id': 'bird-4', 'species': 'Eurasian blue tit', 'diet': ['seeds', 'scraps'], 'wariness': 0.5, 'look': 'tiny bird with a blue cap, white cheeks and a yellow belly', 'size': .11,
     'colours': ['#c9bf4a', '#4f7fb0', '#f2f2ea', '#333333'], 'habits': ['tree', 'low'], 'areas': ['grove', 'woodland_edge']},
    {'id': 'bird-5', 'species': 'Eurasian magpie', 'diet': ['scraps', 'meat', 'fruit'], 'wariness': 0.8, 'look': 'black-and-white bird with a long dark tail that shows a green-blue sheen', 'size': .4,
     'colours': ['#16181c', '#f0f0ea', '#25405a', '#1a1a1a'], 'habits': ['tree', 'ground', 'roof', 'object'], 'areas': ['clearing', 'woodland_edge']},
    {'id': 'bird-6', 'species': 'Carrion crow', 'diet': ['scraps', 'meat'], 'wariness': 0.85, 'look': 'large all-black bird with a heavy black beak', 'size': .45,
     'colours': ['#111216', '#16181e', '#111216', '#111111'], 'habits': ['tree', 'roof', 'ground'], 'areas': ['deeper_woods', 'woodland_edge', 'clearing']},
    {'id': 'bird-7', 'species': 'Eurasian wren', 'diet': ['insects'], 'wariness': 0.85, 'look': 'very small round brown bird with its short tail cocked upright', 'size': .09,
     'colours': ['#8a6a48', '#6e5238', '#8a6a48', '#3a3a3a'], 'habits': ['low', 'ground'], 'areas': ['woodland_edge', 'spring_side', 'grove']},
    {'id': 'bird-8', 'species': 'Eurasian jay', 'diet': ['seeds'], 'wariness': 0.85, 'look': 'pinkish-brown bird with a bright blue patch on its wing and a black tail', 'size': .34,
     'colours': ['#b48a78', '#3d6fb8', '#f2efe6', '#2b2b2b'], 'habits': ['tree', 'ground'], 'areas': ['grove', 'deeper_woods', 'woodland_edge']},
    {'id': 'bird-9', 'species': 'Common chaffinch', 'diet': ['seeds'], 'wariness': 0.55, 'look': 'small bird with a pink breast, a blue-grey head and white bars on its wings', 'size': .15,
     'colours': ['#c48a7c', '#5a4a3c', '#7a8ea6', '#9a9a8a'], 'habits': ['ground', 'tree', 'low'], 'areas': ['woodland_edge', 'clearing']},
    {'id': 'bird-10', 'species': 'Great tit', 'diet': ['seeds', 'scraps'], 'wariness': 0.5, 'look': 'small bird with a black head, white cheeks, a yellow breast and a black stripe down it', 'size': .14,
     'colours': ['#d4c13a', '#5f7a5a', '#111111', '#333333'], 'habits': ['tree', 'low'], 'areas': ['grove', 'deeper_woods']},
]
AIR_SHARE = .2  # share of moments a bird is in the air


def _h(*parts):
    return int(hashlib.sha1(':'.join(map(str, parts)).encode()).hexdigest()[:12], 16)


def _minutes(state):
    try:
        return datetime.fromisoformat(state['clock']['iso']).timestamp() / 60
    except (KeyError, ValueError, TypeError):
        return 0.


def _perches(state, bird, area, ecology):
    """Places this kind of bird uses in an area, as (kind, label, x, y, z)."""
    out = []
    world = state['built_world']
    trees = [t for t in world['trees'].values() if t['stage'] == 'standing' and ecology.in_area(area, t['x'], t['z'])]
    if 'tree' in bird['habits'] or 'low' in bird['habits']:
        for t in trees[:40]:
            high = 'tree' in bird['habits']
            y = t['height'] * (.82 if high else .35)
            out.append(('tree', f'on a {"high" if high else "low"} branch of {t["id"]}', t['x'] + .4, y, t['z'] + .2))
    if 'roof' in bird['habits'] or 'object' in bird['habits']:
        for o in world['objects'].values():
            if not o.get('parts') or not ecology.in_area(area, o['x'], o['z']):
                continue
            top = max(p['y'] + p['height'] / 2 for p in o['parts'])
            if top < .3:
                continue
            if o.get('kind') in ('building', 'structure') and 'roof' in bird['habits']:
                out.append(('roof', f'on the roof of the {o["name"].lower()}', o['x'], top + .05, o['z']))
            elif o.get('kind') not in ('building', 'structure') and 'object' in bird['habits']:
                out.append(('object', f'on top of the {o["name"].lower()}', o['x'], top + .02, o['z']))
    if 'ground' in bird['habits']:
        a = ecology.AREAS[area]
        for k in range(6):
            ang = (_h(bird['id'], area, k) % 628) / 100
            r = (a.get('r') or (a['r_min'] + a['r_max']) / 2) * (.3 + .6 * ((_h(area, k, bird['id']) % 100) / 100))
            if 'r' not in a:
                r = a['r_min'] + (a['r_max'] - a['r_min']) * ((_h(area, k) % 100) / 100)
            x, z = a['x'] + math.cos(ang) * r, a['z'] + math.sin(ang) * r
            out.append(('ground', f'on the ground near ({x:.0f}, {z:.0f})', x, 0., z))
    return out


def where(state, ecology, daylight):
    """Where every bird is right now on Crow's clock."""
    now = _minutes(state)
    out = []
    for b in BIRDS:
        span = 6 + _h(b['id'], 'span') % 14          # minutes between moves, 6-19
        seg = int(now // span)
        if daylight < .12:                            # roosting out of sight for the night
            day = int(now // 1440)
            area = b['areas'][_h(b['id'], day) % len(b['areas'])]
            trees = [t for t in state['built_world']['trees'].values() if t['stage'] == 'standing' and ecology.in_area(area, t['x'], t['z'])]
            t = trees[_h(b['id'], day, 'roost') % len(trees)] if trees else None
            out.append({'id': b['id'], 'mode': 'roost', 'area': area, 'x': (t or {}).get('x', 0) + .3,
                        'y': (t or {}).get('height', 5) * .6, 'z': (t or {}).get('z', 0), 'label': ''})
            continue
        area = b['areas'][_h(b['id'], seg, 'area') % len(b['areas'])]
        trust = state.get('wildlife', {}).get('trust', {}).get(b['id'], 0.)
        if trust >= .7 and _h(b['id'], seg, 'home') % 100 < 60:   # a bird that trusts him stays about his cabin (v0.26)
            k = _h(b['id'], seg, 'spot') % 3
            label, x, y, z = [('on the ground near the cabin door', -9.2, 0., -4.4), ('on the cabin roof', -10., 3.1, -6.),
                              ('on the edge of the provisions chest', -8.4, .72, -8.3)][k]
            out.append({'id': b['id'], 'mode': 'ground' if k == 0 else 'roof' if k == 1 else 'object', 'area': 'clearing',
                        'x': x + (_h(b['id'], 'dx') % 10) / 10 - .5, 'y': y, 'z': z, 'label': label})
            continue
        if _h(b['id'], seg, 'air') % 100 < AIR_SHARE * 100:
            a = ecology.AREAS[area]
            r = a.get('r') or (a['r_min'] + a['r_max']) / 2
            out.append({'id': b['id'], 'mode': 'air', 'area': area, 'x': a['x'], 'y': 7 + _h(b['id'], seg) % 6,
                        'z': a['z'], 'radius': round(min(r, 18) * .6, 1), 'label': f'flying over {ecology.AREAS[area]["name"]}'})
            continue
        perches = _perches(state, b, area, ecology)
        if not perches:
            continue
        kind, label, x, y, z = perches[_h(b['id'], seg, 'perch') % len(perches)]
        out.append({'id': b['id'], 'mode': kind, 'area': area, 'x': round(x, 2), 'y': round(y, 2), 'z': round(z, 2), 'label': label})
    return out


def facts(state, ecology, area, daylight):
    """What can be noticed of birds in an area: their look and where they are, nothing more."""
    looks = {b['id']: b for b in BIRDS}
    out = []
    for w in where(state, ecology, daylight):
        if w['mode'] == 'roost' or not w['label']:
            continue
        if w['area'] == area or (w['mode'] != 'air' and ecology.in_area(area, w['x'], w['z'])):
            b = looks[w['id']]
            out.append((w['id'], f'A {b["look"]} is {w["label"]}.'))
    return out


def view(state, ecology, daylight):
    """For the 3D view: positions and how to draw each bird."""
    looks = {b['id']: b for b in BIRDS}
    return [{**w, 'size': looks[w['id']]['size'], 'colours': looks[w['id']]['colours']} for w in where(state, ecology, daylight)]
