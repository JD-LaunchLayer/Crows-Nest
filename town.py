"""The wider settlement: an internet café, a trading post and a few unexplained things.

Jordan supplies these places and their rules; Crow decides whether and how to
use them. Decorations carry only physical details that can be observed on
inspection, never an explanation of what they are for. The trading post is an
unattended post with posted rates and a ledger of his trade credit. Its stock is
finite; only Jordan restocks it (tools/stock_shop.py). Items Crow asks for are
recorded as requests so Jordan can decide whether to stock them.
"""
import math

from world_state import part

POST = 'trading_post'
CAFE = 'internet_cafe'

# Posted exchange rates (trade credit). Authored world rules, adjustable by Jordan.
SELL_RATES = {'wood': {'kg_per_credit': 3}, 'stone': {'kg_per_credit': 5}}
JOBS = {
    'sweep_post': {'name': 'Sweep and tidy the trading post', 'minutes': 30, 'credit': 1, 'effort': 'light'},
    'carry_crates': {'name': 'Carry delivered crates into the store room', 'minutes': 60, 'credit': 2, 'effort': 'heavy'},
}
# Effects are the only ways goods can change his world: 'pantry:N' adds ready food,
# 'possession:NAME' gives him an item he keeps. Known possessions with mechanics:
#   lantern  - lets him make out nearby detail when observing or inspecting in the dark
#   whetstone - keeps his carving blade keen (narrower carving error)
# Any other possession is simply owned: it exists, with no invented ability.
STARTING_STOCK = {
    'provisions_bundle': {'name': 'Bundle of bread, cheese and dried fruit (4 servings)', 'price': 3, 'qty': 6, 'effect': 'pantry:4'},
    'lantern': {'name': 'Oil lantern', 'price': 6, 'qty': 1, 'effect': 'possession:lantern'},
    'whetstone': {'name': 'Whetstone', 'price': 4, 'qty': 1, 'effect': 'possession:whetstone'},
}


def _building(ident, name, x, z, roof, wall, w=5., d=4.):
    parts = [part('floor', 0, .05, 0, w, .1, d, '#7c6f5a'),
             part('back', 0, 1.4, -d / 2, w, 2.8, .18, wall), part('left', -w / 2, 1.4, 0, .18, 2.8, d, wall),
             part('right', w / 2, 1.4, 0, .18, 2.8, d, wall),
             part('front_left', -w / 2 + .8, 1.4, d / 2, 1.6, 2.8, .18, wall),
             part('front_right', w / 2 - .8, 1.4, d / 2, 1.6, 2.8, .18, wall),
             part('lintel', 0, 2.55, d / 2, w - 3.2, .5, .18, wall),
             part('roof', 0, 3.0, 0, w + .6, .25, d + .6, roof)]
    return {'id': ident, 'name': name, 'kind': 'building', 'x': x, 'z': z, 'portable': False, 'revision': 0, 'parts': parts}


def _stone(p):
    p['material'] = 'stone'
    return p


def _shape(p, shape):
    p['shape'] = shape
    return p


def decorations():
    statue = {'id': 'weathered_figure', 'name': 'Weathered stone figure', 'kind': 'decoration', 'x': -5., 'z': 4.5,
              'portable': False, 'revision': 0,
              'parts': [_stone(part('plinth', 0, .35, 0, .8, .7, .8, '#8d8a80')),
                        _stone(_shape(part('body', 0, 1.05, 0, .55, .7, .45, '#9a978c'), 'sphere')),
                        _stone(_shape(part('head', 0, 1.5, .08, .32, .32, .3, '#9a978c'), 'sphere')),
                        _stone(_shape(part('ear_l', -.07, 1.8, .05, .08, .35, .06, '#9a978c'), 'cone')),
                        _stone(_shape(part('ear_r', .07, 1.8, .05, .08, .35, .06, '#9a978c'), 'cone'))],
              'details': ['A crouching animal with long upright ears, carved in pale stone and worn smooth.',
                          'One ear is chipped at the tip.', 'Yellow-grey lichen grows on its north-facing side.',
                          'Letters on the plinth are too worn to read; only a final "-ER" is clear.']}
    dial = {'id': 'bronze_dial', 'name': 'Bronze dial on a plinth', 'kind': 'decoration', 'x': 4.2, 'z': -3.8,
            'portable': False, 'revision': 0,
            'parts': [_stone(_shape(part('plinth', 0, .5, 0, .45, 1.0, .45, '#8d8a80'), 'cylinder')),
                      _shape(part('plate', 0, 1.03, 0, .7, .04, .7, '#9c7a3c'), 'cylinder'),
                      _shape(part('blade', 0, 1.15, 0, .03, .22, .3, '#7d5f2c'), 'box')],
            'details': ['A flat bronze disc engraved with the numerals I to XII around its edge.',
                        'A triangular bronze blade stands upright across the middle of the disc.'],
            'dynamic': 'shadow'}
    ring = {'id': 'stone_ring', 'name': 'Ring of standing stones', 'kind': 'decoration', 'x': 15., 'z': -14.,
            'portable': False, 'revision': 0, 'parts': [],
            'details': ['Nine rough stones stand in a circle about four metres across.',
                        'They differ in height; the tallest stands on the north-east side.',
                        'The grass inside the circle is shorter than outside it.']}
    for i in range(9):
        a = i * 2 * math.pi / 9 + .3
        h = 1.0 + (1.0 if i == 1 else (i % 3) * .25)
        ring['parts'].append(_stone(part(f'stone_{i + 1}', round(math.cos(a) * 2, 2), h / 2, round(math.sin(a) * 2, 2),
                                         .45, h, .35, '#7f7f78')))
    chimes = {'id': 'hanging_tubes', 'name': 'Hanging tubes on a frame', 'kind': 'decoration', 'x': -4.5, 'z': 14.,
              'portable': False, 'revision': 0,
              'parts': [part('post_l', -.6, 1.1, 0, .1, 2.2, .1, '#6b5a42'), part('post_r', .6, 1.1, 0, .1, 2.2, .1, '#6b5a42'),
                        part('bar', 0, 2.15, 0, 1.4, .1, .1, '#6b5a42')],
              'details': ['Five hollow metal tubes of different lengths hang from a wooden crossbar.',
                          'They swing freely and ring when touched; each gives a different note.']}
    for i, length in enumerate([.9, .8, .7, .6, .5]):
        chimes['parts'].append(_shape(part(f'tube_{i + 1}', -.4 + i * .2, 2.05 - length / 2, 0, .05, length, .05, '#b8b8ad'), 'cylinder'))
    return [statue, dial, ring, chimes]


def ensure(state):
    world = state['built_world']
    post = state.setdefault('trading', {'credit': 0., 'stock': {k: dict(v) for k, v in STARTING_STOCK.items()},
                                        'requests': [], 'ledger': []})
    state.setdefault('possessions', {})
    if not world.get('town_added'):
        objects = world['objects']
        cafe = _building(CAFE, 'Internet café', 9., -17., '#5a4f63', '#b9ab8f')
        cafe['details'] = ['Inside are a counter, two chairs and a terminal with a screen and keyboard.',
                           'A notice reads: "Open. Search anything. Be patient with slow pages."']
        shop = _building(POST, 'Trading post', -3., -17., '#6b4e33', '#a99474')
        shop['details'] = ['Shelves, a counter and a slate board of posted rates.',
                           'An honesty box and a ledger record trade credit. No one is behind the counter.']
        for obj in [cafe, shop] + decorations():
            objects.setdefault(obj['id'], obj)
        world['town_added'] = True
        world['revision'] += 1
    if not world.get('town_furnished'):
        furnish(world['objects'])
        world['town_furnished'] = True
        world['revision'] += 1
    keeper(state)
    return post


def _p(ident, x, y, z, w, h, d, color, shape='box', material='wood'):
    p = part(ident, x, y, z, w, h, d, color)
    p['shape'] = shape
    p['material'] = material
    return p


def furnish(objects):
    """Interiors for the café and trading post (added once, also to existing saves)."""
    cafe, post = objects.get(CAFE), objects.get(POST)
    furnished = lambda o: any(p['id'] == 'counter' for p in o['parts'])
    cafe = None if cafe and furnished(cafe) else cafe
    post = None if post and furnished(post) else post
    if cafe:
        cafe['parts'] += [
            _p('counter', -1.4, .45, -1.2, 1.6, .9, .5, '#6b4a32'),
            _p('cup_shelf', -1.4, 1.6, -1.85, 1.3, .05, .25, '#5a3f2b'),
            _p('cups', -1.4, 1.68, -1.85, 1.0, .12, .12, '#e8e1d2', 'cylinder'),
            _p('terminal_desk', 1.3, .375, -1.3, 1.0, .75, .6, '#5a4636'),
            _p('screen', 1.3, 1.0, -1.45, .6, .42, .05, '#7fd0ff'),
            _p('keyboard', 1.3, .77, -1.15, .45, .03, .18, '#2c2c2c'),
            _p('terminal_stool', 1.3, .25, -.65, .35, .5, .35, '#3f3a36', 'cylinder'),
            _p('table', -1.2, .72, .7, .8, .05, .8, '#7a5a3c', 'cylinder'),
            _p('table_leg', -1.2, .36, .7, .08, .72, .08, '#4b3a2a', 'cylinder'),
            _p('chair_a', -1.9, .25, .7, .4, .5, .4, '#4f6b5a'),
            _p('chair_b', -.5, .25, .7, .4, .5, .4, '#4f6b5a'),
            _p('lamp', 0, 2.35, 0, .3, .3, .3, '#ffd98a', 'sphere', 'stone')]
        cafe['details'] = ['A counter with a shelf of cups, a small table with two chairs, and a desk with a lit screen and keyboard.',
                           'A notice reads: "Open. Search anything. Be patient with slow pages."']
        cafe['revision'] += 1
    if post:
        post['parts'] += [
            _p('counter', 0, .475, -.6, 2.2, .95, .55, '#5e4330'),
            _p('shelf_low', 0, .8, -1.75, 4.2, .06, .35, '#4e3826'),
            _p('shelf_mid', 0, 1.4, -1.75, 4.2, .06, .35, '#4e3826'),
            _p('shelf_high', 0, 2.0, -1.75, 4.2, .06, .35, '#4e3826'),
            _p('jars', -1.2, 1.55, -1.75, 1.4, .25, .2, '#b48a4a', 'cylinder'),
            _p('bundles', 1.1, .95, -1.75, 1.6, .25, .25, '#8e6f4b'),
            _p('tins', .4, 2.12, -1.75, 1.8, .18, .18, '#7d8c8f', 'cylinder', 'stone'),
            _p('slate_board', -1.6, 1.75, 1.88, 1.1, .75, .05, '#2f3336', 'box', 'stone'),
            _p('crate_a', 1.8, .3, 1.2, .6, .6, .6, '#9b7b52'),
            _p('crate_b', 1.8, .85, 1.15, .5, .5, .5, '#a5875e'),
            _p('barrel', -1.9, .45, 1.1, .6, .9, .6, '#6d5136', 'cylinder'),
            _p('lamp', 0, 2.35, 0, .3, .3, .3, '#ffd98a', 'sphere', 'stone')]
        post['details'] = ['Shelves of jars, bundles and tins, a counter, crates and a barrel, and a slate board of posted rates.',
                           'A ledger records trade credit. Edda Thorne keeps the post and is usually behind the counter.']
        post['revision'] += 1


KEEPER_PERSONA = ('You are Edda Thorne, keeper of the small trading post beside the clearing. You are warm, chatty and fair-minded, '
    'but shrewd: you drive a decent bargain, you notice who keeps their word, and you remember debts and kindnesses. '
    'You have your own small concerns: the store-room roof leaks when it rains, deliveries arrive irregularly, and the post is '
    'often quiet. You speak naturally and briefly, as a person, never as an assistant or narrator. You know only what Crow says '
    'to you and what has happened between you; you cannot read his thoughts. Do not invent events in the world. You can only '
    'change anything through the single proposal you return; the posted board shows normal prices.')


def keeper(state):
    return state.setdefault('keeper', {'name': 'Edda Thorne', 'where': POST, 'notes': [], 'warmth': 0., 'talks': 0,
                                       'favours': [], 'next_favour': 1, 'last_gift': ''})


PROPOSAL_KINDS = ['none', 'sell_item', 'buy_goods', 'favour', 'gift']


def proposal_schema():
    return {'type': 'object', 'additionalProperties': False,
            'required': ['kind', 'item', 'quantity', 'credit', 'minutes', 'task'],
            'properties': {'kind': {'type': 'string', 'enum': PROPOSAL_KINDS}, 'item': {'type': 'string'},
                           'quantity': {'type': 'integer', 'minimum': 1, 'maximum': 20},
                           'credit': {'type': 'number', 'minimum': 0, 'maximum': 60},
                           'minutes': {'type': 'integer', 'minimum': 0, 'maximum': 180}, 'task': {'type': 'string'}}}


def _goods_value(state, item, quantity):
    """Posted value of goods Crow could hand over, or None if he does not have them."""
    if item in SELL_RATES:
        key = 'materials' if item == 'wood' else 'stone'
        if state.get(key, 0) + 1e-9 < quantity:
            return None
        return quantity / SELL_RATES[item]['kg_per_credit']
    obj = state['built_world']['objects'].get(item)
    if not obj or obj.get('kind') != 'carving':
        return None
    creation = next((c for c in state.get('creations', []) if 'carving-' + str(c['id']) == item), {})
    q = creation.get('quality', 5)
    return 1 if q < 5 else 2 if q < 8 else 3


def check_proposal(state, p, day):
    """Is a proposed deal within the world's limits right now? Returns (ok, reason)."""
    post = ensure(state)
    kind = p.get('kind', 'none')
    if kind == 'none':
        return True, ''
    if kind == 'sell_item':
        stock = post['stock'].get(p['item'])
        if not stock or stock['qty'] < p['quantity']:
            return False, 'that is not in stock in that quantity'
        if p['credit'] < .7 * stock['price'] * p['quantity'] - 1e-9:
            return False, 'below what the post can afford to sell for'
        if post['credit'] + 1e-9 < p['credit']:
            return False, 'he does not have that much credit'
        return True, ''
    if kind == 'buy_goods':
        value = _goods_value(state, p['item'], p['quantity'])
        if value is None:
            return False, 'he does not have those goods'
        if p['credit'] > 1.3 * value + 1e-9:
            return False, 'more than the post can pay for them'
        return True, ''
    if kind == 'favour':
        if not 15 <= p['minutes'] <= 180 or not p['task'].strip():
            return False, 'a favour needs a task and 15–180 minutes'
        if p['credit'] > p['minutes'] / 30 * 1.5 + 1e-9:
            return False, 'more pay than the post can give for that work'
        return True, ''
    if kind == 'gift':
        if keeper(state)['last_gift'] == day:
            return False, 'she has already given something today'
        if p['credit'] > 1 + 1e-9:
            return False, 'too generous for the post'
        return True, ''
    return False, 'unknown kind of deal'


def apply_proposal(state, p, at, day):
    """Carry out an agreed deal, re-checked at the moment it is settled."""
    ok, why = check_proposal(state, p, day)
    if not ok:
        return {'success': False, 'text': f'The agreed deal could not be settled: {why}.'}
    post = ensure(state)
    kp = keeper(state)
    kind = p['kind']
    if kind == 'none':
        return {'success': True, 'text': 'No deal was made.'}
    if kind == 'sell_item':
        stock = post['stock'][p['item']]
        post['credit'] = round(post['credit'] - p['credit'], 2)
        stock['qty'] -= p['quantity']
        effect, _, value = stock['effect'].partition(':')
        if effect == 'pantry':
            state['provisions']['pantry'] = round(state['provisions']['pantry'] + float(value) * p['quantity'], 2)
        else:
            state['possessions'][value] = state['possessions'].get(value, 0) + p['quantity']
        text = f'Bought {p["quantity"]} × {stock["name"]} from Edda for {p["credit"]:g} credit (board price {stock["price"] * p["quantity"]:g}).'
    elif kind == 'buy_goods':
        if p['item'] in SELL_RATES:
            key = 'materials' if p['item'] == 'wood' else 'stone'
            state[key] = round(state[key] - p['quantity'], 2)
            what = f'{p["quantity"]:g} kg of {p["item"]}'
        else:
            obj = state['built_world']['objects'].pop(p['item'])
            state['built_world']['revision'] += 1
            what = obj['name']
            for c in state.get('creations', []):
                if 'carving-' + str(c['id']) == p['item']:
                    c['sold'] = at
        post['credit'] = round(post['credit'] + p['credit'], 2)
        text = f'Edda took {what} for {p["credit"]:g} credit.'
    elif kind == 'favour':
        fav = {'id': f'favour-{kp["next_favour"]}', 'task': p['task'].strip()[:160], 'minutes': p['minutes'], 'credit': p['credit'], 'agreed': at}
        kp['next_favour'] += 1
        kp['favours'] = (kp['favours'] + [fav])[-6:]
        text = f'Agreed a favour for Edda: "{fav["task"]}" ({fav["minutes"]} minutes, {fav["credit"]:g} credit). It can be done as job {fav["id"]}.'
    else:
        kp['last_gift'] = day
        post['credit'] = round(post['credit'] + p['credit'], 2)
        text = f'Edda gave him {p["credit"]:g} credit as a gift.'
    _record(post, text, at)
    return {'success': True, 'text': text, 'credit': post['credit']}


def remember(state, note, warmth, at):
    """Edda's own memory of Crow: short, finite, reworded notes merged."""
    import memory_recall
    kp = keeper(state)
    note = ' '.join(str(note).split())[:200]
    if note and not any(memory_recall.similar(n['text'], note) for n in kp['notes']):
        kp['notes'] = (kp['notes'] + [{'text': note, 'at': at}])[-24:]
    if isinstance(warmth, (int, float)) and math.isfinite(warmth):
        kp['warmth'] = round(max(-1., min(1., .8 * kp['warmth'] + .2 * warmth)), 3)
    kp['talks'] += 1


def board(state):
    """What the posted board at the trading post shows."""
    post = ensure(state)
    return {'your_credit': post['credit'],
            'for_sale': {k: {'name': v['name'], 'price': v['price'], 'left': v['qty']} for k, v in post['stock'].items() if v['qty'] > 0},
            'we_buy': {'wood': '1 credit per 3 kg', 'stone': '1 credit per 5 kg',
                       'carving': '1–3 credit for a carving you made, by how well it turned out'},
            'jobs': {**{k: {'name': v['name'], 'minutes': v['minutes'], 'pays': v['credit']} for k, v in JOBS.items()},
                     **{f['id']: {'name': 'Favour for Edda: ' + f['task'], 'minutes': f['minutes'], 'pays': f['credit']}
                        for f in keeper(state)['favours']}}}


def _record(post, text, at):
    post['ledger'] = (post['ledger'] + [{'at': at, 'text': text, 'credit_after': post['credit']}])[-200:]


def trade(state, mode, item, quantity, at):
    """Carry out one exchange at the posted rates. Returns a world result."""
    post = ensure(state)
    quantity = max(1, min(20, int(quantity or 1)))
    if mode == 'buy':
        stock = post['stock'].get(item)
        if not stock or stock['qty'] <= 0:
            return {'success': False, 'text': 'That item is not in stock at the trading post.'}
        quantity = min(quantity, stock['qty'])
        cost = stock['price'] * quantity
        if post['credit'] + 1e-9 < cost:
            return {'success': False, 'text': f'Not enough trade credit: {stock["name"]} costs {cost:g} and he has {post["credit"]:g}.'}
        post['credit'] = round(post['credit'] - cost, 2)
        stock['qty'] -= quantity
        kind, _, value = stock['effect'].partition(':')
        if kind == 'pantry':
            state['provisions']['pantry'] = round(state['provisions']['pantry'] + float(value) * quantity, 2)
        else:
            state['possessions'][value] = state['possessions'].get(value, 0) + quantity
        text = f'Bought {quantity} × {stock["name"]} for {cost:g} credit. Credit left: {post["credit"]:g}.'
    elif mode == 'sell':
        if item in SELL_RATES:
            key = 'materials' if item == 'wood' else 'stone'
            per = SELL_RATES[item]['kg_per_credit']
            kg = min(state.get(key, 0), per * quantity)
            credits = int(kg // per)
            if credits < 1:
                return {'success': False, 'text': f'Not enough {item} to sell: {per} kg are needed per credit.'}
            state[key] = round(state[key] - credits * per, 2)
            post['credit'] = round(post['credit'] + credits, 2)
            text = f'Sold {credits * per:g} kg of {item} for {credits} credit. Credit now: {post["credit"]:g}.'
        else:
            obj = state['built_world']['objects'].get(item)
            if not obj or obj.get('kind') != 'carving':
                return {'success': False, 'text': 'The trading post only buys wood, stone or carvings he made.'}
            creation = next((c for c in state.get('creations', []) if 'carving-' + str(c['id']) == item), {})
            quality = creation.get('quality', 5)
            credits = 1 if quality < 5 else 2 if quality < 8 else 3
            del state['built_world']['objects'][item]
            state['built_world']['revision'] += 1
            creation['sold'] = at
            post['credit'] = round(post['credit'] + credits, 2)
            text = f'Sold {obj["name"]} for {credits} credit. It now belongs to the trading post. Credit now: {post["credit"]:g}.'
    elif mode == 'job':
        job = JOBS.get(item)
        favour = next((f for f in keeper(state)['favours'] if f['id'] == item), None)
        if favour:
            keeper(state)['favours'].remove(favour)
            post['credit'] = round(post['credit'] + favour['credit'], 2)
            text = f'Did the favour for Edda: "{favour["task"]}" and earned {favour["credit"]:g} credit. Credit now: {post["credit"]:g}.'
            _record(post, text, at)
            return {'success': True, 'text': text, 'credit': post['credit']}
        if not job:
            return {'success': False, 'text': 'There is no such posted job.'}
        post['credit'] = round(post['credit'] + job['credit'], 2)
        text = f'Finished the posted job "{job["name"]}" and earned {job["credit"]} credit. Credit now: {post["credit"]:g}.'
    elif mode == 'ask':
        wanted = ' '.join(str(item).split())[:120]
        if not wanted:
            return {'success': False, 'text': 'He did not say what he was asking for.'}
        same = next((r for r in post['requests'] if r['item'].casefold() == wanted.casefold()), None)
        if same:
            same['times'] += 1
            same['last'] = at
        else:
            post['requests'].append({'item': wanted, 'first': at, 'last': at, 'times': 1})
        post['requests'] = post['requests'][-60:]
        text = f'Wrote "{wanted}" in the request book at the trading post. Nothing appears because of it.'
    else:
        return {'success': False, 'text': 'Unknown kind of trade.'}
    _record(post, text, at)
    return {'success': True, 'text': text, 'credit': post['credit']}


def sundial_reading(at, daylight):
    """Where the dial's shadow falls, from apparent solar time at Wickford (about 0.56° E)."""
    if daylight < .12:
        return 'No shadow falls on the dial now.'
    utc = at.utctimetuple()
    solar = utc.tm_hour + utc.tm_min / 60 + .56 / 15
    # The shadow points opposite the sun; on a horizontal dial it marks the solar hour.
    mark = ((round(solar) - 1) % 12) + 1
    numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
    return f'The blade casts a shadow on the disc, lying near the {numerals[mark - 1]} mark.'


def inspect(state, ident, at, daylight):
    """Physical details only. Returns None for objects without authored details."""
    obj = state['built_world']['objects'].get(ident)
    if not obj or 'details' not in obj:
        return None
    if daylight < .12 and not state.get('possessions', {}).get('lantern'):
        return {'success': True, 'text': f'Too dark to make out the {obj["name"].lower()} clearly; only its outline is visible.'}
    details = list(obj['details'])
    if obj.get('dynamic') == 'shadow':
        details.append(sundial_reading(at, daylight))
    if ident == POST:
        details.append('The board shows: ' + str(board(state)))
    return {'success': True, 'text': f'Inspected the {obj["name"].lower()}. ' + ' '.join(details), 'findings': [{'about': ident, 'text': d} for d in details]}


ORDERS = 'crow-stock-orders.json'


def apply_stock_orders(state, root, at):
    """Jordan's restocking (written by tools/stock_shop.py) is picked up while Crow runs."""
    path = root / ORDERS
    if not path.exists():
        return []
    import json
    try:
        orders = json.loads(path.read_text())
    except (OSError, ValueError):
        return []
    path.unlink()
    post = ensure(state)
    done = []
    for o in orders if isinstance(orders, list) else []:
        ident = str(o.get('id', '')).strip()[:40]
        effect = str(o.get('effect', ''))
        kind, _, value = effect.partition(':')
        if not ident or kind not in ('pantry', 'possession') or not value:
            continue
        if kind == 'pantry':
            try:
                float(value)
            except ValueError:
                continue
        item = post['stock'].setdefault(ident, {'name': str(o.get('name', ident))[:80], 'price': 1, 'qty': 0, 'effect': effect})
        item.update(name=str(o.get('name', item['name']))[:80], effect=effect,
                    price=max(0, float(o.get('price', item['price']))))
        item['qty'] += max(0, int(o.get('qty', 1)))
        done.append(f"{item['name']} (now {item['qty']} at {item['price']:g} credit)")
    if done:
        _record(post, 'New stock arrived: ' + '; '.join(done) + '.', at)
    return done
