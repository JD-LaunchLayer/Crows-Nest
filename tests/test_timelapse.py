"""Time-lapse twin: a copy on a virtual clock that never touches the real Crow."""
import contextlib, hashlib, io, json, sys, tempfile, time
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
import timelapse

cycle=['eat','drink','observe','rest','sleep','inspect','explore']
calls={'n':0,'choices':0}
def model(prompt,schema,limit=650,*purpose):
    calls['n']+=1
    if 'action' in schema['properties']:calls['choices']+=1
    def fill(name,s):
        if name=='action':return cycle[calls['choices']%len(cycle)] if cycle[calls['choices']%len(cycle)] in s['enum'] else s['enum'][0]
        if 'enum' in s:return s['enum'][0]
        t=s.get('type')
        return {'string':'A brief note.','boolean':False,'integer':1,'number':.3,'array':[]}.get(t,{})
    return {k:fill(k,v) for k,v in schema['properties'].items()},.01

with tempfile.TemporaryDirectory() as td:
    real=Path(td)/'real';real.mkdir();twin=Path(td)/'twin'
    (real/'crow-save.json').write_text(json.dumps({'materials':2,'memories':[],'creations':[]}))
    (real/'crow-events.jsonl').write_text('')
    digest=lambda: {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in real.iterdir()}
    before=digest()
    try:timelapse.run(real,real/'crow-save.json',1);raise AssertionError('must refuse the real folder')
    except SystemExit:pass
    t0=time.monotonic()
    with contextlib.redirect_stdout(io.StringIO()):app=timelapse.run(twin,real/'crow-save.json',2,model=model)
    assert time.monotonic()-t0<60, 'virtual time must not wait in real time'
    assert digest()==before, 'the real save and log are only read'
    st=json.loads((twin/'crow-save.json').read_text());meta=st['twin']
    start=datetime.fromisoformat(meta['started_virtual']);reached=datetime.fromisoformat(meta['virtual_now'])
    assert (reached-start).total_seconds()>=2*86400
    events=[json.loads(l) for l in (twin/'crow-events.jsonl').read_text().splitlines()]
    assert events and max(datetime.fromisoformat(e['at']) for e in events)>start
    assert any(e.get('action')=='sleep' for e in events) and any(e.get('action')=='observe' and e.get('kind')=='experience' for e in events)
    assert st['body']['active_hours']>40, 'the body lives through the simulated time'
    # Resumable: the next run continues from where the twin's clock stopped.
    with contextlib.redirect_stdout(io.StringIO()):timelapse.run(twin,real/'crow-save.json',3,model=model)
    again=json.loads((twin/'crow-save.json').read_text())['twin']
    assert again['started_virtual']==meta['started_virtual'] and datetime.fromisoformat(again['virtual_now'])>=start.replace()+(reached-start)
    assert digest()==before

    # An Ollama/network outage is waited out in real time; the twin neither ages nor records it as his failure.
    import urllib.error
    down={'n':3}
    def flaky(*a,**k):
        if down['n']>0:down['n']-=1;raise urllib.error.URLError('Connection refused')  # model server down
        return model(*a,**k)
    real_sleep=timelapse.time.sleep;timelapse.time.sleep=lambda s:None
    before_outage=json.loads((twin/'crow-save.json').read_text())['twin']
    with contextlib.redirect_stdout(io.StringIO()):timelapse.run(twin,real/'crow-save.json',3.2,model=flaky)
    timelapse.time.sleep=real_sleep
    after=json.loads((twin/'crow-save.json').read_text())['twin']
    assert down['n']==0 and len(after['errors'])==len(before_outage['errors'])
print('PASS: outage waited out without ageing; separate twin copy; refuses the real folder; virtual clock without real waiting; real life untouched; '
      'body, sleep and observation continue through simulated days; resumable.')
