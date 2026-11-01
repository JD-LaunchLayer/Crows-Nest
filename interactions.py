"""Bounded, material-conserving object operations and reusable tested methods.

The model chooses an operation and targets. Geometry/properties decide what
happens. Methods are typed parameter records, never Python/JS or arbitrary code.
No operation assigns enjoyment, a hobby, a goal or a preferred posture.
"""
import copy
import hashlib
import json
import math

import life
import world_state as ws

VERBS = ['shape', 'split', 'stack', 'place_on', 'sit', 'lie']


def ensure(state):
    world = ws.ensure(state)
    if not world.get('interaction_furniture'):
        # These replace already visible scene props, rather than adding a new
        # reward/opportunity. Never replace an object that already has history.
        furniture = {
            'library_chair': ('Reading chair', -9.1, 9.3, True, [
                ws.part('seat', 0, .43, 0, .95, .12, .95, '#795d3f'),
                ws.part('back', 0, .95, .45, .95, .95, .12, '#795d3f'),
                *[ws.part('leg-'+str(i), x, .2, z, .10, .43, .10, '#795d3f')
                  for i, (x, z) in enumerate([(-.39,-.37),(-.39,.37),(.39,-.37),(.39,.37)])]]),
            'cabin_bed': ('Bed', -11.5, -10.3, False, [
                ws.part('bed', 0, .35, 0, 1.5, .4, 2.6, '#a3a782'),
                ws.part('pillow', 0, .65, -.8, 1.3, .18, .55, '#d5ccb1')]),
            'workbench': ('Workbench', 0, 12, False, [
                ws.part('top', 0, 1.2, 0, 3, .23, 1.4, '#a58c5c'),
                *[ws.part('leg-'+str(i), x, .6, z, .17, 1.2, .17, '#645739')
                  for i, (x, z) in enumerate([(-1.2,-.5),(-1.2,.5),(1.2,-.5),(1.2,.5)])]])}
        for ident, (name, x, z, portable, parts) in furniture.items():
            world['objects'].setdefault(ident, {'id': ident, 'name': name, 'x': x, 'z': z,
                'portable': portable, 'kind': 'furniture', 'parts': parts, 'revision': 0})
        world['interaction_furniture'] = True
        world['revision'] += 1
    return state.setdefault('procedures', {'methods': [], 'attempts': [], 'next_id': 1})


def surfaces(obj):
    """Visible flat upper faces, without pretending arbitrary geometry is a chair."""
    return [p for p in obj.get('parts', []) if p['shape'] in ('box', 'cylinder')
            and abs(p.get('rotation_z', 0)) < .05 and p['width'] >= .12 and p['depth'] >= .12]


def properties(obj):
    return {'id': obj['id'], 'name': obj['name'], 'portable': obj.get('portable', False),
        'materials_kg': ws.mass(obj.get('parts', [])),
        'parts': [{'id': p['id'], 'material': p['material'], 'shape': p['shape'],
                   'size_m': [p['width'], p['height'], p['depth']]} for p in obj.get('parts', [])[:8]],
        'flat_faces': [{'part_id': p['id'], 'height_m': round(p['y']+p['height']/2, 3),
                        'width_m': p['width'], 'depth_m': p['depth']} for p in surfaces(obj)][:6],
        'on': obj.get('on')}


def context(state, limit=8):
    objects = state['built_world']['objects']
    near = [o['id'] for o in ws.nearby(state)['objects']]
    # Nearby objects first; IDs for the whole world remain selectable in stage two.
    ids = near + [i for i in objects if i not in near and objects[i].get('parts')]
    return [properties(objects[i]) for i in ids[:limit] if objects[i].get('parts')]


def parameters(state, decision):
    op = decision.get('verb')
    if op not in VERBS:
        raise ValueError('Unknown physical operation')
    method_id = decision.get('procedure_id', '')
    params = copy.deepcopy(decision.get('interaction_params') or {})
    if method_id:
        method = next((m for m in state['procedures']['methods'] if m['id'] == method_id), None)
        if not method or method['verb'] != op:
            raise ValueError('That tested method is not available for this operation')
        params = copy.deepcopy(method['parameters'])
    return params


def prepare(state, decision):
    """Save predictions, method and current target revisions BEFORE any work."""
    ensure(state)
    for key in ('hypothesis','prediction','object_id','other_id','procedure_id','creation_name'):
        if not isinstance(decision.get(key,''),str):
            raise ValueError('Invalid interaction text: '+key)
    if not isinstance(decision.get('interaction_params',{}),dict):
        raise ValueError('Interaction parameters must be an object')
    params = parameters(state, decision)
    for key, value in params.items():
        if type(value) in (int, float) and not math.isfinite(value):
            raise ValueError('Non-finite interaction parameter')
    decision['interaction_params'] = params
    decision['interaction_revisions'] = {
        ident: state['built_world']['objects'][ident]['revision']
        for ident in (decision.get('object_id'), decision.get('other_id'))
        if ident in state['built_world']['objects']}
    decision['interaction_valid_posture'] = posture_target(state, decision) is not None


def duration(decision):
    if decision['verb']=='shape':
        return max(1800,_number(decision['interaction_params'],'mass_kg',.1,20)*1800)
    return {'shape': 1800, 'split': 1200, 'stack': 600, 'place_on': 180,
            'sit': 900, 'lie': 900}[decision['verb']]


def _object(state, ident):
    obj = state['built_world']['objects'].get(ident)
    if not obj or not obj.get('parts'):
        raise ValueError('That object is no longer present')
    return obj


def _face(obj, ident):
    face = next((p for p in surfaces(obj) if p['id'] == ident), None)
    if face is None:
        raise ValueError('That part has no supported flat upper face')
    return face


def _number(params, name, low, high):
    value = params.get(name)
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{name} must be between {low} and {high}')
    return value


def posture_target(state, d):
    if d.get('verb') not in ('sit', 'lie'):
        return None
    try:
        obj = _object(state, d.get('object_id'))
        face = _face(obj, d.get('interaction_params', {}).get('part_id'))
        top = face['y'] + face['height']/2
        width, depth = ((.35, .35) if d['verb'] == 'sit' else (.7, 1.6))
        if face['width'] < width or face['depth'] < depth or not .2 <= top <= 1.2:
            return None
        return {'x': obj['x']+face['x'], 'z': obj['z']+face['z'], 'height': top,
                'verb': d['verb'], 'object_id': obj['id'], 'part_id': face['id']}
    except ValueError:
        return None


def _new_object(state, name, parts, x=None, z=None):
    world = state['built_world']
    if x is None or z is None:
        # Completed work is put down in a free spot beside the bench. Crow can
        # subsequently choose a different place; this is no artistic layout.
        for candidate in range(100):
            x=(candidate%10)*.55-2.5;z=8-(candidate//10)*.55
            if not ws.intersects_world(world,{'parts':parts},x,z):break
        else:raise ValueError('No clear space beside the workbench for that result')
    for p in parts:
        if abs(x+p['x'])+p['width']/2>31 or abs(z+p['z'])+p['depth']/2>31:
            raise ValueError('The result would extend beyond the world boundary')
    ident = 'worked-' + str(world['next_object_id'])
    world['next_object_id'] += 1
    obj = {'id': ident, 'name': str(name or 'Untitled workpiece')[:100], 'kind': 'workpiece',
           'parts': parts, 'x': x, 'z': z, 'portable': sum(ws.mass(parts).values()) <= 20,
           'revision': 0}
    world['objects'][ident] = obj
    return obj


def _bottom(obj):
    return min(p['y']-p['height']/2 for p in obj['parts'])


def _fits_on(obj, face):
    lo = [min(p[k]-p[size]/2 for p in obj['parts']) for k, size in [('x','width'),('z','depth')]]
    hi = [max(p[k]+p[size]/2 for p in obj['parts']) for k, size in [('x','width'),('z','depth')]]
    if hi[0]-lo[0] > face['width'] or hi[1]-lo[1] > face['depth']:
        raise ValueError('The object overhangs that face; it was not placed')
    return [(lo[i]+hi[i])/2 for i in range(2)]


def _execute(state, d, seconds):
    world = state['built_world']; op = d['verb']; p = d['interaction_params']
    for ident, revision in d.get('interaction_revisions', {}).items():
        if _object(state, ident)['revision'] != revision:
            raise ValueError('A target changed after work began; nothing was changed')
    if op in ('sit', 'lie'):
        target = posture_target(state, d)
        if not target:
            raise ValueError('That face cannot support that posture at a reachable height')
        state['posture'] = target
        return {'success': True, 'text': ('Sat' if op == 'sit' else 'Lay down')+
                ' on '+_object(state,d['object_id'])['name']+'.', 'object_id':d['object_id'], 'changed_ids': []}
    if op == 'shape':
        material = p.get('material')
        if material not in ws.DENSITY:
            raise ValueError('That material is not supported')
        if material != 'wood' or not world['tools'].get('axe'):
            raise ValueError('The available blades cannot shape that material')
        kg = round(_number(p, 'mass_kg', .1, 20), 2)
        width = _number(p, 'width_m', .05, 2); depth = _number(p, 'depth_m', .05, 2)
        shape = p.get('shape')
        if shape not in ws.SHAPES:
            raise ValueError('Unsupported solid shape')
        if ws.inventory(state, material)+1e-9 < kg:
            raise ValueError('Not enough material in inventory; no object was made')
        if p.get('support') not in ('hand', 'bench') or p.get('passes') not in ('light', 'deep'):
            raise ValueError('Unsupported working method')
        if p['support'] == 'bench' and not any(surfaces(o) for o in world['objects'].values() if o['id']=='workbench'):
            raise ValueError('The workbench no longer has a working surface')
        practice = state['practical']['control_hours']
        error = .007/(1+math.sqrt(practice+.1))*(1+.7*life.fatigue(state))
        error *= (1 if p['support']=='bench' else 1.8)*(1 if p['passes']=='light' else 1.7)
        error *= 1+(1-state.get('tool_condition',{}).get('carving_knife',1.))
        actual_width = width+error
        piece = ws.part('body',0,0,0,actual_width,1,depth,ws.COLORS[material])
        piece.update(shape=shape,material=material)
        # Adjust height to conserve the chosen mass exactly, across all shapes.
        factors={'sphere':math.pi/6,'wedge':.5,'arch':.35,'cylinder':math.pi/4,'cone':math.pi/12}
        unit_mass = actual_width*depth*ws.DENSITY[material]*factors.get(shape,1.)
        height = kg/unit_mass
        if not .03 <= height <= 3:
            raise ValueError('The chosen mass and dimensions give an impractical height; nothing was made')
        piece.update(height=height,y=height/2)
        ws.add_inventory(state, material, -kg)
        obj = _new_object(state,d.get('creation_name'),[piece])
        state['practical']['control_hours'] += max(0,seconds)/3600*.12/(1+life.fatigue(state))
        return {'success': True, 'object_id':obj['id'], 'changed_ids':[obj['id']],
            'measurements':{'target_width_m':width,'actual_width_m':actual_width,'width_error_mm':round(error*1000,2),
                            'materials_kg':ws.mass(obj['parts'])},
            'text':f'Shaped {obj["name"]} ({obj["id"]}) from {kg:g} kg wood as a {shape}. Width {actual_width:.3f} m; {error*1000:.1f} mm wider than intended.'}
    obj = _object(state, d.get('object_id'))
    if not obj.get('portable'):
        raise ValueError('That whole object is fixed or too heavy for this operation')
    if any(o.get('on') == obj['id'] and o.get('parts') for o in world['objects'].values()):
        raise ValueError('Other objects are resting on it; move those first')
    if op == 'split':
        fraction = _number(p, 'fraction', .1, .9)
        if len(obj['parts']) != 1 or obj.get('on'):
            raise ValueError('Splitting currently needs a single loose solid on the ground')
        original = obj['parts'][0]
        if original['shape'] != 'box' or original['material'] != 'wood' or not world['tools'].get('axe'):
            raise ValueError('The axe can divide a loose wooden box-shaped blank; this object was unchanged')
        if original['width']*min(fraction,1-fraction) < .03:
            raise ValueError('That cut would leave a piece too narrow')
        left,right=copy.deepcopy(original),copy.deepcopy(original)
        left['width']*=fraction; right['width']*=1-fraction
        left['x']=right['x']=0
        # Both resulting solids keep their material. There is no free inventory credit.
        obj['parts']=[left];obj['revision']+=1;obj['kind']='workpiece'
        other=_new_object(state,d.get('creation_name') or obj['name']+' — offcut',[right],
                          obj['x']+(left['width']+right['width'])/2+.04,obj['z'])
        return {'success':True,'object_id':obj['id'],'changed_ids':[obj['id'],other['id']],
            'text':f'Divided {obj["id"]} into two wooden solids: {obj["id"]} and {other["id"]}. Both pieces remain in the world.'}
    other = _object(state, d.get('other_id'))
    if obj['id'] == other['id']:
        raise ValueError('An object cannot support itself')
    face = _face(other,p.get('part_id'))
    center = _fits_on(obj,face)
    moved=copy.deepcopy(obj)
    dy=face['y']+face['height']/2-_bottom(obj)
    moved['x']=other['x']+face['x']-center[0]
    moved['z']=other['z']+face['z']-center[1]
    for piece in moved['parts']:piece['y']+=dy
    if ws.intersects_world(world,moved,moved['x'],moved['z'],obj['id']):
        raise ValueError('Another solid blocks that placement; nothing moved')
    if op == 'place_on':
        obj.update(parts=moved['parts'],x=moved['x'],z=moved['z'],on=other['id'],revision=obj['revision']+1)
        return {'success':True,'object_id':obj['id'],'changed_ids':[obj['id']],
            'text':f'Placed {obj["name"]} on {other["name"]}, on face {face["id"]}. It remains a separate object.'}
    if not other.get('portable') or other.get('on') or obj.get('on'):
        raise ValueError('A reusable stack currently needs two loose portable solids')
    if sum(ws.mass(obj['parts']).values())+sum(ws.mass(other['parts']).values()) > 20:
        raise ValueError('That stack would be too heavy to carry as one assembly')
    parts=copy.deepcopy(other['parts'])
    for piece in moved['parts']:
        piece['x']+=moved['x']-other['x'];piece['z']+=moved['z']-other['z'];parts.append(piece)
    for i,piece in enumerate(parts):piece['id']='piece-'+str(i+1)
    stack=_new_object(state,d.get('creation_name') or 'Untitled stack',parts,other['x'],other['z'])
    for old in (obj,other):
        old.update(parts=[],portable=False,consumed_by=stack['id'],revision=old['revision']+1)
    return {'success':True,'object_id':stack['id'],'changed_ids':[obj['id'],other['id'],stack['id']],
            'text':f'Arranged two solids as {stack["name"]} ({stack["id"]}). All material remains in the stack. This is an arrangement, not a glued or engineered joint.'}


def execute(state, d, seconds):
    ensure(state)
    staged={**state,'built_world':copy.deepcopy(state['built_world']),
            'practical':copy.deepcopy(state['practical'])}
    try:
        result=_execute(staged,d,seconds)
    except (ValueError,KeyError,TypeError) as exc:
        result={'success':False,'text':'Attempt did not change the world: '+str(exc), 'changed_ids':[]}
    if result['success']:
        if result.get('changed_ids'):staged['built_world']['revision']+=1
        for key in ('built_world','practical','materials','stone','posture'):
            if key in staged:state[key]=staged[key]
    return result


def record(state, decision, result, memory):
    """Only the executor can add an attempt; research/reflection cannot certify a method."""
    book=ensure(state);op=decision['verb'];params=copy.deepcopy(decision['interaction_params'])
    signature=hashlib.sha256(json.dumps([op,params],sort_keys=True).encode()).hexdigest()[:12]
    ident='method-'+signature
    method=next((m for m in book['methods'] if m['id']==ident),None)
    if method is None:
        method={'id':ident,'verb':op,'parameters':params,'attempts':0,'successes':0,'evidence':[], 'tested_on':[]}
        book['methods'].append(method)
    method['attempts']+=1;method['successes']+=int(result['success'])
    method['evidence']=(method['evidence']+[memory['id']])[-20:]
    target=decision.get('object_id') or params.get('material','')
    if target not in method['tested_on']:method['tested_on']=(method['tested_on']+[target])[-12:]
    attempt={'id':book['next_id'],'source_id':memory['id'],'at':memory.get('at',''),'method_id':ident,
             'verb':op,'parameters':params,'success':result['success'],
             'hypothesis':decision.get('hypothesis','')[:250],
             'prediction':decision.get('prediction','')[:250],
             'result':result['text'][:500],'measurements':result.get('measurements',{}),
             'changed_ids':result.get('changed_ids',[]),'reused':bool(decision.get('procedure_id')),
             'intention':decision.get('intention','')[:250]}
    book['next_id']+=1;book['attempts']=(book['attempts']+[attempt])[-240:]
    book['methods']=book['methods'][-80:]
    return attempt


def learning_context(state, verb=None, limit=5):
    book=state.get('procedures',{})
    return {'methods':[copy.deepcopy(m) for m in book.get('methods',[]) if not verb or m['verb']==verb][-limit:],
            'recent_attempts':[copy.deepcopy(a) for a in book.get('attempts',[]) if not verb or a['verb']==verb][-2:]}
