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
    return post


def board(state):
    """What the posted board at the trading post shows."""
    post = ensure(state)
    return {'your_credit': post['credit'],
            'for_sale': {k: {'name': v['name'], 'price': v['price'], 'left': v['qty']} for k, v in post['stock'].items() if v['qty'] > 0},
            'we_buy': {'wood': '1 credit per 3 kg', 'stone': '1 credit per 5 kg',
                       'carving': '1–3 credit for a carving you made, by how well it turned out'},
            'jobs': {k: {'name': v['name'], 'minutes': v['minutes'], 'pays': v['credit']} for k, v in JOBS.items()}}


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
