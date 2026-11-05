"""v0.36.10: doing the work settles his promises and plans to do it. He swept at 08:39 and spent the day meaning to go
and sweep, his promise to sweep still open."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import story
s = {'stories': [], 'next_story_id': 1, 'threads': [], 'promises': []}; story.ensure(s)
s['promises'] = [{'id': 1, 'text': "I'll come back tomorrow to do the sweeping.", 'to': 'Edda Thorne', 'status': 'open'},
                 {'id': 2, 'text': "I'll be here Monday around one o'clock to carry the crates.", 'to': 'Edda Thorne', 'status': 'open'}]
s['stories'] = [{'id': 1, 'title': 'Get up slowly, loosen my stiff limbs, and then head to the trading post to start on the sweeping I owe Edda.',
                 'stage': 'pursuing', 'steps': [], 'count': 142},
                {'id': 2, 'title': 'Stay at the counter and hear her terms for the Monday crate job', 'stage': 'pursuing', 'steps': [], 'count': 5}]
assert story.work_done(s, 'sweep_post', '2027-01-09T08:39:00+00:00') == 1
assert s['promises'][0]['status'].startswith('kept') and s['promises'][1]['status'] == 'open'
assert s['stories'][0]['stage'] == 'done' and s['stories'][0]['ended_by'] == 'he did the sweeping' and s['stories'][1]['stage'] == 'pursuing'
assert s['promises'][0]['text'] == "I'll come back tomorrow to do the sweeping.", 'his words kept'
story.work_done(s, 'carry_crates', '2027-01-11T13:10:00+00:00')
assert s['promises'][1]['status'].startswith('kept') and s['stories'][1]['stage'] == 'done'
print('PASS v0.36.10: the work done settles his promises and plans to do it.')
s2 = {'stories': [{'id': 1, 'title': 'head to the post to start on the sweeping', 'stage': 'pursuing', 'started': '2027-01-08T20:00:00+00:00', 'steps': []},
                  {'id': 2, 'title': 'sweep again tomorrow', 'stage': 'pursuing', 'started': '2027-01-09T12:00:00+00:00', 'steps': []}],
      'promises': [{'id': 1, 'text': 'I will sweep tomorrow', 'status': 'open', 'at': '2027-01-09T15:00:00+00:00'}],
      'threads': [], 'next_story_id': 3, 'trading': {'jobs_done': {'sweep_post': '2027-01-09T08:39:00+00:00'}}}
story.settle_done_work(s2)
assert s2['stories'][0]['stage'] == 'done' and s2['stories'][1]['stage'] == 'pursuing' and s2['promises'][0]['status'] == 'open'
print('PASS v0.36.10: work already done settles only what came before it.')
# v0.36.12: agreeing the work answers the stories about hearing its terms, and keeps promises to give an answer.
s3 = {'stories': [{'id': 1, 'title': "Stay at Edda's counter and hear her full terms for the Monday crate job and the food bundle", 'stage': 'pursuing', 'steps': []},
                  {'id': 2, 'title': 'Walk home across the clearing in the dark', 'stage': 'pursuing', 'steps': []}],
      'promises': [{'id': 1, 'text': "I'll give you a clear answer on the crate carrying once I've eaten.", 'status': 'open'},
                   {'id': 2, 'text': "I'll do the crate work in the yard now.", 'status': 'open'}],
      'threads': [], 'next_story_id': 3}
story.work_agreed(s3, 'carry_crates', '2027-01-12T06:50:00+00:00')
assert s3['stories'][0]['stage'] == 'answered' and s3['stories'][1]['stage'] == 'pursuing'
assert s3['promises'][0]['status'].startswith('kept') and s3['promises'][1]['status'] == 'open', 'doing it is still owed'
print('PASS v0.36.12: agreed work answers the term-hearing stories.')
