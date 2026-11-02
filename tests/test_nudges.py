"""v0.21: observation text carries no novelty score; stories are listed side by side, not newest-first."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import story

s={'body':{'active_hours':0.}}
def ev(i,intention,action='observe'):
    return {'id':i,'kind':'experience','at':'2026-11-01T10:00','intention':intention,'action':action,'event':'x','reason':'y'}
for i,(h,text) in enumerate([(0,'Carve a bowl that holds water'),(1,'Carve a bowl that holds water'),
                             (2,'Learn what the beetles under bark eat'),(3,'Learn what the beetles under bark eat'),
                             (50,'Watch the woodland edge at dusk'),(51,'Watch the woodland edge at dusk')]):
    s['body']['active_hours']=h;story.note_step(s,ev(i,text,'craft' if 'Carve' in text else 'observe'))
s['body']['active_hours']=100;story.age(s)
listed=story.context(s,10)
assert [x['story'] for x in listed]==['Carve a bowl that holds water','Learn what the beetles under bark eat','Watch the woodland edge at dusk'], listed
assert all('last_step' not in x for x in listed) and listed[0]['hours_since_last_step']==99 and listed[0]['stage']=='dormant'
assert [x['story'] for x in story.context(s,2)]==['Learn what the beetles under bark eat','Watch the woodland edge at dusk'], 'longest-untouched dropped first, order kept'
source=(ROOT/'ecology.py').read_text()
assert 'were new to him' not in source
print('PASS v0.21 nudges: no novelty score in observation text; all stories side by side in starting order.')
