"""v0.34.0 (mapping phase 1b): one world layout for his world and the 3D view; a real position for him; a safe move.

Also the first checks of "everything described is real": every ecology fact names a real thing inside the area it is
reported for, bushy outlines in the dark only where something bushy grows, and "not here" answers carry no
coordinates and no suggestion.
"""
import contextlib, copy, importlib.util, io, json, math, re, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'tests'))
import layout, actions, world_state, inner, ecology, life, town, lived_fixture

# ---- the file: checked, and the only source of places ----
data = json.loads((ROOT / 'data' / 'world_layout.json').read_text())
layout.validate(data)
for bad in ({**data, 'version': 2}, {k: v for k, v in data.items() if k != 'lanes'},
            {**data, 'items': data['items'] + [data['items'][0]]},
            {**data, 'items': [{**i, 'blocks': 'sometimes'} for i in data['items']]}):
    try:
        layout.validate(copy.deepcopy(bad)); raise SystemExit('a malformed layout was accepted')
    except ValueError:
        pass
assert set(actions.places().values()) <= set(layout.get()['places']), 'every place he can be has a spot'
for place in layout.get()['places']:
    assert layout.region_of(*layout.stand(place)) == place, place
assert world_state.PLACE_SPOTS == layout.place_spots()
assert set(world_state.STATIC_SOLIDS) == set(layout.solids())
assert inner.LANDMARKS == layout.landmarks() and ecology.AREAS == layout.regions()
src = (ROOT / 'world.js').read_text() + (ROOT / 'village.js').read_text()
assert "fetch('/world_layout.json')" in src and 'LAYOUT.pebbles' in src and 'LAYOUT.items' in src
assert 'export const VILLAGE' not in src and 'i*2.39996' not in src, 'no copies of the layout or the tree formula left on screen'
spring = next(i for i in layout.get()['items'] if i['kind'] == 'water')
s = {'materials': 0., 'stone': 0., 'creations': []}; world_state.ensure(s); life.ensure(s)
sp = s['built_world']['objects']['spring']
assert math.hypot(spring['x'] - sp['x'], spring['z'] - sp['z']) <= spring['r'] + .5, 'the pool is where the spring is'

# ---- his position: from where he already is; follows his place; stays put while he stays ----
s = {'location': 'shop', 'clock': {'iso': '2026-12-20T12:00:00+00:00'}}
pos = layout.ensure_position(s); assert (pos['x'], pos['z']) == layout.stand('shop') and s['spatial_version'] == 1
again = copy.deepcopy(s); layout.ensure_position(again); assert again == s, 'a second run changes nothing'
s['position'].update(x=-2.2, z=-14.6); layout.follow(s); assert s['position']['x'] == -2.2, 'he stays where he is at the same place'
s['location'] = 'library'; layout.follow(s); assert (s['position']['x'], s['position']['z']) == layout.stand('library')

# ---- moving a lived save: a backup first, nothing else touched, twice is the same as once ----
with tempfile.TemporaryDirectory() as td:
    folder = Path(td); shutil.copy(ROOT / 'crow.py', folder / 'crow.py')
    spec = importlib.util.spec_from_file_location('crow_lay0', folder / 'crow.py'); app = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE = lambda: datetime(2026, 12, 20, 9, 0, tzinfo=app.TZ); app.clock()
    lived_fixture.populate(app.state); app.state['location'] = 'cafe'
    app.state.pop('position', None); app.state.pop('spatial_version', None)
    old = json.loads(json.dumps(app.state, default=str))
    (folder / 'crow-save.json').write_text(json.dumps(old))
    loaded = []
    for n in range(2):
        spec = importlib.util.spec_from_file_location(f'crow_lay{n + 1}', folder / 'crow.py'); app = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(app)
        loaded.append(json.loads(json.dumps(app.state, default=str)))
        (folder / 'crow-save.json').write_text(json.dumps(app.state, default=str))
    bak = folder / 'crow-save-before-v0.34.json'
    assert bak.exists() and 'position' not in json.loads(bak.read_text())
    st = loaded[0]
    assert (st['position']['x'], st['position']['z']) == layout.stand('cafe') and st['spatial_version'] == 1
    for key in ('memories', 'notebook', 'possessions', 'creations', 'trading'):
        assert st.get(key) == old.get(key), key
    assert st['built_world']['trees'] == old['built_world']['trees'], 'tree ids and places untouched'
    assert loaded[1]['position'] == loaded[0]['position']

# ---- everything described is real ----
s = {'materials': 0., 'stone': 0., 'creations': []}
world_state.ensure(s); life.ensure(s); town.ensure(s); ecology.ensure(s)
import resources; resources.ensure(s)
trees, plants = s['built_world']['trees'], {p['id']: p for p in s['ecology']['plants']}
for area in ecology.AREAS:
    for doy in (20, 120, 200, 300):
        for about, text, _ in ecology.visible_facts(s, area, doy, .9):
            thing = trees.get(about) or plants.get(about) or s['built_world'].get('resources', {}).get(about)
            if str(about).startswith(('bird-', 'deer-')):
                continue
            assert thing, f'{area}: a fact about nothing real: {text}'
            assert ecology.in_area(area, thing['x'], thing['z']), f'{text} is reported in {area} but is not there'
bushy = lambda area: any(ecology.in_area(area, p['x'], p['z']) and p.get('host') is None
                         and ecology.PLANT_KIND.get(p['species'], '').split()[:1] in (['shrub'], ['fern']) for p in plants.values())
for area in ecology.AREAS:
    r = ecology.observe(s, area, '', 200, 0., lamp=False)
    assert ('bushy' in r['text']) == bushy(area), f'{area}: bushy outlines must match what grows there'
r = ecology.observe(s, 'woodland_edge', 'the shrub near tree-205', 330, .9)
assert r.get('edge', {}).get('kind') == 'not_here', r.get('edge')
assert not re.search(r'\(-?\d+(\.\d+)?,\s*-?\d+', r['text']), 'no coordinates in what he is told'
assert not re.search(r'\b(try|you could|you should|instead|go to)\b', r['text'].lower()), 'no suggestion where to look'
print('PASS v0.34.0: one world layout for his world and the 3D view; a real position from where he is; a safe, repeatable move; facts name real things where they are.')
