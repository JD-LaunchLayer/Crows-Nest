"""Real temporary Git remotes plus authenticated endpoint and restart contract."""
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request

root=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import maintenance

def git(cwd,*args):
    return subprocess.check_output(['git','-c','user.name=Test','-c','user.email=test@example.invalid',*args],cwd=cwd,text=True,stderr=subprocess.DEVNULL).strip()

with tempfile.TemporaryDirectory() as td:
    base=pathlib.Path(td);remote=base/'remote.git';author=base/'author';checkout=base/'running'
    remote.mkdir();git(remote,'init','--bare','--initial-branch=main')
    git(base,'clone',str(remote),str(author))
    (author/'.gitignore').write_text('crow-save*.json\ncrow-events.jsonl\ncrow-reading/\ncrow-config.json\nbackups/\ncrow-update-status.json\n')
    (author/'crow.py').write_text('# first version\n');git(author,'add','.');git(author,'commit','-m','Initial');git(author,'push','origin','main')
    git(base,'clone',str(remote),str(checkout))
    life={'day':8,'memories':[{'event':'I made something.'}],'pending':{'remaining':123}}
    (checkout/'crow-save.json').write_text(json.dumps(life));(checkout/'crow-events.jsonl').write_text('history\n')
    (checkout/'crow-reading').mkdir();(checkout/'crow-reading'/'article-1.json').write_text('{"title":"Test"}')
    (checkout/'crow-config.json').write_text('{"activity_minutes":{"read":20}}')
    (author/'crow.py').write_text('# second version\n');git(author,'add','crow.py');git(author,'commit','-m','Second');git(author,'push','origin','main')
    statuses=[]
    result=maintenance.update_checkout(checkout,lambda **x:statuses.append(x),{str(remote)})
    assert result['changed'] and git(checkout,'rev-parse','HEAD')==git(author,'rev-parse','HEAD')
    backup=checkout/result['backup'];assert json.loads((backup/'crow-save.json').read_text())==life
    assert (backup/'crow-reading'/'article-1.json').exists() and (backup/'crow-config.json').exists()
    assert json.loads((checkout/'crow-save.json').read_text())==life
    assert [x['status'] for x in statuses]==['checking','backing_up','pulling']
    assert not maintenance.update_checkout(checkout,lambda **x:None,{str(remote)})['changed']
    (checkout/'crow.py').write_text('# local edits\n')
    try:maintenance.update_checkout(checkout,lambda **x:None,{str(remote)});raise AssertionError('Dirty source overwritten')
    except RuntimeError as e:assert 'local edits' in str(e)
    assert (checkout/'crow.py').read_text()=='# local edits\n'
    git(checkout,'checkout','--','crow.py')
    try:maintenance.update_checkout(checkout,lambda **x:None);raise AssertionError('Unexpected origin accepted')
    except RuntimeError as e:assert 'Origin' in str(e)
    git(checkout,'checkout','-b','work')
    try:maintenance.update_checkout(checkout,lambda **x:None,{str(remote)});raise AssertionError('Non-main branch accepted')
    except RuntimeError as e:assert 'main branch' in str(e)
    git(checkout,'checkout','main')
    (checkout/'local.txt').write_text('Keep this local commit.');git(checkout,'add','local.txt');git(checkout,'commit','-m','Local work')
    local_head=git(checkout,'rev-parse','HEAD')
    (author/'upstream.txt').write_text('Upstream work.');git(author,'add','upstream.txt');git(author,'commit','-m','Upstream work');git(author,'push','origin','main')
    try:maintenance.update_checkout(checkout,lambda **x:None,{str(remote)});raise AssertionError('Diverged history overwritten')
    except RuntimeError:pass
    assert git(checkout,'rev-parse','HEAD')==local_head and (checkout/'local.txt').exists()

with tempfile.TemporaryDirectory() as td:
    folder=pathlib.Path(td);shutil.copy(root/'crow.py',folder/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_maintenance',folder/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    app.state['paused']=False
    running=threading.Event();release=threading.Event()
    def fake_update(was_paused):
        assert was_paused is False;running.set();release.wait(5);app.UPDATE_LOCK.release()
    app.perform_update=fake_update
    server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    base='http://127.0.0.1:'+str(server.server_port)
    def post(path,headers):
        req=urllib.request.Request(base+path,method='POST',headers=headers)
        try:
            with urllib.request.urlopen(req) as r:r.read();return r.status
        except urllib.error.HTTPError as e:return e.code
    assert post('/api/update',{'X-Crow':'local'})==403
    app.ACCESS_TOKEN='test-owner-token'
    assert post('/api/update',{'X-Crow':'local'})==401
    headers={'X-Crow':'local','Authorization':'Bearer '+app.ACCESS_TOKEN}
    assert post('/api/update',headers)==202;assert running.wait(2);assert app.state['paused']
    assert post('/api/update',headers)==409 and post('/api/toggle',headers)==409
    assert json.loads((folder/'crow-save.json').read_text())['paused']
    release.set();server.shutdown()
    captured={}
    original=app.os.execve
    app.os.execve=lambda executable,args,env:captured.update(executable=executable,args=args,env=env)
    app.restart_updated_process(False)
    assert captured['env']['CROW_RESTART_TOKEN']==app.ACCESS_TOKEN
    assert captured['env']['CROW_UPDATE_RESUME']=='1'
    assert captured['args'][1]==str(folder/'crow.py')
    app.os.execve=original
print('PASS: backup before pull; real fast-forward update; unchanged life; dirty/origin/branch refusal; authenticated single-job endpoint; paused snapshot; same-token and resume restart contract.')
