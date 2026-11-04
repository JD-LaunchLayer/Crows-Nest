"""v0.31.1: the materials data is checked at start; the item ledger begins from what he has, keeps the old wood and
stone totals in step, conserves mass, survives being run twice, and reading it changes nothing."""
import contextlib, copy, importlib.util, io, json, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import materials, lived_fixture
# ---- the data: complete, unique, in range; anything malformed is refused ----
good=json.loads((ROOT/'data'/'materials.json').read_text())
mats=materials.validate(good)
assert {'oak','ash','hazel','birch','hornbeam','holly','stone','flint','clay','iron_ore','copper_ore','tin_ore','flax','wool','hide'}<=set(mats)
assert mats['oak']['bending']>mats['mixed_wood']['bending'] and mats['flint']['hardness']>mats['stone']['hardness']
assert mats['wool']['conductivity']<mats['hide']['conductivity'] and mats['tin_ore']['density']>mats['iron_ore']['density']
for bad in ({'materials':[]}, {'materials':good['materials']+[good['materials'][0]]},
            {'materials':[{**m,'density':-1} if m['id']=='oak' else m for m in good['materials']]},
            {'materials':[{k:v for k,v in m.items() if k!='texture'} for m in good['materials']]},
            {'materials':[m for m in good['materials'] if m['id']!='mixed_wood']}):
    try:materials.validate(bad);raise SystemExit('malformed data was accepted')
    except ValueError:pass
with tempfile.TemporaryDirectory() as td:
    (Path(td)/'materials.json').write_text('{"materials": [ broken')
    try:materials.load(td);raise SystemExit('broken json was accepted')
    except ValueError:pass
# ---- on a lived life ----
with tempfile.TemporaryDirectory() as td:
    folder=Path(td);shutil.copy(ROOT/'crow.py',folder/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_mat',folder/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,19,9,0,tzinfo=app.TZ);app.clock()
    st=app.state;lived_fixture.populate(st);st['materials']=45.7;st['stone']=3.
    st.pop('stock',None);st.pop('crafting_version',None)
    materials.ensure(st);first=copy.deepcopy(st['stock'])
    assert materials.totals(st)=={'mixed_wood':45.7,'stone':3.0} and st['crafting_version']==1
    materials.ensure(st);materials.ensure(st);assert st['stock']==first, 'running it again changes nothing'
    # Reading changes nothing.
    before=json.dumps(st,sort_keys=True,default=str);materials.view(st);materials.totals(st)
    assert json.dumps(st,sort_keys=True,default=str)==before
    # Old code that changes a total directly is reconciled: grown as a plain lot, shrunk from the oldest.
    st['materials']=round(st['materials']+3,2);materials.reconcile(st);assert materials.totals(st)['mixed_wood']==48.7
    oak=materials.add(st,'oak',5.,form='log',source='felled');assert st['materials']==53.7
    st['materials']=round(st['materials']-46,2);materials.reconcile(st)
    t=materials.totals(st);assert t['oak']==5. and abs(t['mixed_wood']-2.7)<1e-6, t
    # Taking keeps the total in step, oldest first, and never takes more than is there.
    got=materials.take(st,'oak',7.);assert got==[('oak',5.)] and abs(st['materials']-2.7)<1e-6
    # Mass is conserved across a run of changes.
    total=lambda:round(sum(l['mass_kg'] for l in st['stock']['lots']),3)
    start=total();materials.add(st,'flint',2.);materials.take(st,'flint',.5);materials.add(st,'stone',1.)
    assert abs(total()-(start+2.5))<1e-6 and st['stone']==4. and materials.totals(st)['flint']==1.5, 'flint lives in the ledger only'
    # A new life starts with an empty ledger; the world loads its data on start.
with tempfile.TemporaryDirectory() as td:
    folder=Path(td);shutil.copy(ROOT/'crow.py',folder/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_new',folder/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    assert app.state['stock']['lots']==[] and app.state['crafting_version']==1 and 'oak' in materials.all_materials()
# The backup before the ledger first runs is written once, and only for an existing save without one.
with tempfile.TemporaryDirectory() as td:
    folder=Path(td);shutil.copy(ROOT/'crow.py',folder/'crow.py')
    (folder/'crow-save.json').write_text(json.dumps({'materials':12.5,'stone':2.0,'paused':True}))
    spec=importlib.util.spec_from_file_location('crow_bak',folder/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    bak=folder/'crow-save-before-v0.31.json';assert bak.exists() and json.loads(bak.read_text())['materials']==12.5
    assert materials.totals(app.state)=={'mixed_wood':12.5,'stone':2.0}
print('PASS v0.31.1: materials data checked; the item ledger begins from what he has, keeps his totals, conserves mass, runs twice safely, reads without change.')
