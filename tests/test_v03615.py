"""v0.36.15: slow changes survive short ticks; he can walk to a place he knows; a failed carry does not move him,
and what he can carry is what is near him or already in his hands."""
import copy
import contextlib
import importlib.util
import io
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import garden, world_state, life, resources, layout, materials

STEP = 12 / 3600  # one tick at time scale 24


def sown(item='radish_seeds'):
    s = {'materials': 0, 'stone': 0, 'creations': [], 'possessions': {item: 1}}
    world_state.ensure(s)
    life.ensure(s)
    garden.ensure(s)
    assert garden.work(s, 1, 'sow', item)['success']
    b = s['garden']['beds'][0]
    b.update(moisture=1., weeds=0., health=1., growth=0.)
    s['garden']['_sec'] = 0.
    return s


def tiny(s, hours, doy, tend=False):
    n = int(round(hours / STEP))
    for _ in range(n):
        if tend:
            b = s['garden']['beds'][0]
            b['moisture'] = 1.
            b['weeds'] = 0.
        garden.advance(s, STEP, doy)


def big(s, hours, doy):
    garden.advance(s, hours, doy)


# Many 12-second steps match one stretch of the same length.
a, b = sown(), sown()
tiny(a, 48, 20)
big(b, 48, 20)
for key in ('moisture', 'weeds', 'growth', 'health'):
    assert abs(a['garden']['beds'][0][key] - b['garden']['beds'][0][key]) < 1e-6, (key, a['garden']['beds'][0], b['garden']['beds'][0])
assert a['garden']['beds'][0]['moisture'] < 1, 'moisture falls'
assert a['garden']['beds'][0]['weeds'] > 0, 'weeds rise'
assert a['garden']['beds'][0]['health'] < .6, 'two midwinter days of frost hurt a tender crop'
# Summer radish, kept moist, ripens in about 28 days even when time arrives in 12-second ticks.
summer = sown()
tiny(summer, 26 * 24, 200, tend=True)
assert garden.stage(summer['garden']['beds'][0]) != 'ripe'
tiny(summer, 3 * 24, 200, tend=True)
assert garden.stage(summer['garden']['beds'][0]) == 'ripe', summer['garden']['beds'][0]
# Four midwinter days wither it.
winter = sown()
tiny(winter, 4 * 24, 20)
assert winter['garden']['beds'][0]['crop'] == 'withered', winter['garden']['beds'][0]

# Trees: a young hazel grows the same amount in short steps as in one stretch.
def young():
    s = {'materials': 0, 'stone': 0, 'creations': []}
    world_state.ensure(s)
    s['built_world']['trees'] = {'p1': {'id': 'p1', 'x': 20, 'z': 20, 'height': .6, 'stage': 'young',
                                        'timber_kg': 0, 'stock': 0, 'species': 'hazel'}}
    return s
ta, tb = young(), young()
n = int(round(48 / STEP))
for _ in range(n):
    world_state.grow_trees(ta, STEP, garden.warmth(200))
world_state.grow_trees(tb, 48, garden.warmth(200))
assert abs(ta['built_world']['trees']['p1']['height'] - tb['built_world']['trees']['p1']['height']) < 1e-9
assert ta['built_world']['trees']['p1']['height'] > .6

# Regrowth likewise.
def patch():
    s = {'materials': 0, 'stone': 0, 'creations': [], 'clock': {'iso': '2026-07-15T12:00:00+00:00'}}
    world_state.ensure(s)
    resources.ensure(s)
    node = next(n for n in s['built_world']['resources'].values() if n.get('kind') == 'clay_bed')
    node['stock'] = node['capacity'] * .5
    return s, node['id']
ra, ia = patch()
rb, ib = patch()
started = ra['built_world']['resources'][ia]['stock']
for _ in range(n):
    resources.advance(ra, STEP)
resources.advance(rb, 48)
assert abs(ra['built_world']['resources'][ia]['stock'] - rb['built_world']['resources'][ib]['stock']) < 1e-6
assert ra['built_world']['resources'][ia]['stock'] > started
print('PASS v0.36.15: twelve-second steps grow the garden, the trees and the ground the same as one long step.')


def colder(st):
    import senses
    return senses.felt_temp({**st, 'location': 'woods'}, 'walk') < senses.felt_temp({**st, 'location': 'shop'}, 'walk')


with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT / 'crow.py', Path(td) / 'crow.py')
    spec = importlib.util.spec_from_file_location('crow_v03615', Path(td) / 'crow.py')
    app = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(app)
    st = app.state
    st['paused'] = False
    st['location'] = 'shop'
    st['mind_map'] = {'version': 1, 'landmarks': {}, 'changes': [],
                      'places': {'cabin': {'visits': 3}, 'shop': {'visits': 5}}}
    home = None
    day = None

    def at(hour):
        app.CLOCK_OVERRIDE = lambda hour=hour: datetime(2027, 1, 23, hour, 0, tzinfo=app.TZ)
        app.clock()
        st.pop('walking', None)
        st['location'] = 'shop'
        layout.follow(st)

    at(12)
    home = next(name for name, (key, _x, _z) in layout.destinations(st).items() if key == 'cabin')
    assert 'shop' not in home and '(' not in home
    day = {**app.DECISION_DEFAULTS, 'action': 'walk', 'walk_to': home, 'intention': 'Walk home', 'reason': 'r'}
    app.start_action(dict(day), 1)
    by_day = st['pending']['duration']
    assert st['location'] == 'woods' and st.get('walking')
    st['pending'] = None
    at(22)
    app.start_action(dict(day), 1)
    assert st['pending']['duration'] > by_day, 'the dark path is slower'
    assert colder(st)
    app.tick(st['pending']['duration'] + 5)
    ev = app.finish_action()['event']
    assert ev.startswith('Walked to') and st['location'] == 'cabin', (ev, st['location'])
    # A carry of nothing, at the post, leaves him at the post.
    st['location'] = 'shop'
    layout.follow(st)
    d = {**app.DECISION_DEFAULTS, 'action': 'move_object', 'object_id': 'none', 'destination_x': 1, 'destination_z': 1,
         'intention': 'Walk home by the dark path now, carefully', 'reason': 'r'}
    app.start_action(d, 1)
    assert st['location'] == 'shop'
    app.tick(120)
    ev = app.finish_action()['event']
    assert ev.startswith('Nothing was carried') and st['location'] == 'shop', (ev, st['location'])
    # A boulder beside him is refused by weight. Wood he has put by can be carried. Selling rates stay as they are.
    import town
    sx, sz = layout.stand('shop')
    st['built_world']['objects']['boulder'] = {
        'id': 'boulder', 'name': 'Great boulder', 'kind': 'rock', 'portable': False, 'x': sx, 'z': sz, 'revision': 0,
        'parts': [world_state.part('body', 0, .5, 0, 2, 1, 2)]}
    assert world_state.object_kg(st['built_world']['objects']['boulder']) > 20
    boulder = {**app.DECISION_DEFAULTS, 'action': 'move_object', 'object_id': 'boulder', 'destination_x': 1,
               'destination_z': 1, 'intention': 'shift the boulder', 'reason': 'r'}
    app.start_action(boulder, 1)
    assert st['location'] == 'shop'
    app.tick(400)
    ev = app.finish_action()['event']
    assert 'too heavy to lift alone' in ev and st['built_world']['objects']['boulder']['x'] == sx and st['location'] == 'shop', ev
    rates = copy.deepcopy(town.SELL_RATES)
    st['materials'] = 5
    materials.ensure(st)
    req = app.parameter_request({'action': 'move_object'})
    lot = next(h for h in req[1]['object_id']['enum'] if str(h).startswith('lot:'))
    assert any('wood' in row['what'] for row in req[2]['near_me']), req[2]
    ok = {**app.DECISION_DEFAULTS, 'action': 'move_object', 'object_id': lot, 'carry_kg': 4,
          'destination_x': 1, 'destination_z': 1, 'intention': 'carry the loose wood', 'reason': 'r'}
    app.start_action(ok, 1)
    assert st['location'] == 'shop'
    app.tick(400)
    ev = app.finish_action()['event']
    assert ev.startswith('Carried 4') and abs(st['materials'] - 1) < 1e-6 and st['location'] == 'shop', (ev, st['materials'])
    assert town.SELL_RATES == rates
print('PASS v0.36.15: he can walk home in the dark, and a failed or heavy carry leaves him where he was.')
