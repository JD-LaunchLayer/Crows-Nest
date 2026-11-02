"""v0.24.2: his field notebook lists only what he has recorded, by place and kind, and is rebuilt from his own memories."""
import contextlib, importlib.util, io, json, shutil, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import ecology
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_nb',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    st=app.state;eco=ecology.ensure(st)
    assert ecology.notebook(st)=={} , 'nothing recorded, nothing listed'
    br=[p for p in eco['plants'] if p['species']=='bramble']
    ecology.observe(st,'woodland_edge',f"the bramble at ({br[0]['x']:.0f}, {br[0]['z']:.0f})",314,1.)
    book=ecology.notebook(st);edge=book['the woodland edge around the clearing']
    assert any(l.startswith('shrubs: bramble') for l in edge) and sum(1 for p in br if f"({p['x']:.0f}, {p['z']:.0f})" in json.dumps(edge))==1
    assert 'deeper' not in json.dumps(book), 'never lists places or things he has not recorded'
    # Rebuilt once from remembered events for an existing life.
    st2={'built_world':st['built_world'],'ecology':{k:v for k,v in eco.items() if k not in ('recorded','recorded_backfilled')},
         'memories':[{'kind':'experience','event':f"Observed it. A bramble thicket at ({br[1]['x']:.0f}, {br[1]['z']:.0f}) with arching thorny stems. tree-3 is an oak."}]}
    ecology.backfill_recorded(st2);assert br[1]['id'] in st2['ecology']['recorded'] and 'tree-3' in st2['ecology']['recorded']
    assert 'your_field_notebook' in app.decision_context()
    # v0.24.3: reworded wishes and repeated open questions are shown once, with how often; stored records unchanged.
    texts=['Find one edge shrub detail I have not recorded before.','Get a clear daylight look at a new edge shrub.','Find one shrub at the edge that nobody has logged yet.','Learn to carve a bowl that holds water']
    app.state['wishes']=[{'id':i,'text':t,'mentions':2,'status':'expressed'} for i,t in enumerate(texts)]
    g=app.grouped_wishes(8);assert len(g)==2 and g[1]['times_expressed']==6 and len(app.state['wishes'])==4
print('PASS v0.24.2: field notebook of his own records only, by place and kind; rebuilt from his memories.')
