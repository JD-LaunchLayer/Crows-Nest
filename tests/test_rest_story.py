"""v0.36.3: a story about lying down to rest is done once he has rested, however it is worded; it is not carried on
for days as something he is in the middle of."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import story
s = {'stories': [], 'next_story_id': 1, 'clock': {'iso': '2026-12-22T06:00:00+00:00'}}
story.ensure(s)
title = 'Lie back down under the covers and rest until it gets light, letting my hands and feet warm up after the water.'
for i in range(3):
    m = {'id': i, 'kind': 'experience', 'action': 'rest', 'intention': title, 'at': f'2026-12-22T0{6 + i}:00:00+00:00', 'event': 'Finished a quiet rest.'}
    story.note_step(s, m); story.settle_need(s, m, [])
st = s['stories'][0]; assert st['stage'] == 'done' and st['ended_by'] == 'he rested', st['stage']
s2 = {'stories': [], 'next_story_id': 1, 'clock': {'iso': '2026-12-22T06:00:00+00:00'}}; story.ensure(s2)
for i in range(3):
    m = {'id': i, 'kind': 'experience', 'action': 'talk', 'intention': 'Stay with Edda and go through the ledger line by line', 'at': f'2026-12-22T1{i}:00:00+00:00', 'event': 'Talked.'}
    story.note_step(s2, m); story.settle_need(s2, m, [])
assert s2['stories'][0]['stage'] == 'pursuing', 'a story that is not about resting is untouched'
s3 = {'stories': [], 'next_story_id': 1, 'clock': {'iso': '2026-12-22T06:00:00+00:00'}}; story.ensure(s3)
for i in range(3):
    m = {'id': i, 'kind': 'experience', 'action': 'rest', 'intention': 'Stop the notebook copy loop for tonight; rest in the cabin and come back in daylight', 'at': f'2026-12-22T2{i}:00:00+00:00', 'event': 'Finished a quiet rest.'}
    story.note_step(s3, m); story.settle_need(s3, m, [])
assert s3['stories'][0]['stage'] == 'done', 'rest named anywhere in it counts (v0.36.4)'
print('PASS v0.36.3: lying down to rest is done once he has rested.')
