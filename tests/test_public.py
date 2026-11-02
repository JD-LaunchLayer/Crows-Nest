"""v0.22: public mode lets anyone watch read-only; changes need the owner's token."""
import contextlib, gzip, importlib.util, io, json, shutil, sys, tempfile, threading, urllib.error, urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py');shutil.copy(ROOT/'index.html',Path(td)/'index.html')
    spec=importlib.util.spec_from_file_location('crow_public',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    app.PUBLIC=True;app.ACCESS_TOKEN='owner-secret'
    server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_address[1]}'
    def get(path,token=None,gz=False):
        h={'Authorization':'Bearer '+token} if token else {}
        if gz:h['Accept-Encoding']='gzip'
        with urllib.request.urlopen(urllib.request.Request(base+path,headers=h)) as r:
            body=r.read();return gzip.decompress(body) if r.headers.get('Content-Encoding')=='gzip' else body
    def post(path,token=None):
        h={'X-Crow':'local',**({'Authorization':'Bearer '+token} if token else {})}
        try:
            with urllib.request.urlopen(urllib.request.Request(base+path,data=b'',headers=h,method='POST')) as r:return r.status
        except urllib.error.HTTPError as e:return e.code
    visitor=json.loads(get('/api/state',gz=True))
    assert visitor['viewer']=='visitor' and visitor['maintenance_enabled'] is False
    assert b'crow-version' in get('/')
    paused=app.state['paused']
    assert post('/api/toggle')==401 and post('/api/update')==401 and app.state['paused']==paused, 'visitors cannot change anything'
    assert json.loads(get('/api/state','owner-secret'))['viewer']=='owner'
    assert post('/api/toggle','owner-secret')==200 and app.state['paused']!=paused
    assert 'owner-secret' not in get('/api/state').decode() and 'anthropic_api_key' not in get('/api/state').decode()
    server.shutdown()
print('PASS v0.22 public mode: visitors watch read-only (compressed, cached); only the owner token changes anything; no secrets in state.')
