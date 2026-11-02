"""v0.21.3: a focus naming one tree brings that tree's details first instead of matching every tree."""
import sys, tempfile, json, shutil, importlib.util, contextlib, io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_focus',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    import ecology
    st=app.state
    for area in ecology.AREAS:
        trees=[t for t in st['built_world']['trees'].values() if t['stage']=='standing' and ecology.in_area(area,t['x'],t['z'])]
        if len(trees)>=4:break
    target=trees[-1]['id']
    for i in range(6):
        r=ecology.observe(st,area,f'look closely at {target}',300,1.)
        assert r['findings'][0]['about']==target or target in r['findings'][0]['text'], (target,r['findings'])
print('PASS v0.21.3: naming a tree in the focus brings that tree first, every time.')
