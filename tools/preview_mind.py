#!/usr/bin/env python3
"""Show what Crow sees of his own life right now, exactly as his mind is shown it (v0.30). No model call, no cost.

    python3 tools/preview_mind.py              # reads a COPY of crow-save.json; never writes to it

Prints the moment as he knows it: the first-person view he decides from. Use it to check how he is
spoken to before letting him live with it. Nothing here changes his life.
"""
import contextlib, importlib.util, io, shutil, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
with tempfile.TemporaryDirectory() as td:
    for name in ['crow.py', 'crow-save.json', 'crow-config.json']:
        if (ROOT / name).exists():
            shutil.copy(ROOT / name, Path(td) / name)
    spec = importlib.util.spec_from_file_location('crow_preview', Path(td) / 'crow.py')
    app = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(app)
    seen = []
    app.model_call = lambda prompt, schema, *a, **k: (seen.append(prompt) or ({'action': 'rest', 'intention': '', 'reason': '', 'next_step': '',
                                                                                 'wish': '', 'wish_reason': '', 'project': 'none', 'which_project': ''}, 0))
    app.choose_action()
    print('WHO HE IS\n' + app.BASELINE + '\n\nWHAT HE SEES NOW\n' + seen[0])
