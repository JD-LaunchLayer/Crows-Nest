"""The rule above all (v0.31.0): Crow is never told what to make, what he can make, or that he has learned anything.

Every string he can see is built through the real code paths and checked against a list of forbidden
phrases, and against the names of anything the world's data can produce. Extend FORBIDDEN and the
product list as content grows; never weaken them to make a new feature pass.
"""
import contextlib, importlib.util, io, json, re, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FORBIDDEN = [r'\bunlock', r'\byou (can|could) now\b', r'\bnow (you )?know\b', r'\blearn(ed|t) (how|to)\b', r'\brecipes?\b',
             r'\bblueprint list\b', r'\bcrafting\b', r'\btech tree\b', r'\bnew ability\b', r'\bdiscovered how\b',
             r'\btry (making|building|combining)\b', r'\byou should\b', r'\byou need to\b', r'\bthe way (out|forward)\b',
             r'\bhint\b', r'\btip:', r'\bnew skill\b', r'\byou have learned\b', r'\bunlocked\b', r'\blevel(led)? up\b']
# Legacy product-named actions (hunt, butcher, preserve) predate this rule and are allowed by name until
# they move to generic verbs. Nothing new may be named after what it makes.
LEGACY_ACTIONS = {'hunt', 'butcher', 'preserve'}


def products():
    """Every output id the world's data can produce. Empty until the materials data arrives; then it fills."""
    out = set()
    for f in (ROOT / 'data').glob('*.json') if (ROOT / 'data').exists() else []:
        data = json.loads(f.read_text())
        for proc in data.get('processes', []) if isinstance(data, dict) else []:
            out |= {o for o in proc.get('outputs', []) if isinstance(o, str)}
    return out


def check(where, text):
    low = str(text).lower()
    for pat in FORBIDDEN:
        assert not re.search(pat, low), f'{where}: forbidden phrase /{pat}/ in: {text[:300]}'
    for p in products():
        assert p.lower().replace('_', ' ') not in low, f'{where}: product name {p!r} shown to him'


with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT / 'crow.py', Path(td) / 'crow.py')
    spec = importlib.util.spec_from_file_location('crow_hints', Path(td) / 'crow.py')
    app = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(app)
    import inner, senses, actions
    for when in (datetime(2026, 12, 19, 3, 0, tzinfo=app.TZ), datetime(2026, 7, 10, 14, 0, tzinfo=app.TZ)):
        app.CLOCK_OVERRIDE = lambda when=when: when
        app.clock()
        st = app.state
        st['possessions'].update(hunting_bow=1, arrows=4, harp=1, stove=1, lantern=1)
        # What he sees each moment, and the list of what he could do.
        seen = []
        app.model_call = lambda p, s, *a, **k: (seen.append(p) or ({'action': 'rest', 'intention': 'i', 'reason': 'r', 'next_step': '', 'wish': '',
                                                                     'wish_reason': '', 'project': 'none', 'which_project': ''}, 0))
        app.choose_action()
        check('choose_action prompt', seen[-1])
        check('choices', inner.choices(app.available_actions()))
        check('scene', inner.scene(st, app.decision_context(), app.inner_extras()))
        for loc in ('cabin', 'woods', 'cafe', 'library', 'shop'):
            st['location'] = loc
            check('senses ' + loc, senses.outside(st))
        check('body', ' '.join(app.life.perceive(st)['sensations']))
        # The menu, his words for each action, and why something cannot be done.
        for k, a in actions.REGISTRY.items():
            check('menu ' + k, a.menu)
            check('choice ' + k, a.choice)
            check('why ' + k, a.why)
            assert k in LEGACY_ACTIONS or not any(p in k for p in products()), f'action {k} is named after a product'
        # Every details step he could be asked.
        for k in app.available_actions():
            d = {**app.DECISION_DEFAULTS, 'action': k, 'intention': 'something', 'reason': 'because'}
            try:
                req = app.parameter_request(d)
            except Exception:
                continue
            if req:
                check('details ' + k, json.dumps(req, ensure_ascii=False, default=str))
        # Edda's own instructions and a conversation with her.
        check("Edda's description", app.town.KEEPER_PERSONA)
        asked = []
        def talk(p, s, *a, **k):
            asked.append(p + ' ' + str(k.get('system', '')))
            if 'reply' in s.get('properties', {}):
                return {'reply': 'Morning.', 'proposal': {'kind': 'none', 'item': '', 'quantity': 1, 'credit': 0, 'minutes': 15, 'task': ''},
                        'note_about_crow': '', 'warmth': .5}, 1
            return {'say': 'Thank you.', 'accept_offer': False, 'leave': True, 'promise': ''}, 1
        app.model_call = talk
        app.talk_session('Morning, Edda.', 'a chat')
        for p in asked:
            check('talk', p)
# The test itself bites: a planted phrase is caught.
for bad in ('You can now make bricks.', 'Tip: try making a pot.', 'You learned how to tan.'):
    try:
        check('self-test', bad)
        raise SystemExit('the no-hints check missed: ' + bad)
    except AssertionError:
        pass
print('PASS v0.31.0: nothing he can see names a recipe, an unlock, a skill learned, or what he ought to make.')
