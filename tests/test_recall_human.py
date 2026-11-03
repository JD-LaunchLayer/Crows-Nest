"""v0.29: recall closer to a person's: vivid moments stand out, places bring things back, rehearsal strengthens,
and a recalled moment comes with what happened just before and after."""
import sys, copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import memory_recall as mr
def mem(i,action,text,felt=None):
    m={'id':i,'kind':'experience','action':action,'event':text,'reason':'','at':f'2026-12-0{1+i%5}T10:00'}
    if felt:m['felt']=felt
    return m
base={'current_intention':'go to the trading post and talk to Edda about the bundle','next_step':'','projects':[],'location':'cabin',
      'memories':[mem(1,'rest','Finished a quiet rest in his cabin.'),
                  mem(2,'talk','Talked with Edda about the bundle price; she laughed and gave him a gift.',{'valence':.9,'importance':.9}),
                  mem(3,'trade','Bought the bundle at the post.'),
                  mem(4,'talk','Talked with Edda about the bundle and the weather.'),
                  mem(5,'drink','Drank at the spring.')]}
st=copy.deepcopy(base);before=copy.deepcopy(st)
r=mr.recall(st,3000,limit=4)
assert r[0]['id']==2, 'the vivid moment comes first among equally relevant ones'
assert any('around_it' in x for x in r) and any('before:' in a or 'after:' in a for x in r for a in x.get('around_it',[]))
assert st==before, 'recall never changes his saved life'
# Place cue: about to go to the shop brings shop memories up.
pl={'current_intention':'bundle','next_step':'','projects':[],'location':'cabin',
    'memories':[mem(1,'trade','Bought the bundle at the post.'),mem(2,'rest','Thought about the bundle in the cabin.')]}
assert mr.recall(pl,3000,limit=1)[0]['id']==2, 'at home, the newer cabin memory'
pl['pending']={'decision':{'action':'trade'}};assert mr.recall(pl,3000,limit=1)[0]['id']==1, 'heading to the post, the post memory'
# Rehearsal: a memory recalled often comes back ahead of an otherwise equal one.
st=copy.deepcopy(base);st['memories'][1].pop('felt',None);st['recall_strength']={'4':30}
assert mr.recall(st,3000,limit=2)[0]['id']==4
print('PASS v0.29: vivid moments, place cues, rehearsal, and before/after recall; recall stays read-only.')
