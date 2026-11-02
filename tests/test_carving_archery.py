"""v0.21.1: stated carving settings beat a reused method; past mismatches are labelled; archery is measured."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import life

s={'built_world':{'objects':{},'life_sites_added':True},'skills':{'archery':10},'daylight':1}
life.ensure(s)
s['practical']['methods'].append({'id':'hand:light:along','parameters':{'support':'hand','passes':'light','direction':'along'}})
d={'method_id':'hand:light:along','attempt':{'passes':'deep'}}
assert life.method_parameters(s,d)=={'support':'hand','passes':'deep','direction':'along'}, 'his stated setting is used'
assert life.method_parameters(s,{'method_id':'hand:light:along','attempt':{}})['passes']=='light', 'unstated settings come from the method'
s['practical']['trials']=[
 {'id':1,'hypothesis':'Changing only pass depth from light to deep, keeping hand support','parameters':{'support':'hand','passes':'light','direction':'along'}},
 {'id':2,'hypothesis':'Changing only pass depth back to light, keeping hand support and along-grain direction','parameters':{'support':'hand','passes':'light','direction':'along'}}]
assert life.annotate_overridden_trials(s)==1 and 'passes: deep named, light used' in s['practical']['trials'][0]['note']
assert 'note' not in s['practical']['trials'][1] and life.annotate_overridden_trials(s)==0, 'once only'
assert s['practical']['trials'][0]['parameters']['passes']=='light', 'measured history is not rewritten'
a=life.archery_session(s,1800,1);b=life.archery_session(s,1800,1)
assert a['success'] and a['archery']['arrows']==12 and 'arrows' in a['text'] and s['practical']['archery_hours']>5
s['daylight']=0;dark=[life.archery_session(s,1800,i)['archery']['on_target'] for i in range(20)]
s['daylight']=1;light=[life.archery_session(s,1800,i)['archery']['on_target'] for i in range(20)]
assert sum(light)>sum(dark), 'darkness costs accuracy'
print('PASS v0.21.1: carving settings honoured, past mismatches labelled not rewritten, archery measured.')
