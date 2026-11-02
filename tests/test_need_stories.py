"""v0.25.2: a story about easing a body need ends when the body no longer reports that need."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import story
st={'body':{'active_hours':1.}}
def step(action,intention,sens,i):
    m={'id':i,'kind':'experience','action':action,'intention':intention,'at':f't{i}','event':'x'}
    story.note_step(st,m);story.settle_need(st,m,sens);return next(s for s in st['stories'] if s['id']==m['story_id'])
s=step('drink','Ease the noticeable thirst at the spring first',['Noticeable thirst.'],1)
assert s['stage']=='started', 'still thirsty: stays open'
s=step('drink','Ease the noticeable thirst at the spring first',[],2)
assert s['stage']=='done' and s['ended_by'], 'thirst gone: done'
s=step('eat','Settle the mild hunger from the ready provisions',['Food is still digesting.'],3)
assert s['stage']=='done'
s=step('sleep','Sleep now that sleepiness has deepened',['Beginning to feel sleepy.'],4)
assert s['stage']=='started'
# Unrelated stories are never ended by a meal, and 'great' is not 'eat'.
s=step('eat','A great walk past tree-75 into unrecorded woodland',[],5)
assert s['stage']=='started'
s=step('rest','Ease the thirst before walking',[],6)
assert s['stage']=='started', 'only drinking can end a thirst story'
print('PASS v0.25.2: body-need stories end on the evidence of his own body; others untouched.')
