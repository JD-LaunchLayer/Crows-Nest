"""v0.36.6: stories that rest on Edda's soup (which never existed) are left, with a plain note; his words are kept."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import story
s = {'stories': [], 'next_story_id': 1, 'threads': [], 'promises': []}; story.ensure(s)
title = 'Stay at the stove with Edda, eat her soup and bread, and drink before we go through the ledger.'
s['stories'] = [{'id': 1, 'title': title, 'variants': [title], 'stage': 'pursuing', 'steps': [], 'count': 11},
                {'id': 2, 'title': 'Stay with Edda and go through the ledger line by line', 'variants': [], 'stage': 'pursuing', 'steps': [], 'count': 11}]
s['threads'] = [{'id': 1, 'text': 'I never got the soup Edda offered.', 'status': 'open', 'place': 'shop'}]
assert story.leave_phantom_stories(s) == 1
assert s['stories'][0]['stage'] == 'left' and 'no soup' in s['stories'][0]['ended_by'] and s['stories'][0]['title'] == title
assert s['stories'][1]['stage'] == 'pursuing', 'other stories untouched'
assert 'no soup' in s['threads'][0]['world_note'] and s['threads'][0]['text'] == 'I never got the soup Edda offered.'
assert story.leave_phantom_stories(s) == 0, 'once'
print('PASS v0.36.6: stories resting on soup that never existed are left, with a note; his words kept.')
