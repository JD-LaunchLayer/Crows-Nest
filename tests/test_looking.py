"""v0.23.1: names in a 'not …' list are avoided; places by coordinates; looking for the unrecorded; plant close-ups; markup leaks; reworded wishes."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import ecology
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_looking',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    st=app.state;eco=ecology.ensure(st)
    edge=[t for t in st['built_world']['trees'].values() if ecology.in_area('woodland_edge',t['x'],t['z']) and t['stage']=='standing']
    t=edge[0]['id']
    r=ecology.observe(st,'woodland_edge',f'an unrecorded plant at the edge, not a hornbeam, hazel, or {t}',312,1.)
    assert not any(f['about']==t for f in r['findings']), 'a name in a "not ..." list is not the target'
    assert ecology._negated('look closely at tree-3', len('look closely at ')) is False
    # A plant named by its place: its close detail, nothing else.
    br=next(p for p in eco['plants'] if p['species']=='bramble')
    r=ecology.observe(st,'woodland_edge',f"the bramble at ({br['x']:.0f}, {br['z']:.0f}): leaf edges and stem colour",312,1.)
    assert all(f['about']==br['id'] for f in r['findings']) and 'hooked prickles' in r['text'], r['text']
    assert 'Up close' in ecology.inspect(st,br['id'],312,1.)['text']
    # Looking for what he has not recorded: unseen things first, then a plain statement when there are none.
    eco['seen'].clear()
    seen_texts=set()
    for i in range(40):
        r=ecology.observe(st,'grove','something I have not recorded',312,1.)
        if r['edge']:break
        assert any(f['new'] for f in r['findings'])
    assert r['edge']['kind']=='seen_all' and 'has been seen before' in r['text'], r
    # Leaked tool markup is cut from text answers.
    assert app.conform('Bramble leaves unexamined.</left_open> <parameter name="x">3',{'type':'string'})=='Bramble leaves unexamined.'
    # The same wish in new words is one wish mentioned twice.
    base={**app.DECISION_DEFAULTS,'action':'rest','reason':'r','intention':'i'}
    n=len(st['wishes'])
    app.start_action({**base,'wish':'Find one plant at the edge I have not recorded before.','wish_reason':'x'},1)
    app.state['pending']=None
    app.start_action({**base,'wish':'Find a plant at the edge I have not yet recorded.','wish_reason':'x'},1)
    assert len(st['wishes'])==n+1 and st['wishes'][-1]['mentions']==2
    # v0.23.2: looking for an unrecorded kind of thing ("a shrub, not a tree, fern or bramble") finds that kind,
    # never what he steered away from, and says plainly when every one of that kind has been seen.
    eco['seen'].clear()
    f='an unrecorded shrub at the woodland edge, not a tree, fern, bramble, or the spring'
    first=ecology.observe(st,'woodland_edge',f,314,1.)
    assert 'bramble' not in first['findings'][0]['text'].lower() and not first['findings'][0]['about'].startswith('tree-'), first['findings'][0]
    for i in range(6):
        r=ecology.observe(st,'woodland_edge',f,314,1.)
        if r['edge']:break
    assert r['edge']['kind']=='seen_all' and 'Every shrub' in r['text'], r['text']
    assert 'Every shrub' in r['text'][:200], 'v0.23.3: the edge statement comes first, never cut off'
    st['memories'].append({'id':99999,'kind':'experience','time':'14:35','at':'2026-11-10T14:35','action':'observe','event':r['text']+' '+'x'*300})
    ev=app.decision_context()['recent_events'][-1]['event'];assert 'Every shrub' in ev and len(ev)>180
    assert ecology.observe(st,'grove','an unrecorded fungus',314,1.)['edge']['kind']=='not_found'
print('PASS v0.23.1: "not" lists respected; places by coordinates; unrecorded-first looking with an honest end; plant close-ups; markup stripped; reworded wishes merged; kinds he seeks and avoids respected.')
