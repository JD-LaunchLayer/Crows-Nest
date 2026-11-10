"""v0.36.18: the machine sells the shelf, the slate pays a posted job once, and a job question is not the bread price."""
import sys
from datetime import datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import life, senses, town, world_state

s = {'materials': 0., 'stone': 0., 'creations': [], 'clock': {'iso': '2027-03-06T09:00:00'}}
world_state.ensure(s); life.ensure(s)
post = town.ensure(s)
shop = s['built_world']['objects']['trading_post']
assert any(p['id'] == 'machine_case' for p in shop['parts'])
n = len(shop['parts'])
town.ensure(s)
assert len(shop['parts']) == n
post['stock']['arrows']['qty'] = 3
trees = dict(s['built_world']['trees'])
town.ensure(s)
assert post['stock']['arrows']['qty'] == 3 and s['built_world']['trees'] == trees
assert not world_state.his_to_dismantle(shop)

post['credit'] = 5
before = len(post['ledger'])
bought = town.trade(s, 'buy', 'arrows', 1, s['clock']['iso'])
assert bought['success'] and post['credit'] == 4 and post['stock']['arrows']['qty'] == 2, bought
assert 'came out' in bought['text'] and '4 gold' in bought['text']
assert post['ledger'][-1]['text'].startswith('Bought 1 × Broadhead arrow for 1 gold')
assert post['ledger'][-1]['credit_after'] == 4 and len(post['ledger']) == before + 1

post['credit'] = 1.7
lines = len(post['ledger'])
refused = town.trade(s, 'buy', 'provisions_bundle', 1, s['clock']['iso'])
assert not refused['success'] and 'did not open' in refused['text'] and 'Not enough money' in refused['text']
assert post['credit'] == 1.7 and len(post['ledger']) == lines and post['stock']['provisions_bundle']['qty'] == town.STARTING_STOCK['provisions_bundle']['qty']

# The machine works while she is away.
s['world_rolls'] = {'seed': 1}
away = None
for hour in range(8, 20):
    s['clock'] = {'iso': f'2027-03-06T{hour:02d}:00:00'}
    if not town.keeper_here(s):
        away = hour
        break
if away is None:
    for day in range(1, 20):
        for hour in range(8, 19):
            s['clock'] = {'iso': f'2027-04-{day:02d}T{hour:02d}:00:00'}
            if not town.keeper_here(s):
                away = s['clock']['iso']
                break
        if away:
            break
assert away
credit = post['credit']
again = town.trade(s, 'buy', 'arrows', 1, s['clock']['iso'])
assert again['success'] and post['credit'] == round(credit - 1, 2)

# The slate pays a posted job once.
s['clock'] = {'iso': '2027-03-06T10:00:00'}
post['credit'] = 1.7
paid = town.trade(s, 'job', 'sweep_post', 1, s['clock']['iso'])
assert paid['success'] and 'slate' in paid['text'] and 'posted job' in paid['text'] and post['credit'] == 2.7
second = town.trade(s, 'job', 'sweep_post', 1, '2027-03-06T11:00:00')
assert not second['success'] and post['credit'] == 2.7
assert sum(1 for l in post['ledger'] if 'Sweep and tidy' in l['text'] and '2 gold 7 silver' in l['text']) == 1

# A job question that also mentions bread is not answered with the bundle's price.
s['clock'] = {'iso': '2027-03-06T09:17:00'}
post['credit'] = 1.7
words = "Write the sweeping job's terms, the work, the time and the pay, on the Friday ledger page. I won't buy the bread bundle. I have 1 gold 7 silver."
reply = town.counter_reply(s, words)
assert reply is None or 'Bundle of bread' not in reply, reply
assert town.counter_reply(s, 'What does the crate job pay?') is None
food = town.counter_reply(s, 'I have 1 gold 7 silver. Is there any cheaper food than the bread?')
assert food and 'Bundle of bread' in food and '1 gold 7 silver' in food
seen = town.inspect(s, 'trading_post', datetime.fromisoformat(s['clock']['iso']), 0.8)
assert 'machine' in seen['text'] and 'Broadhead arrow' in seen['text'] and 'Sweep and tidy' in seen['text']
print('PASS v0.36.18: the machine takes the right coin, the slate pays a job once, and a job question is not the bread price.')
