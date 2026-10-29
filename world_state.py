"""Persistent geometry, inventory, finite sources and material-checked construction.

This module implements consequences, not Crow's preferences or goals. Units are
metres and kilograms. Construction is a bounded geometric model, not engineering
validation or a full structural physics simulation.
"""
import copy
import math

DENSITY = {'wood': 500, 'stone': 2200}
COLORS = {'wood': '#a48859', 'stone': '#8b9187'}


def part(ident, x, y, z, w, h, d, color='#817057', rz=0):
    return {'id': ident, 'shape': 'box', 'x':x,'y':y,'z':z,'width':w,'height':h,'depth':d,'color':color,'rotation_z':rz,'material':'wood'}


def mass(parts):
    bill = {'wood':0.0, 'stone':0.0}
    for p in parts:
        volume=p['width']*p['height']*p['depth']
        if p['shape']=='sphere': volume*=math.pi/6
        elif p['shape']=='cylinder': volume*=math.pi/4
        elif p['shape']=='cone': volume*=math.pi/12
        bill[p['material']]+=volume*DENSITY[p['material']]
    return {k:round(v,2) for k,v in bill.items() if v>0}


def ensure(state):
    if 'built_world' not in state:
        shell=[part('floor',0,.01,0,7,.12,6),part('back',0,1.5,3,7,3,.18),
               part('left',-3.5,1.5,0,.18,3,6),part('right',3.5,1.5,0,.18,3,6),
               part('front_left',-2.5,1.5,-3,2,3,.18),part('front_right',2.5,1.5,-3,2,3,.18),
               part('lintel',0,2.75,-3,3,.5,.2),part('roof_left',-1.75,3.5,0,4.05,.18,6.8,'#4e5946',.37),
               part('roof_right',1.75,3.5,0,4.05,.18,6.8,'#4e5946',-.37)]
        state['built_world']={'objects':{'library':{'id':'library','name':'Reading cabin','kind':'structure','x':-11,'z':10,'portable':False,'parts':shell,'revision':0}},
                              'plans':[],'next_plan_id':1,'next_object_id':1,'revision':0,
                              'sources':{'wood':{'name':'Fallen timber in the woodland','stock':250.0,'area':'woods'},
                                         'stone':{'name':'Loose stone at the woodland edge','stock':400.0,'area':'woods'}},'last_result':None}
    state.setdefault('stone',0.0)
    world=state['built_world']
    if 'trees' not in world:
        world['trees']={}
        positions=[(math.cos(i*2.39996)*(23+(i%7)*1.1),math.sin(i*2.39996)*(23+(i%7)*1.1),4+(i%5)*.65) for i in range(65)]
        positions += [(17,10,5),(15,14,6),(20,12,5),(18,6,4),(-18,-9,5),(-20,-15,6)]
        for i,(x,z,h) in enumerate(positions):
            ident='tree-'+str(i)
            world['trees'][ident]={'id':ident,'x':x,'z':z,'height':h,'stage':'standing','timber_kg':round(h*18),'stock':0}
        world['tools']={'axe':1}
    for i,c in enumerate(state.get('creations',[])):
        ident='carving-'+str(c['id'])
        if ident not in world['objects']:
            shape={'spire':'cone','orb':'sphere','totem':'box','bowl':'cylinder'}.get(c['shape'],'box')
            # Existing carvings retain their previous placement. Migration spends
            # no more material; their historical one-unit cost is preserved.
            factor={'sphere':math.pi/6,'cone':math.pi/12,'cylinder':math.pi/4}.get(shape,1)
            # A new practice result has a measurable width deviation. Preserve
            # the paid kilogram by compensating height, rather than spawning mass.
            width=c.get('actual_width_m',.14)
            height=1/(500*width*.14*factor)
            p=part('body',0,height/2,0,width,height,.14);p['shape']=shape
            world['objects'][ident]={'id':ident,'name':c['name'],'kind':'carving','x':3+(i%5)*.9,'z':9+(i//5),
                                     'portable':True,'parts':[p],'paid_materials':{'wood':1.0},'revision':0}
            if 'actual_width_m' in c:world['objects'][ident]['work_measurement']={'target_width_m':c.get('target_width_m',.14),'actual_width_m':width}
    return world


def inventory(state, material):
    return state['materials'] if material=='wood' else state['stone']


def add_inventory(state, material, amount):
    key='materials' if material=='wood' else 'stone'
    state[key]=round(max(0,state[key]+amount),2)


def nearby(state):
    world=ensure(state)
    # Area-based observations, not claims of visual recognition or pixel vision.
    x,z={'cabin':[-10,-6],'range':[10,-7],'woods':[13,10],'workbench':[0,10],'library':[-11,5]}.get(state['location'],[0,0])
    objects=sorted(world['objects'].values(),key=lambda o:(o['x']-x)**2+(o['z']-z)**2)
    return {'observation_method':'area-based spatial state',
            'inventory_kg':{'wood':state['materials'],'stone':state['stone']},
            'sources':world['sources'],
            'objects':[{'id':o['id'],'name':o['name'],'x':o['x'],'z':o['z'],'portable':o['portable'],
                        'parts':[{'id':p['id'],'shape':p['shape'],'material':p['material']} for p in o['parts']][:9]} for o in objects[:4]],
            'tools':world['tools'],'trees':[t for t in sorted(world['trees'].values(),key=lambda t:(t['x']-x)**2+(t['z']-z)**2)[:4]],
            'plans':[{k:p[k] for k in ['id','name','operation','target_id','bill','minutes','status']} for p in world['plans'][-4:]]}


def fell_tree(state, ident):
    world=ensure(state);tree=world['trees'].get(ident)
    if not tree:return {'success':False,'text':'That tree does not exist.'}
    if tree['stage']!='standing':return {'success':False,'text':'That tree has already been felled.'}
    if not world['tools'].get('axe'):return {'success':False,'text':'No axe is available; the tree remains standing.'}
    tree['stage']='felled';tree['stock']=tree['timber_kg'];world['revision']+=1
    return {'success':True,'text':f'Felled {ident} with the axe. A stump remains and {tree["stock"]} kg of timber is at the site, not yet carried into inventory.'}


def collect(state, material, requested=3, source_id=''):
    world=ensure(state)
    source=world['sources'][material]
    tree=world['trees'].get(source_id) if source_id else None
    if tree:
        if material!='wood' or tree['stage']!='felled':return {'success':False,'text':'That tree is still standing or does not provide the requested material.'}
        source=tree
    amount=round(min(requested,source['stock']),2)
    if amount<=0:return {'success':False,'text':'No loose '+material+' remains at this source. Nothing was gathered.'}
    source['stock']=round(source['stock']-amount,2)
    add_inventory(state,material,amount);world['revision']+=1
    return {'success':True,'text':f'Gathered {amount:g} kg of {material} from {source.get("name",source_id)}. {source["stock"]:g} kg remains there.'}


def validate_parts(parts):
    import re
    if not isinstance(parts,list) or not 1<=len(parts)<=16:raise ValueError('A plan needs 1–16 solid parts')
    clean=[]
    for i,p in enumerate(parts):
        if not isinstance(p,dict) or p.get('shape') not in ['box','sphere','cylinder','cone']:raise ValueError('Unsupported part shape')
        if p.get('material') not in DENSITY:raise ValueError('Unsupported material')
        if not isinstance(p.get('color'),str) or not re.fullmatch(r'#[0-9a-fA-F]{6}',p['color']):raise ValueError('Invalid colour')
        c={'id':'part-'+str(i+1),'shape':p['shape'],'material':p['material'],'color':p['color'],'rotation_z':0}
        for k,lo,hi in [('x',-12,12),('y',0,8),('z',-12,12),('width',.03,8),('height',.03,6),('depth',.03,8)]:
            v=p.get(k)
            if type(v) not in [int,float] or not math.isfinite(v) or not lo<=v<=hi:raise ValueError('Invalid part dimension '+k)
            c[k]=v
        if c['y']-c['height']/2 < -.1:raise ValueError('A part would be buried below ground')
        clean.append(c)
    return clean


def propose(state, name, operation, target_id, x, z, parts=None, remove_part=''):
    world=ensure(state)
    if operation not in ['new','add','remove']:raise ValueError('Unknown build operation')
    if type(x) not in [int,float] or type(z) not in [int,float] or not -25<=x<=25 or not -25<=z<=25:raise ValueError('Site is outside the clearing')
    target=world['objects'].get(target_id)
    if operation in ['add','remove'] and not target:raise ValueError('That target does not exist')
    if operation=='remove':
        p=next((p for p in target['parts'] if p['id']==remove_part),None)
        if not p:raise ValueError('That part does not exist')
        prepared=[];bill={};minutes=15;salvage={k:round(v*.5,2) for k,v in mass([p]).items()}
    else:
        prepared=validate_parts(parts);bill=mass(prepared);salvage={}
        if not bill:raise ValueError('Plan has no material requirement')
        minutes=max(15,math.ceil(sum(bill.values())*2+len(prepared)*8))
        origin=target if operation=='add' else {'x':x,'z':z}
        for p in prepared:
            if abs(origin['x']+p['x'])+p['width']/2>31 or abs(origin['z']+p['z'])+p['depth']/2>31:raise ValueError('A part would extend outside the clearing')
    plan={'id':world['next_plan_id'],'name':name[:100] or 'Untitled plan','operation':operation,'target_id':target_id,
          'x':target['x'] if target else x,'z':target['z'] if target else z,'parts':prepared,'remove_part':remove_part,
          'bill':bill,'salvage':salvage,'minutes':minutes,'work_done_minutes':0,'status':'proposed','target_revision':target['revision'] if target else None}
    world['next_plan_id']+=1;world['plans'].append(plan);world['revision']+=1
    return copy.deepcopy(plan)


def plan_by_id(state, ident):
    return next((p for p in ensure(state)['plans'] if p['id']==ident),None)


def affordable(state, plan):
    return all(inventory(state,k)+.001>=v for k,v in plan['bill'].items())


def construct(state, plan_id, work_minutes=None):
    world=ensure(state);p=plan_by_id(state,plan_id)
    if not p or p['status'] not in ['proposed','in_progress']:return {'success':False,'text':'No unbuilt plan with that ID is available.'}
    target=world['objects'].get(p['target_id'])
    if p['operation'] in ['add','remove'] and (not target or target['revision']!=p['target_revision']):
        return {'success':False,'text':'The target changed after planning. A new plan is needed.'}
    if not affordable(state,p):return {'success':False,'text':'The required materials are not in inventory. No building occurred.'}
    if work_minutes is not None:
        remaining=max(0,p['minutes']-p.get('work_done_minutes',0))
        p['work_done_minutes']=round(p.get('work_done_minutes',0)+min(work_minutes,remaining),2)
        if p['work_done_minutes']<p['minutes']:
            p['status']='in_progress';world['revision']+=1
            return {'success':True,'built':False,'text':f'Worked {work_minutes:g} minutes on plan {p["id"]}. {p["minutes"]-p["work_done_minutes"]:g} minutes of construction remains; no completed object exists yet.'}
    if p['operation']=='new' and intersects_world(world,{'parts':p['parts']},p['x'],p['z']):
        return {'success':False,'text':'The planned site intersects another solid object. No building occurred.'}
    if p['operation']=='new':
        ident='built-'+str(world['next_object_id']);world['next_object_id']+=1
        target={'id':ident,'name':p['name'],'kind':'built','x':p['x'],'z':p['z'],'parts':copy.deepcopy(p['parts']),
                'portable':sum(p['bill'].values())<=20,'paid_materials':copy.deepcopy(p['bill']),'revision':0}
        world['objects'][ident]=target
    elif p['operation']=='add':
        for part in p['parts']:
            piece=copy.deepcopy(part);piece['id']='plan-'+str(p['id'])+'-'+piece['id'];target['parts'].append(piece)
        target['revision']+=1
    else:
        target['parts']=[part for part in target['parts'] if part['id']!=p['remove_part']];target['revision']+=1
    for k,v in p['bill'].items():add_inventory(state,k,-v)
    for k,v in p['salvage'].items():add_inventory(state,k,v)
    p['status']='built';world['revision']+=1
    return {'success':True,'built':True,'object_id':target['id'],'text':('Completed construction plan: '+p['name']+'. '+
            ('Recovered '+str(p['salvage'])+' kg of material.' if p['salvage'] else 'Used '+str(p['bill'])+' kg of material.'))}


def intersects_world(world, obj, x, z, ignore_id=None):
    for a in obj['parts']:
        # A floor supporting a new object is not an obstruction. This is an
        # axis-aligned overlap check; full structural physics is out of scope.
        for other in world['objects'].values():
            if other['id']==ignore_id:continue
            for b in other['parts']:
                if b['y']+b['height']/2<.2:continue
                ax,az=x+a['x'],z+a['z'];bx,bz=other['x']+b['x'],other['z']+b['z']
                if (abs(ax-bx)<(a['width']+b['width'])/2-.02 and
                    abs(az-bz)<(a['depth']+b['depth'])/2-.02 and
                    abs(a['y']-b['y'])<(a['height']+b['height'])/2-.02):return True
    return False


def move(state, ident, x, z):
    world=ensure(state);o=world['objects'].get(ident)
    if not o:return {'success':False,'text':'That object does not exist.'}
    if not o['portable']:return {'success':False,'text':'That object is too heavy to carry whole; it did not move.'}
    if type(x) not in [int,float] or type(z) not in [int,float] or not -25<=x<=25 or not -25<=z<=25:
        return {'success':False,'text':'That destination is outside the clearing.'}
    # Moving an object is a supported macro: travel, carry and put down. It does
    # not mean inventing a teleporting ability in the agent's autobiographical log.
    if intersects_world(world,o,x,z,ident):return {'success':False,'text':'The destination intersects another solid object; it was not moved.'}
    o['x']=x;o['z']=z;o['revision']+=1;world['revision']+=1
    return {'success':True,'object_id':ident,'text':f'Carried {o["name"]} and put it down at ({x:g}, {z:g}).'}
