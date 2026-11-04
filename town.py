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
#   whetstone - does nothing by itself; used on a blade it restores the edge
# Any other possession is simply owned: it exists, with no invented ability.
STARTING_STOCK = {
    'provisions_bundle': {'name': 'Bundle of bread, cheese and dried fruit (4 servings)', 'price': 3, 'qty': 6, 'effect': 'pantry:4'},
    'lantern': {'name': 'Oil lantern', 'price': 6, 'qty': 1, 'effect': 'possession:lantern'},
    'whetstone': {'name': 'Whetstone', 'price': 4, 'qty': 1, 'effect': 'possession:whetstone'},
    'seeds': {'name': 'Packet of vegetable seeds (one bed)', 'price': 2, 'qty': 8, 'effect': 'possession:seeds'},
    'salad_seeds': {'name': 'Salad leaf seeds (one bed)', 'price': 1, 'qty': 4, 'effect': 'possession:salad_seeds'},
    'radish_seeds': {'name': 'Radish seeds (one bed)', 'price': 1, 'qty': 4, 'effect': 'possession:radish_seeds'},
    'seed_potatoes': {'name': 'Seed potatoes (one bed)', 'price': 2, 'qty': 3, 'effect': 'possession:seed_potatoes'},
    'broad_bean_seeds': {'name': 'Broad bean seeds (one bed)', 'price': 2, 'qty': 3, 'effect': 'possession:broad_bean_seeds'},
    'garlic_bulbs': {'name': 'Garlic bulbs for planting (one bed)', 'price': 2, 'qty': 3, 'effect': 'possession:garlic_bulbs'},
    'onion_sets': {'name': 'Onion sets (one bed)', 'price': 2, 'qty': 3, 'effect': 'possession:onion_sets'},
    'hazel_sapling': {'name': 'Young hazel tree, bare-rooted', 'price': 2, 'qty': 4, 'effect': 'possession:hazel_sapling'},
    'birch_sapling': {'name': 'Young silver birch, bare-rooted', 'price': 2, 'qty': 3, 'effect': 'possession:birch_sapling'},
    'oak_sapling': {'name': 'Young oak, bare-rooted', 'price': 3, 'qty': 2, 'effect': 'possession:oak_sapling'},
    'harp': {'name': 'Small harp in a cloth case', 'price': 12, 'qty': 1, 'effect': 'possession:harp'},
    'hunting_bow': {'name': 'Hunting bow (ash longbow)', 'price': 10, 'qty': 1, 'effect': 'possession:hunting_bow'},
    'arrows': {'name': 'Broadhead arrow', 'price': 1, 'qty': 12, 'effect': 'possession:arrows'},
    'stove': {'name': 'Small cast-iron wood stove with a flue pipe', 'price': 14, 'qty': 1, 'effect': 'possession:stove'},
}
# Not on the shelves, but the post will buy them (about half this price) and sell them on at it.
OTHER_PRICES = {'hide': 4}
RESTOCK_DAYS = 7  # Edda's delivery comes once a week on Crow's own calendar, topping shelves back up to these levels


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


def money(amount):
    """Gold and silver (v0.27): one gold is ten silver. Stored internally as gold with tenths."""
    tenths = int(round(float(amount) * 10))
    g, s = divmod(abs(tenths), 10)
    parts = ([f'{g} gold'] if g else []) + ([f'{s} silver'] if s else [])
    return ('-' if tenths < 0 else '') + (' '.join(parts) or 'nothing')


def ensure(state):
    world = state['built_world']
    post = state.setdefault('trading', {'credit': 0., 'stock': {k: dict(v) for k, v in STARTING_STOCK.items()},
                                        'requests': [], 'ledger': []})
    state.setdefault('possessions', {})
    for k in ('hunting_bow', 'arrows', 'stove'):          # v0.26: on her shelves from now on (the stove from v0.30.19)
        post['stock'].setdefault(k, dict(STARTING_STOCK[k]))
    if not world.get('town_added'):
        objects = world['objects']
        cafe = _building(CAFE, 'Internet café', 9., -17., '#5a4f63', '#b9ab8f')
        cafe['details'] = ['Inside are a counter, two chairs and a terminal with a screen and keyboard.',
                           'A notice reads: "Open. Search anything. Be patient with slow pages."']
        shop = _building(POST, 'Trading post', -3., -17., '#6b4e33', '#a99474')
        shop['details'] = ['Shelves, a counter and a slate board of posted rates.',
                           'An honesty box and a ledger record what is owed in gold and silver. No one is behind the counter.']
        for obj in [cafe, shop] + decorations():
            objects.setdefault(obj['id'], obj)
        world['town_added'] = True
        world['revision'] += 1
    if not world.get('town_furnished'):
        furnish(world['objects'])
        world['town_furnished'] = True
        world['revision'] += 1
    keeper(state)
    if 'seeds' not in post['stock'] and not post.get('seeds_added'):
        post['stock']['seeds'] = dict(STARTING_STOCK['seeds'])
    post['seeds_added'] = True
    for k, v in STARTING_STOCK.items():  # new lines on the board for older saves (v0.23)
        post['stock'].setdefault(k, dict(v))
    if not world.get('sheet_music_added'):
        import music  # a shelf of sheet music in the reading cabin (v0.24)
        world['objects'].setdefault('sheet_music', {
            'id': 'sheet_music', 'name': 'Shelf of sheet music', 'kind': 'furniture', 'x': -13.6, 'z': 9.2, 'portable': False,
            'revision': 0, 'parts': [_p('post', 0, .55, 0, .06, 1.1, .06, '#5b4a33'), _p('desk', 0, 1.15, 0, .55, .04, .4, '#8a7350')],
            'details': ['A narrow shelf and a slanted reading desk holding sheets of music.',
                        'The music is written as note names with how long each lasts, for example "C4:1 E4:0.5 G4:0.5 R:1".',
                        'The sheets are titled: ' + '; '.join(t['title'] for t in music.SONGBOOK) + '.']})
        world['sheet_music_added'] = True
        world['revision'] += 1
    return post


def weekly_delivery(state, now):
    """Once a week of Crow's time a delivery tops the standard lines back up. Extra lines Jordan stocked stay as they are."""
    post = ensure(state)
    last = post.get('last_delivery')
    if last is None:
        post['last_delivery'] = now.isoformat()
        return None
    from datetime import datetime
    if (now - datetime.fromisoformat(last)).total_seconds() < RESTOCK_DAYS * 86400:
        return None
    for k, v in STARTING_STOCK.items():
        item = post['stock'].setdefault(k, dict(v))
        item['qty'] = max(item['qty'], v['qty'])
    post['last_delivery'] = now.isoformat()
    post['ledger'] = (post.get('ledger', []) + [{'at': now.isoformat(), 'text': 'The weekly delivery arrived; the shelves were topped up.'}])[-LEDGER_KEEP:]
    return True


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
                           'A ledger records his gold and silver. Edda Thorne keeps the post and is usually behind the counter.']
        post['revision'] += 1


KEEPER_PERSONA = ('You are Edda Thorne, keeper of the small trading post beside the clearing. You are warm, chatty and fair-minded, '
    'but shrewd: you drive a decent bargain, you notice who keeps their word, and you remember kindnesses. '
    'Your own small concern is that the post is often quiet. You speak naturally and briefly, as a person, never as an assistant or narrator. You know only what Crow says '
    'to you and what has happened between you; you cannot read his thoughts. Do not invent events in the world. You can only '
    'change anything through the single proposal you return; the posted board shows normal prices. '
    'You keep a kitchen garden yourself and know the ordinary practical basics of growing food and planting trees '
    'in this part of England: what goes in when and roughly how long things take. Share it if he asks. You are not an expert: '
    'for anything deeper or more particular you would say there are books at the reading cabin and a terminal at the café '
    'that can find most things, rather than guessing. A delivery comes once a week and tops your shelves up. '
    'Like most country folk you know the birds and the roe deer in these woods by sight and habit, that patient people who put '
    'out scraps can get birds coming close, and the basics of hunting, butchering and smoking meat; you only say so if asked. '
    'You run the post on your own: nobody else works here or calls by, so never mention other people as if Crow could meet '
    'them or wait for them. Do not describe damage, loose boards, repairs or other things at the post that are not in what '
    'you are told; if you do not know something, such as exactly when the delivery will come, say what you are told or that '
    'you are not sure. You keep no tab and do not hold goods back: every deal is paid in full at the counter when it is '
    'agreed and the goods go with him then, so nobody ever owes you a balance, and you never say they do. '
    'If he asks to pay part now and part later, you say no to the tab kindly. '
    'Your book is what you are told of it: when he asks about a day, go by those entries exactly, read him every one if he '
    'wants them, and never agree that something is in your book, or that money is missing or owed, when it is not.')


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


# What the post asks when it sells on what it bought from Crow (v0.24.4): always more than it paid.
RESALE = {'wood': {'name': 'Seasoned wood, by the kg', 'price': .5, 'effect': 'materials:1'},
          'stone': {'name': 'Building stone, by the kg', 'price': .3, 'effect': 'stone:1'}}


def _board_price(post, item):
    return (post['stock'].get(item) or STARTING_STOCK.get(item) or {}).get('price')


def _stock_in(post, key, name, price, qty, effect, **extra):
    """Goods the post has taken in go on its shelves, at its own selling price."""
    line = post['stock'].setdefault(key, {'name': name, 'price': price, 'qty': 0, 'effect': effect, **extra})
    line['qty'] = round(line['qty'] + qty, 2)
    line.update(extra)


def _give(state, stock, quantity):
    """Hand bought goods to Crow according to what they are."""
    kind, _, value = stock['effect'].partition(':')
    if kind == 'pantry':
        import foods
        foods.add(state, stock.get('food', 'provisions'), float(value) * quantity)
    elif kind == 'materials':
        state['materials'] = round(state.get('materials', 0) + float(value) * quantity, 2)
    elif kind == 'stone':
        state['stone'] = round(state.get('stone', 0) + float(value) * quantity, 2)
    elif kind == 'object':
        obj = dict(stock['object'])
        world = state['built_world']
        world['objects'][obj['id']] = obj
        world['revision'] += 1
        for c in state.get('creations', []):
            if 'carving-' + str(c['id']) == obj['id']:
                c.pop('sold', None)
                c['bought_back'] = True
    else:
        state['possessions'][value] = state['possessions'].get(value, 0) + quantity


def _take(state, item, quantity, at):
    """Crow hands goods to the post: they leave him and go on its shelves. Returns (what, credit) or (None, reason)."""
    post = ensure(state)
    if item in SELL_RATES:
        key = 'materials' if item == 'wood' else 'stone'
        state[key] = round(state[key] - quantity, 2)
        r = RESALE[item]
        _stock_in(post, item, r['name'], r['price'], quantity, r['effect'])
        return f'{quantity:g} kg of {item}'
    obj = state['built_world']['objects'].get(item)
    if obj and obj.get('kind') in ('carving', 'workpiece'):
        paid = _goods_value(state, item, 1) or 2
        state['built_world']['objects'].pop(item)
        state['built_world']['revision'] += 1
        for c in state.get('creations', []):
            if 'carving-' + str(c['id']) == item:
                c['sold'] = at
        _stock_in(post, item, obj['name'] + (' (a carving)' if obj.get('kind') == 'carving' else ''), round(paid * 1.5 + .5), 1, 'object:' + item, object=obj)
        return obj['name']
    state['possessions'][item] -= quantity
    price = _board_price(post, item) or 2
    name = (post['stock'].get(item) or STARTING_STOCK.get(item) or {}).get('name', item.replace('_', ' '))
    _stock_in(post, item, name, price, quantity, 'possession:' + item)
    return f'{quantity} × {name}'


def _made_value(state, obj):
    """What the post pays for something he made: always well above its raw materials, more the better it is made (v0.25)."""
    from world_state import mass
    kg = mass(obj.get('parts', [])) if obj.get('parts') else {}
    raw = kg.get('wood', 0) / SELL_RATES['wood']['kg_per_credit'] + kg.get('stone', 0) / SELL_RATES['stone']['kg_per_credit']
    if obj.get('kind') == 'carving':
        creation = next((c for c in state.get('creations', []) if 'carving-' + str(c['id']) == obj['id']), {})
        quality = creation.get('quality', 5)
    else:  # a shaped workpiece: how closely it came out to what he meant
        m = obj.get('work_measurement') or {}
        err = abs(m.get('actual_width_m', 0) - m.get('target_width_m', 0)) * 1000 if m else 10
        quality = max(1, min(10, round(10 - err / 3)))
    value = raw * 2 + 1 + quality * .25
    return max(1., round(value * 2) / 2)


def _goods_value(state, item, quantity):
    """Posted value of goods Crow could hand over, or None if he does not have them."""
    if item in SELL_RATES:
        key = 'materials' if item == 'wood' else 'stone'
        if state.get(key, 0) + 1e-9 < quantity:
            return None
        return quantity / SELL_RATES[item]['kg_per_credit']
    if state.get('possessions', {}).get(item, 0) >= quantity > 0:  # something he owns: about half its board price
        post = state.get('trading', {})
        price = (post.get('stock', {}).get(item) or STARTING_STOCK.get(item) or {}).get('price', OTHER_PRICES.get(item, 2))
        return max(.5, round(price / 2 * 2) / 2) * quantity
    obj = state['built_world']['objects'].get(item)
    if not obj or not obj.get('parts') or obj.get('kind') not in ('carving', 'workpiece') or not obj.get('portable', True):
        return None
    return _made_value(state, obj)


def check_proposal(state, p, day):
    """Is a proposed deal within the world's limits right now? Returns (ok, reason)."""
    post = ensure(state)
    kind = p.get('kind', 'none')
    if 'credit' in p:   # v0.30.3: money changes hands in whole silver; there is no smaller coin
        p['credit'] = round(float(p['credit'] or 0) * 10) / 10
    if kind == 'none':
        return True, ''
    if kind == 'sell_item':
        stock = post['stock'].get(p['item'])
        if not stock or stock['qty'] < p['quantity']:
            return False, 'that is not in stock in that quantity'
        if p['credit'] < .7 * stock['price'] * p['quantity'] - 1e-9:
            return False, 'below what the post can afford to sell for'
        if post['credit'] + 1e-9 < p['credit']:
            return False, 'he does not have that much money'
        return True, ''
    if kind == 'buy_goods':
        value = _goods_value(state, p['item'], p['quantity'])
        if value is None:
            return False, 'he does not have those goods'
        if p['credit'] > 1.3 * value + 1e-9:
            return False, 'more than the post can pay for them'
        if p['credit'] < .7 * value - 1e-9:   # v0.32.2: the post buys goods; it does not take them for nothing
            return False, 'below what the goods are worth; the post pays for what it takes'
        return True, ''
    if kind == 'favour':
        if not 15 <= p['minutes'] <= 180 or not p['task'].strip():
            return False, 'a favour needs a task and 15–180 minutes'
        job = same_work(p['task'])
        if job:
            open_, why = job_open(state, job, (state.get('clock') or {}).get('iso', ''))
            if not open_:
                return False, f'that work is not needed now: {why}'
            if any(same_work(f['task']) == job for f in keeper(state)['favours']):
                return False, 'he has already agreed to do that work for her'
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
        stock['qty'] = round(stock['qty'] - p['quantity'], 2)
        _give(state, stock, p['quantity'])
        text = f'Bought {p["quantity"]} × {stock["name"]} from Edda for {money(p["credit"])} (board price {money(stock["price"] * p["quantity"])}).'
    elif kind == 'buy_goods':
        what = _take(state, p['item'], p['quantity'], at)
        post['credit'] = round(post['credit'] + p['credit'], 2)
        text = f'Edda took {what} for {money(p["credit"])}.'
    elif kind == 'favour':
        fav = {'id': f'favour-{kp["next_favour"]}', 'task': p['task'].strip()[:160], 'minutes': p['minutes'], 'credit': p['credit'], 'agreed': at}
        kp['next_favour'] += 1
        kp['favours'] = (kp['favours'] + [fav])[-6:]
        text = (f'Agreed a favour for Edda: "{fav["task"]}" ({fav["minutes"]} minutes, {money(fav["credit"])}). '
                f'It is done by working at the trading post as job {fav["id"]}; whatever the work needs is there.')
    else:
        kp['last_gift'] = day
        post['credit'] = round(post['credit'] + p['credit'], 2)
        text = f'Edda gave him {money(p["credit"])} as a gift.'
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


JOB_WORDS = {'sweep_post': ('sweep',), 'carry_crates': ('crate',)}


def same_work(task):
    """The posted job a favour really is, if any (v0.30.3): sweeping the post is sweeping the post, whoever asks for it."""
    t = str(task or '').lower()
    return next((k for k, words in JOB_WORDS.items() if any(w in t for w in words)), None)


def job_open(state, key, at):
    """Posted jobs are real work (v0.26.2): the post is swept once a day; crates come only with the weekly delivery.
    Returns (open, plain words for the board)."""
    post = state.get('trading', {})
    done = post.get('jobs_done', {}).get(key)
    if key == 'carry_crates':
        last = post.get('last_delivery')
        if not last or (done and done >= last):
            return False, 'no crates waiting; they come with the weekly delivery'
        return True, 'crates from the last delivery are waiting in the yard'
    if done and done[:10] == str(at)[:10]:
        return False, 'already done today; needed again tomorrow'
    return True, 'needs doing today'


def next_delivery(state):
    """When the weekly delivery is due on Crow's calendar, in plain words (for Edda, who would know)."""
    from datetime import datetime, timedelta
    last = state.get('trading', {}).get('last_delivery')
    if not last:
        return 'not known yet'
    due = datetime.fromisoformat(last) + timedelta(days=RESTOCK_DAYS)
    return due.strftime('%A %d %B, around %H:00')


def board(state):
    """What the posted board at the trading post shows."""
    post = ensure(state)
    return {'your_money': money(post['credit']), 'money': 'gold and silver; ten silver make one gold',
            'for_sale': {k: {'name': v['name'], 'price': money(v['price']), 'left': v['qty']} for k, v in post['stock'].items() if v['qty'] > 0},
            'we_buy': {'wood': '1 gold per 3 kg', 'stone': '1 gold per 5 kg',
                       'things you made': 'priced by what they are and how well they are made',
                       'things you own': 'about half what the post sells them for'},
            'note': 'What the post buys goes on its shelves and is sold on at the posted price.',
            'what_you_owe': 'nothing: the post keeps no tab; every deal is paid in full when it is made, and goods are handed over then',
            'ledger_latest_entries': [f"{str(l.get('at',''))[5:16].replace('T',' ')} · {l['text']}" for l in post['ledger'][-6:]],
            'jobs': {**{k: {'name': v['name'], 'minutes': v['minutes'], 'pays': money(v['credit']),
                            'now': job_open(state, k, (state.get('clock') or {}).get('iso', ''))[1]} for k, v in JOBS.items()},
                     **{f['id']: {'name': 'Favour for Edda: ' + f['task'], 'minutes': f['minutes'], 'pays': money(f['credit'])}
                        for f in keeper(state)['favours']}}}


LEDGER_KEEP = 5000   # v0.28.3: the post's book keeps its whole history (before, a weekly delivery cut it to the last 60 lines)
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']


def ledger_lookup(state, query, limit=15):
    """Entries in the post's book for a day ("2026-12-03", "12-03", "3 December") or containing a word. Oldest first."""
    import re
    q = str(query).strip().lower()
    book = ensure(state)['ledger']
    day = None
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', q) or re.search(r'\b(\d{1,2})-(\d{1,2})\b', q)
    if m:
        g = m.groups()
        day = f'{int(g[-2]):02d}-{int(g[-1]):02d}'
    else:
        m = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(' + '|'.join(MONTHS) + r')', q) or re.search(r'(' + '|'.join(MONTHS) + r')\s+(\d{1,2})', q)
        if m:
            a, b = m.groups()
            d, mon = (a, b) if a.isdigit() else (b, a)
            day = f'{MONTHS.index(mon) + 1:02d}-{int(d):02d}'
    if day:
        hits = [l for l in book if str(l.get('at', ''))[5:10] == day]
    else:
        words = [w for w in re.findall(r'[a-z]+', q) if len(w) > 2]
        hits = [l for l in book if words and all(w in l['text'].lower() for w in words)]
    return [f"{str(l.get('at', ''))[:16].replace('T', ' ')} · {l['text']}" for l in hits[-limit:]]


def _record(post, text, at):
    post['ledger'] = (post['ledger'] + [{'at': at, 'text': text, 'credit_after': post['credit']}])[-LEDGER_KEEP:]


def trade(state, mode, item, quantity, at):
    """Carry out one exchange at the posted rates. Returns a world result."""
    post = ensure(state)
    by_kg = mode == 'sell' and item in SELL_RATES   # wood and stone are sold by the kilogram he names (v0.32.1)
    quantity = max(1, min(200 if by_kg else 20, int(quantity or 1)))
    if mode == 'buy':
        stock = post['stock'].get(item)
        if not stock or stock['qty'] <= 0:
            return {'success': False, 'text': 'That item is not in stock at the trading post.'}
        quantity = min(quantity, stock['qty'])
        cost = stock['price'] * quantity
        if post['credit'] + 1e-9 < cost:
            return {'success': False, 'text': f'Not enough money: {stock["name"]} costs {money(cost)} and he has {money(post["credit"])}.'}
        post['credit'] = round(post['credit'] - cost, 2)
        stock['qty'] = round(stock['qty'] - quantity, 2)
        _give(state, stock, quantity)
        unit = ' kg' if stock['effect'].split(':')[0] in ('materials', 'stone') else ''
        text = f'Bought {quantity}{unit} × {stock["name"]} for {money(cost)}. Left in his purse: {money(post["credit"])}.'
    elif mode == 'sell':
        if item in SELL_RATES:
            key = 'materials' if item == 'wood' else 'stone'
            per = SELL_RATES[item]['kg_per_credit']
            kg = round(min(float(state.get(key, 0) or 0), quantity), 1)
            credits = int(kg / per * 10 + 1e-6) / 10   # paid in whole silver at the posted rate, rounded down
            if credits < .1:
                return {'success': False, 'text': f'Not enough {item} to sell: he has {float(state.get(key, 0) or 0):g} kg, and the post pays 1 gold per {per} kg.'}
            what = _take(state, item, kg, at)
            post['credit'] = round(post['credit'] + credits, 2)
            text = f'Sold {what} for {money(credits)}; it is on the post\'s shelves now. In his purse: {money(post["credit"])}.'
        else:
            owned = state.get('possessions', {}).get(item, 0)
            if owned:
                quantity = min(quantity, owned)
                credits = _goods_value(state, item, quantity)
            else:
                credits = _goods_value(state, item, 1)
                quantity = 1
            if credits is None:
                return {'success': False, 'text': 'The trading post buys wood, stone, carvings he made, or things he owns; he has none of that.'}
            what = _take(state, item, quantity, at)
            post['credit'] = round(post['credit'] + credits, 2)
            text = f'Sold {what} for {money(credits)}; it belongs to the trading post now. In his purse: {money(post["credit"])}.'
    elif mode == 'job':
        job = JOBS.get(item)
        favour = next((f for f in keeper(state)['favours'] if f['id'] == item), None)
        if favour:
            keeper(state)['favours'].remove(favour)
            work = same_work(favour['task'])
            if work:
                open_, why = job_open(state, work, at)
                if not open_:   # the floor was swept or the crates carried in already: nothing left to do
                    text = f'Went to do the favour for Edda, "{favour["task"]}", but that work is already done ({why}); nothing was paid and the favour lapses.'
                    _record(post, text, at)
                    return {'success': False, 'text': text, 'credit': post['credit']}
                post.setdefault('jobs_done', {})[work] = at
            post['credit'] = round(post['credit'] + favour['credit'], 2)
            text = f'Did the favour for Edda: "{favour["task"]}" and earned {money(favour["credit"])}. In his purse: {money(post["credit"])}.'
            _record(post, text, at)
            return {'success': True, 'text': text, 'credit': post['credit']}
        if not job:
            return {'success': False, 'text': 'There is no such posted job.'}
        open_, why = job_open(state, item, at)
        if not open_:
            return {'success': False, 'text': f'The posted job "{job["name"]}" is not needed now: {why}.'}
        post.setdefault('jobs_done', {})[item] = at
        post['credit'] = round(post['credit'] + job['credit'], 2)
        text = f'Finished the posted job "{job["name"]}" and earned {money(job["credit"])}. In his purse: {money(post["credit"])}.'
    elif mode == 'ledger':
        lines = ledger_lookup(state, item)
        if not lines:
            return {'success': True, 'text': f'Looked through the post\'s ledger for "{str(item)[:60]}": there is no entry for that.'}
        return {'success': True, 'text': f'Looked through the post\'s ledger for "{str(item)[:60]}": ' + ' | '.join(lines), 'ledger': lines}
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
        done.append(f"{item['name']} (now {item['qty']} at {money(item['price'])})")
    if done:
        _record(post, 'New stock arrived: ' + '; '.join(done) + '.', at)
    return done


# How owned things look when he examines them. No uses are stated.
POSSESSION_LOOKS = {
    'harp': ('A small harp of pale wood, about knee height, in a cloth case. It has 19 strings of graded length, '
             'a small lever near the top of each string, and a metal tuning key in a pocket of the case.'),
    'salad_seeds': 'A paper packet of tiny pale seeds.', 'radish_seeds': 'A paper packet of round brown seeds.',
    'seed_potatoes': 'A small sack of potatoes with short purple sprouts.', 'broad_bean_seeds': 'A packet of large flat beans.',
    'garlic_bulbs': 'Two papery garlic bulbs.', 'onion_sets': 'A net of tiny onions.',
    'hazel_sapling': 'A knee-high hazel whip with bare roots wrapped in damp sacking.',
    'birch_sapling': 'A slender young birch with bare roots wrapped in damp sacking.',
    'oak_sapling': 'A small young oak with bare roots wrapped in damp sacking.',
    'lantern': 'A brass and glass oil lantern with a wick, a small oil reservoir and a wire handle.',
    'whetstone': 'A flat grey stone about the length of a hand, fine-grained and smooth, slightly hollowed in the middle.',
    'seeds': 'A paper packet of small dry seeds of mixed sizes.',
    'hunting_bow': 'A plain ash longbow about as tall as he is, with a linen string and a leather grip; it takes a firm pull.',
    'arrows': 'Wooden arrows fletched with grey feathers, each with a broad, flat, sharpened steel head.',
    'hide': 'A raw animal hide, reddish-grey on the hair side, heavy and damp, rolled up.',
    'stove': 'A squat black cast-iron stove on four short legs, with a hinged door, a small ash tray and a pipe that runs up through the roof of his cabin.',
}
# What Edda knows about her goods (only she is told this).
ITEM_KNOWLEDGE = {
    'hunting_bow': ('a hunting bow: an ash longbow, the kind folk round here use for deer. The roe deer keep to the deeper woods '
                    'and come to the edges at dawn and dusk. A hunter gets close and quiet, twenty-odd yards, and a clean shot '
                    'behind the shoulder; a bad shot means a wounded animal and a long follow. A deer has to be gutted and '
                    'skinned and the meat cut up with a good knife the same day or the next; fresh meat keeps only a few days, '
                    'less in warm weather, but smoked slowly over a wood fire it keeps for months. The post will take a hide'),
    'arrows': 'broadhead arrows for hunting, sold singly; a miss in the woods often means a lost arrow',
    'provisions_bundle': 'ready food that keeps well: bread, cheese and dried fruit, about four meals',
    'lantern': 'gives light after dark: you can see what you are doing and work outdoors at night nearly as well as by day',
    'seeds': 'mixed vegetable seeds for one bed: sow from April to August; about two months in summer; tender, so frost kills them and they will not grow in the cold months',
    'salad_seeds': 'salad leaves for one bed: sow April to September; ready in about five weeks of warm weather; nothing grows in winter',
    'radish_seeds': 'radishes for one bed: the quickest crop, about four weeks in warm weather, April to September; useless in winter',
    'seed_potatoes': 'seed potatoes for one bed: plant in April, dig in late summer; a good heavy crop, about six meals; frost kills the tops',
    'broad_bean_seeds': 'broad beans for one bed: hardy; sown now, in October or November, they sit through winter and crop in early summer; or sow in spring',
    'garlic_bulbs': 'garlic for one bed: plant the cloves in autumn, October to December; they need the cold, and are ready next July',
    'onion_sets': 'onion sets for one bed: hardy kinds go in during autumn, others in spring; ready the next summer',
    'hazel_sapling': 'a young hazel, about knee high: plant it in open ground in the dormant season, November to March; it grows quickly and could be cut for poles or firewood in about seven years',
    'birch_sapling': 'a young birch: plant November to March; fast growing, ready to fell in perhaps six or seven years',
    'oak_sapling': 'a young oak: plant November to March; slow, it takes a dozen years or more to make a felling-size tree, and lives for centuries',
    'harp': ('a small lever harp, a good one for learning: 19 strings tuned to the white notes from low C to high G. You pluck '
             'with the pads of the fingers, not the nails. Each string is one note; the little lever at the top of a string '
             'raises it half a step, which is how you get sharps. Tunes are written as note names with how long each lasts; '
             'beginners start with simple folk tunes and get steadier with practice. Fast tunes, big jumps and lots of lever '
             'changes are harder. Music for it can be copied from sheets, made up, or found written down somewhere'),
    'stove': ('a small cast-iron wood stove with a flue pipe: set up in a cabin, it warms the room through for as long as it burns. '
              'It needs lighting and feeding with dry wood, about a kilo and a half an hour, and goes out when the wood is gone. '
              'Fallen wood from the woods burns, and so does the seasoned wood the post sells by the kilo'),
    'whetstone': 'for sharpening blades: drawn along an axe or carving knife it restores a dulled edge; dull blades make chopping slow and carving rough',
}
TOOLS = {'axe', 'carving_knife'}
STOVE_KG_PER_HOUR = 1.5


def use_item(state, item, target, how):
    """Crow tries something he owns. Only real mechanics change anything; everything else is honestly nothing."""
    owned = state.get('possessions', {})
    if not owned.get(item):
        return {'success': False, 'text': 'He does not have that.'}
    target = target if target in TOOLS else ''
    if item == 'whetstone' and target:
        name = target.replace('_', ' ')
        state['tool_condition'][target] = 1.
        return {'success': True, 'text': f'Drew the {name} along the whetstone for a while. The edge now looks bright and even.'}
    if item == 'whetstone':
        return {'success': True, 'text': 'Turned the stone over and rubbed it with his thumb. Nothing else happened.'}
    if item == 'stove':   # v0.30.19: lit and fed with his own wood; it burns as long as the wood lasts
        import re
        from datetime import datetime, timedelta
        wood = state.get('materials', 0)
        if wood < 1:
            return {'success': False, 'text': 'Opened the stove door, but he has no wood to burn in it.'}
        m = re.search(r'(\d+(?:\.\d+)?)\s*kg', str(how))
        kg = round(min(wood, max(1., float(m.group(1)) if m else 4.5), 12.), 1)
        state['materials'] = round(wood - kg, 2)
        try:
            now = datetime.fromisoformat(state['clock']['iso'])
            old = datetime.fromisoformat(state.get('stove_until', '')) if state.get('stove_until') else now
        except (KeyError, ValueError):
            return {'success': False, 'text': 'The stove would not draw.'}
        until = max(now, old) + timedelta(hours=kg / STOVE_KG_PER_HOUR)
        state['stove_until'] = until.isoformat()
        hours = (until - now).total_seconds() / 3600
        return {'success': True, 'text': f'Laid {kg:g} kg of wood in the stove and lit it. It draws well; the cabin is warming, '
                                         f'and there is enough in it to burn for about {round(hours)} hour{"s" if round(hours) != 1 else ""}.'}
    if item == 'lantern':
        return {'success': True, 'text': 'Lit the lantern: a small warm pool of light. He keeps it with him after dark.'}
    return {'success': True, 'text': f'Handled the {item.replace("_", " ")} ({" ".join(str(how).split())[:80] or "idly"}). Nothing in particular happened.'}
