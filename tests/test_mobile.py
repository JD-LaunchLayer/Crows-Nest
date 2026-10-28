"""LAN authentication defaults and asset serving, without a live AI model."""
import importlib.util
import json
import pathlib
import shutil
import tempfile
import threading
import urllib.error
import urllib.request

root = pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
    folder=pathlib.Path(td)
    for name in ['crow.py','index.html','world.js','mobile_controls.js']:
        shutil.copy(root/name,folder/name)
    spec=importlib.util.spec_from_file_location('crow_mobile',folder/'crow.py')
    app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base='http://127.0.0.1:'+str(server.server_port)
    def get(path,headers=None):
        req=urllib.request.Request(base+path,headers=headers or {})
        with urllib.request.urlopen(req) as response:return response.read()
    assert json.loads(get('/api/state'))['paused']
    app.ACCESS_TOKEN='test-token-for-tests-only'
    for path in ['/api/state','/api/state?token=test-token-for-tests-only']:
        try:get(path);raise AssertionError('Private state was exposed')
        except urllib.error.HTTPError as error:assert error.code==401
    assert b'installTouchControls' in get('/mobile_controls.js')
    assert b'touchPad' in get('/')
    assert json.loads(get('/api/state',{'Authorization':'Bearer '+app.ACCESS_TOKEN}))['paused']
    for headers,expected in [({'X-Crow':'local'},401),({'X-Crow':'local','Authorization':'Bearer '+app.ACCESS_TOKEN},200)]:
        req=urllib.request.Request(base+'/api/toggle',method='POST',headers=headers)
        try:
            with urllib.request.urlopen(req) as response:assert response.status==expected;response.read()
        except urllib.error.HTTPError as error:assert error.code==expected
    assert not app.state['paused']
    server.shutdown()
print('PASS: local default, protected LAN state/control, static mobile assets and valid-token access.')
