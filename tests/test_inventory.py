"""v0.24.4: everything sold to the post goes on its shelves and can be bought back, always at a profit to the post."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import town, world_state, life
s={'materials':12.,'stone':10.,'creations':[{'id':7,'name':'Bowl','shape':'bowl','quality':6,'day':1}]}
world_state.ensure(s);life.ensure(s);post=town.ensure(s)
# Wood: sold at the posted rate, then on the shelf by the kg, dearer than he was paid.
r=town.trade(s,'sell','wood',12,'t');assert r['success'] and s['materials']==0 and post['credit']==4 and post['stock']['wood']['qty']==12
r=town.trade(s,'buy','wood',6,'t');assert r['success'] and s['materials']==6 and post['credit']==1 and post['stock']['wood']['qty']==6
assert post['stock']['wood']['price']>1/3, 'the post sells on for more than it pays'
# Something he owns: about half the board price; it goes back on the board line.
s['possessions']['lantern']=1;before=post['stock']['lantern']['qty']
r=town.trade(s,'sell','lantern',1,'t');assert r['success'] and s['possessions']['lantern']==0 and post['stock']['lantern']['qty']==before+1 and post['credit']==4
# A carving: leaves his world, sits on the shelf, can be bought back (dearer) and returns.
obj=s['built_world']['objects']['carving-7'];r=town.trade(s,'sell','carving-7',1,'t')
assert r['success'] and 'carving-7' not in s['built_world']['objects'] and post['stock']['carving-7']['qty']==1
post['credit']=10;price=post['stock']['carving-7']['price'];assert price>2
r=town.trade(s,'buy','carving-7',1,'t');assert r['success'] and 'carving-7' in s['built_world']['objects'] and post['stock']['carving-7']['qty']==0
# Edda's deals move goods the same way.
s['materials']=9;ok=town.apply_proposal(s,{'kind':'buy_goods','item':'wood','quantity':9,'credit':3},'t',1)
assert ok['success'] and s['materials']==0 and post['stock']['wood']['qty']==15
assert town.board(s)['for_sale']['wood']['left']==15
# v0.25: things he made fetch well above their raw materials, more when better made; shaped workpieces sell too.
low=dict(s['creations'][0]);s['creations'].append({'id':8,'name':'Good bowl','shape':'bowl','quality':9,'day':2});world_state.ensure(s)
assert town._goods_value(s,'carving-8',1)>town._goods_value(s,'carving-7',1)>1/3*2
from world_state import part
wp={'id':'workpiece-1','name':'Shaped block','kind':'workpiece','portable':True,'x':1,'z':1,'parts':[part('body',0,.1,0,.2,.2,.2)],'revision':0}
s['built_world']['objects']['workpiece-1']=wp;raw=world_state.mass(wp['parts'])['wood']/3
v=town._goods_value(s,'workpiece-1',1);assert v>=2*raw+1
r=town.trade(s,'sell','workpiece-1',1,'t');assert r['success'] and 'workpiece-1' in post['stock']
print('PASS v0.24.4: sold goods go on the shelves and can be bought back at a profit; carvings return; Edda\'s deals move real goods.')
