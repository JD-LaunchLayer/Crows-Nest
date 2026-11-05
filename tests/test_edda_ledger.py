"""v0.36.13: Edda goes by her ledger. A purse sum he names that is not the book's is corrected once, and prices
are reckoned from the book. Pay asked for before agreed work is refused: work is paid when it is done.
Nothing is suggested to him."""
import contextlib, importlib.util, io, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import town, world_state, life

s = {'materials': 6.7, 'stone': 0., 'creations': []}
world_state.ensure(s); life.ensure(s); town.ensure(s)
s['trading']['credit'] = 1.3
s['trading']['last_delivery'] = '2027-01-06T09:00:00+00:00'
s['clock'] = {'iso': '2027-01-13T11:00:00+00:00'}
favour = {'kind': 'favour', 'item': '', 'quantity': 1, 'credit': 2, 'minutes': 60,
          'task': 'Carry the delivered crates into the store room'}
assert town.check_proposal(s, dict(favour), 1)[0]
town.apply_proposal(s, dict(favour), '2027-01-06T12:00:00+00:00', 1)
assert s['keeper']['favours'] and abs(s['trading']['credit'] - 1.3) < 1e-9
before = len(s['trading']['ledger'])
assert abs(town.ledger_amount(s) - 1.3) < 1e-9
assert any(l['text'] == 'His purse, by the ledger: 1 gold 3 silver.' for l in s['trading']['ledger'])
assert len(s['trading']['ledger']) == before + 1, 'one line, and the earlier lines stay'
again = len(s['trading']['ledger']); town.ledger_amount(s); assert len(s['trading']['ledger']) == again, 'not written twice'
# The old lines are untouched.
assert s['trading']['ledger'][0]['text'].startswith('Agreed a favour')

wrong = 'I have 2 gold 8 silver. What can that buy?'
reply = town.counter_reply(s, wrong)
assert reply and '1 gold 3 silver' in reply and 'not 2 gold 8 silver' in reply, reply
assert 'Broadhead arrow' in reply and '1 gold' in reply.split('within it are:')[-1], reply
for dear in ('Packet of vegetable seeds', 'Bundle of bread', 'Oil lantern', 'Whetstone'):
    assert dear not in reply, (dear, reply)  # 2 gold 8 silver would meet the seeds; the ledger sum does not
for nudge in ('wood', 'sell', 'crate', 'you should', 'you can now', 'hint', 'recipe'):
    assert nudge not in reply.lower(), (nudge, reply)
assert town.named_purse("I've got 2 gold and 8 silver") == 2.8
assert town.named_purse('What can 2 gold 8 silver buy?') == 2.8
assert town.named_purse('What can I buy with 2 gold, 8 silver?') == 2.8
assert town.counter_reply(s, "I've got 2 gold and 8 silver, what will that buy?") is None, 'she has told him once'
assert town.counter_reply(s, 'What can 2 gold 8 silver buy?') is None
# The right sum is not a correction, and a wage is not his purse.
fresh = {'materials': 0., 'stone': 0., 'creations': []}
world_state.ensure(fresh); life.ensure(fresh); town.ensure(fresh); fresh['trading']['credit'] = 1.3
assert town.counter_reply(fresh, 'I have 1 gold 3 silver. What can that buy?') is None
assert town.counter_reply(fresh, 'The crates pay 2 gold.') is None
assert town.counter_reply(fresh, 'I have agreed the crates for 2 gold.') is None
assert 'ledger_told' not in fresh['keeper']

pay = town.counter_reply(s, 'Pay me the 2 gold up front before I start the crates.')
assert pay == 'Work is paid when it is done. That has always been the rule.', pay
assert '1 gold 3 silver' not in pay, 'the purse correction is not said again'
for nudge in ('wood', 'sell', 'you should', 'hint', 'start the'):
    assert nudge not in pay.lower(), (nudge, pay)
assert town.counter_reply(s, 'I need paying in advance for carrying the crates.') == pay
assert town.counter_reply(s, "I won't carry them unless I'm paid first.") == pay
assert town.counter_reply(s, 'What does the crate job pay?') is None
assert town.counter_reply(s, "I'll start after breakfast.") is None
assert abs(s['trading']['credit'] - 1.3) < 1e-9 and s['keeper']['favours'], 'nothing was paid and the favour still waits'
assert 'His gold and silver are the figure in your ledger' in town.KEEPER_PERSONA
assert 'paid when it is done' in town.KEEPER_PERSONA and 'Do not offer a sale or a task' in town.KEEPER_PERSONA
print('PASS v0.36.13: she corrects a wrong purse sum once from the ledger, and refuses pay before the work.')

# In a real talk her plain answer stands; a model that would waffle does not get to say the wrong sum is his.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT / 'crow.py', Path(td) / 'crow.py')
    spec = importlib.util.spec_from_file_location('crow_edda_ledger', Path(td) / 'crow.py')
    app = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE = lambda: datetime(2027, 1, 13, 11, 0, tzinfo=app.TZ)
    app.clock()
    st = app.state
    st['materials'] = 6.7
    st['trading']['credit'] = 1.3
    st['trading']['last_delivery'] = '2027-01-06T09:00:00+00:00'
    fav = {'kind': 'favour', 'item': '', 'quantity': 1, 'credit': 2, 'minutes': 60,
           'task': 'Carry the delivered crates into the store room'}
    assert town.check_proposal(st, dict(fav), st['day'])[0]
    town.apply_proposal(st, dict(fav), '2027-01-06T12:00:00+00:00', st['day'])
    calls = []

    def model(prompt, schema, limit=650, purpose='other', system=None):
        calls.append(purpose)
        if purpose == 'keeper':
            return {'reply': 'Perhaps we might look at that another time.',
                    'proposal': {'kind': 'gift', 'item': '', 'quantity': 1, 'credit': 1, 'minutes': 0, 'task': ''},
                    'note_about_crow': '', 'warmth': .2}, 1
        n = calls.count('talk')
        if n == 1:
            return {'say': 'So I have 2 gold 8 silver. What can that buy?', 'accept_offer': False, 'leave': False, 'promise': ''}, 1
        if n == 2:
            return {'say': 'Pay me the 2 gold up front before I start the crates.', 'accept_offer': False, 'leave': False, 'promise': ''}, 1
        return {'say': 'All right.', 'accept_offer': False, 'leave': True, 'promise': ''}, 1

    app.model_call = model
    session = app.talk_session('I have 2 gold 8 silver. What can that buy?', 'what the sum buys')
    edda = [c['text'] for c in session['conversation'] if c['who'] == 'Edda']
    assert '1 gold 3 silver' in edda[0] and 'Broadhead arrow' in edda[0] and 'Packet of vegetable seeds' not in edda[0], edda[0]
    assert 'another time' in edda[1], edda  # the repeated wrong sum is not corrected again
    assert edda[2] == 'Work is paid when it is done. That has always been the rule.', edda
    assert calls.count('keeper') == 1, calls
    assert session['agreed'] is None and abs(st['trading']['credit'] - 1.3) < 1e-9 and st['keeper']['favours']
    assert 'wood' not in ' '.join(edda).lower() and 'sell' not in ' '.join(edda).lower()
print('PASS v0.36.13: in the talk, the book answers; the favour stays unpaid until the work is done.')
