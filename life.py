"""Small authored body model and evidence-based practical learning.

Values and rates are simulation choices, not clinical physiology. Only active
elapsed time advances them. This module never chooses Crow's intentions.
"""
import copy
import math
import random
import re


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def ensure(state):
    state.setdefault('body', {'reserve': float(state.get('energy',85)), 'stomach': 12.,
        'hydration': 85., 'sleep_debt': 1., 'exertion': 0., 'active_hours': 0.})
    state.setdefault('provisions', {'pantry': 24., 'berries': 8., 'berry_capacity': 12.,
        'water_litres': 40., 'water_capacity': 40.})
    state.setdefault('practical', {'control_hours': 0., 'methods': [], 'trials': [], 'next_trial_id': 1})
    state.setdefault('affect', {'valence': 0., 'arousal': 0., 'signals': []})
    state.setdefault('tool_condition', {'axe': 1., 'carving_knife': 1.})
    world=state['built_world']
    if not world.get('life_sites_added'):
        from world_state import part
        objects=world['objects']
        objects.setdefault('food_store', {'id':'food_store','name':'Provisions chest','kind':'provisions',
            'x':-8.4,'z':-8.3,'portable':False,'revision':0,
            'parts':[part('chest',0,.35,0,.9,.7,.65,'#a58c5c')]})
        objects.setdefault('berry_patch', {'id':'berry_patch','name':'Fruit bushes','kind':'food_source',
            'x':-17.,'z':-3.,'portable':False,'revision':0,
            'parts':[part('foliage',0,.45,0,1.8,.9,1.2,'#577344'),part('fruit',.2,.95,0,.3,.15,.3,'#a34f58')]})
        objects.setdefault('spring', {'id':'spring','name':'Spring and water basin','kind':'water_source',
            'x':-17.,'z':1.,'portable':False,'revision':0,
            'parts':[part('basin',0,.2,0,1.1,.4,.9,'#789a91')]})
        # Stone really is stone in the material ledger.
        objects['spring']['parts'][0]['material']='stone'
        world['life_sites_added']=True;world['revision']+=1
    return state['body']


def _day_of_year(state):
    from datetime import datetime
    try:return datetime.fromisoformat(state['clock']['iso']).timetuple().tm_yday
    except (KeyError,ValueError,TypeError):return 200


def effort(action):
    return {'sleep':0.,'rest':.05,'read':.08,'reflect':.08,'observe':.1,
            'eat':.1,'drink':.05,'inspect':.12,'test_object':.2,'plan':.25,
            'craft':.55,'construct':.75,'gather':.65,'explore':.45,
            'practise':.65,'move_object':.8,'fell_tree':1.,'plant_tree':.6,'play_music':.2,'browse':.08,'trade':.3,'garden':.45,'talk':.05,'use_item':.2,
            'hunt':.5,'butcher':.55,'preserve':.3,'put_out_food':.08}.get(action,.15)


def advance(state, seconds, action):
    body=ensure(state)
    # Small integration steps keep digestion and recovery independent of tick size.
    remaining=max(0.,float(seconds))
    doy=_day_of_year(state)
    # Wild fruit (v0.23): the bushes bear from mid-July to mid-October; nothing grows on them the rest of
    # the year, and from November what is left goes over or is taken by birds, about a tenth a day.
    fruiting=196<=doy<=288;spoiling=doy>=305 or doy<=59
    while remaining>0:
        dt=min(remaining,60.)/3600;remaining-=dt*3600
        sleeping=action=='sleep';resting=action in ['sleep','rest'];work=effort(action)
        digested=min(body['stomach'],18*dt)
        body['stomach']-=digested
        body['reserve']=clamp(body['reserve']+digested-(2.5+5*work)*dt)
        body['hydration']=clamp(body['hydration']-(2+4*work)*dt)
        body['sleep_debt']=clamp(body['sleep_debt']+(-1.8 if sleeping else .65)*dt,0,24)
        body['exertion']=clamp(body['exertion']+(work*.16-(.32 if resting else .04))*dt,0,1)
        body['active_hours']+=dt
        supplies=state['provisions']
        if fruiting:supplies['berries']=min(supplies['berry_capacity'],supplies['berries']+.25*dt)
        elif spoiling:supplies['berries']=max(0.,supplies['berries']*(1-.1/24*dt))
        supplies['water_litres']=min(supplies['water_capacity'],supplies['water_litres']+2*dt)
        for signal in state['affect']['signals']:signal['age_hours']+=dt
        wear(state,action,dt)
    refresh_affect(state)
    sync_energy(state)


OUTDOOR_WORK = {'fell_tree', 'gather', 'construct', 'explore', 'practise', 'move_object', 'craft', 'garden', 'hunt', 'butcher'}
INDOOR_WORK = {'trade'}


def work_rate(state, action):
    """How fast physical work progresses (1 = normal). An authored consequence, not a score:
    marked tiredness, hunger or thirst slow work, and outdoor work in the dark without a lantern
    goes at half speed. Rest, reading, eating and other non-physical activities are unaffected."""
    if action not in OUTDOOR_WORK and action not in INDOOR_WORK:
        return 1.
    rate = 1 / (1 + .6 * max(0., fatigue(state) - .2))
    if action in OUTDOOR_WORK and state.get('daylight', 1) < .12 and not state.get('possessions', {}).get('lantern'):
        rate *= .5
    edge = state.get('tool_condition', {})
    if action == 'fell_tree':
        rate *= .4 + .6 * edge.get('axe', 1.)
    elif action == 'gather':
        rate *= .7 + .3 * edge.get('axe', 1.)
    elif action == 'construct':
        rate *= .85 + .15 * edge.get('axe', 1.)
    return rate


# Blades dull with use (per active hour of that work) and stay dull until something restores the edge.
WEAR = {'fell_tree': ('axe', .05), 'gather': ('axe', .02), 'construct': ('axe', .01), 'craft': ('carving_knife', .06)}


def wear(state, action, hours):
    tool, rate = WEAR.get(action, (None, 0))
    if tool:
        cond = state.setdefault('tool_condition', {'axe': 1., 'carving_knife': 1.})
        cond[tool] = round(max(.2, cond.get(tool, 1.) - rate * hours), 4)


def tool_feel(state, tool):
    """What the edge looks and feels like: observation, not explanation."""
    c = state.get('tool_condition', {}).get(tool, 1.)
    name = {'axe': 'axe', 'carving_knife': 'carving knife'}.get(tool, tool)
    if c > .85:
        return f'The {name} edge is bright and keen.'
    if c > .6:
        return f'The {name} edge has lost a little of its shine.'
    if c > .4:
        return f'The {name} edge is dull; it catches the light along its length.'
    return f'The {name} edge is rounded and nicked.'


def sync_energy(state):
    b=state['body']
    state['energy']=round(clamp(b['reserve']-b['sleep_debt']*2-b['exertion']*25),2)


def fatigue(state):
    b=ensure(state)
    return clamp(b['exertion']+b['sleep_debt']/18+max(0,40-b['reserve'])/80+max(0,40-b['hydration'])/80,0,2)


def perceive(state):
    b=ensure(state);sensations=[]
    if b['reserve']<35 and b['stomach']<8:sensations.append('Persistent hunger; little food is being digested.')
    elif b['reserve']<65 and b['stomach']<8:sensations.append('Some hunger.')
    if b['stomach']>35:sensations.append('Stomach feels full.')
    elif b['stomach']>8:sensations.append('Food is still digesting.')
    if b['hydration']<35:sensations.append('Strong thirst; mouth feels dry.')
    elif b['hydration']<65:sensations.append('Noticeable thirst.')
    if b['sleep_debt']>8:sensations.append('Heavy sleepiness and difficulty concentrating.')
    elif b['sleep_debt']>4:sensations.append('Beginning to feel sleepy.')
    if b['exertion']>.45:sensations.append('Muscles feel tired from recent effort.')
    if not sensations:sensations.append('No strong bodily discomfort.')
    return {'sensations':sensations,'work_impairment':round(fatigue(state),2),
            'supplies':{'ready_food_servings':round(state['provisions']['pantry'],2),
                        'in_the_provisions_chest':__import__('foods').view(state),
                        **({'beside_the_cabin':__import__('wildlife').carcass_view(state)} if state.get('wildlife',{}).get('carcasses') else {}),'fruit_on_bushes_servings':round(state['provisions']['berries'],2),
                        'spring_water_litres':round(state['provisions']['water_litres'],2)},  # units stated (v0.25)
            'sources':{'food_store':'Ready-to-eat provisions; finite stock.',
                       'berry_patch':'Wild fruit bushes; they bear fruit from mid-summer into autumn and none the rest of the year.',
                       'spring':'Drinkable spring basin; replenishes during active time.'}}


def consume(state, action, ident, food=''):
    ensure(state);ident=ident or ('spring' if action=='drink' else 'food_store')
    obj=state['built_world']['objects'].get(ident)
    if not obj or not obj.get('parts'):return {'success':False,'text':'That source is not available.'}
    b=state['body'];stock=state['provisions']
    if action=='drink':
        if ident!='spring':return {'success':False,'text':'That object is not a known drinkable water source.'}
        amount=min(.4,stock['water_litres'],max(0,(100-b['hydration'])/35))
        if amount<=.001:return {'success':False,'text':'No water was consumed; the basin is empty or hydration is already sufficient.'}
        stock['water_litres']-=amount;b['hydration']=clamp(b['hydration']+35*amount)
        text=f'Drank {amount:.2f} litres from the spring basin.'
    else:
        key={'food_store':'pantry','berry_patch':'berries'}.get(ident)
        if key is None:return {'success':False,'text':'That object is not a known edible food source.'}
        # v0.26: each food fills him by its own amount (foods.FOODS; never shown to him).
        import foods
        if key=='pantry':
            foods.larder(state)
            have=[l['food'] for l in stock['larder']]
            kind=food if food in have else (have[0] if have else 'provisions')
            if food and food not in have and have:
                kind=next((l['food'] for l in stock['larder'] if foods.FOODS.get(l['food'],{}).get('name','')==food),kind)
        else:kind='berries'
        per=foods.fill(kind)
        avail=sum(l['servings'] for l in stock['larder'] if l['food']==kind) if key=='pantry' else stock[key]
        amount=min(1.,avail,max(0,(55-b['stomach'])/per))
        if amount<=.001:
            if key=='berries' and stock[key]<=.001:
                bare='The fruit bushes are bare.'+('' if 196<=_day_of_year(state)<=288 else ' Their fruiting season is over for the year.')
                return {'success':False,'text':bare}
            return {'success':False,'text':'No food was consumed; the source is empty or the stomach is full.'}
        if key=='pantry':foods.take(state,kind,amount)
        else:stock[key]-=amount
        b['stomach']+=per*amount
        what=foods.FOODS.get(kind,foods.FOODS['provisions'])['name']
        text=f'Ate {amount:.2f} serving of {what} from {obj["name"]}. Nourishment will become available through digestion.'
    sync_energy(state)
    return {'success':True,'text':text,'source_id':ident,'consumed':round(amount,3)}


def method_parameters(state, decision):
    practical=state['practical'];saved=next((m for m in practical['methods'] if m['id']==decision.get('method_id')),None)
    if decision.get('method_id') and saved is None:raise ValueError('That saved method does not exist')
    raw=decision.get('attempt') or {}
    # A reused method is only a starting point: any setting he states for this attempt replaces it.
    # (Before v0.21.1 a reused method silently overrode his stated settings.)
    base=copy.deepcopy(saved['parameters']) if saved else {'support':'bench','passes':'light','direction':'along'}
    parameters={k:raw.get(k) or base[k] for k in ['support','passes','direction']}
    if parameters['support'] not in ['hand','bench'] or parameters['passes'] not in ['light','deep'] or parameters['direction'] not in ['along','across']:
        raise ValueError('Unsupported working method')
    return parameters


def validate_attempt(state, decision):
    raw=decision.get('attempt',{})
    if not isinstance(raw,dict):raise ValueError('An attempt must be an object')
    method_parameters(state,decision)
    for key in ['target_error_mm','expected_error_mm']:
        if key in raw:
            v=raw[key]
            if type(v) not in [int,float] or not math.isfinite(v) or not .5<=v<=50:
                raise ValueError('Carving error estimates/tolerances must be 0.5–50 mm')
    if 'predicted_success' in raw and type(raw['predicted_success']) is not bool:raise ValueError('Invalid prediction')
    if 'hypothesis' in raw and not isinstance(raw['hypothesis'],str):raise ValueError('Invalid hypothesis')


def practical_attempt(state, decision, seconds):
    """One bounded carving domain; measured error, not claimed general physics."""
    ensure(state);p=state['practical'];raw=decision.get('attempt') or {}
    method=method_parameters(state,decision)
    target=raw.get('target_error_mm',12.)
    if type(target) not in [int,float] or not math.isfinite(target) or not .5<=target<=50:
        raise ValueError('Carving tolerance must be between 0.5 and 50 mm')
    practice=p['control_hours']
    error=(7/(1+math.sqrt(practice+.1)))*(1+fatigue(state)*.7)
    error*=1 if method['support']=='bench' else 1.8
    error*=1 if method['passes']=='light' else 1.7
    error*=1 if method['direction']=='along' else 1.5
    error*=1+(1-state.get('tool_condition',{}).get('carving_knife',1.))  # a dull knife tears instead of cutting
    if state.get('daylight',1)<.12 and not state.get('possessions',{}).get('lantern'):error*=1.4  # carving by starlight
    error=round(error,2);met=error<=target
    # Motor practice transfers across shapes, but reading and idle time cannot add it.
    p['control_hours']+=max(0,seconds)/3600*.12/(1+fatigue(state))
    signature=':'.join(method[k] for k in ['support','passes','direction'])
    saved=next((m for m in p['methods'] if m['id']==signature),None)
    if not saved:
        saved={'id':signature,'parameters':method,'attempts':0,'successes':0,'best_error_mm':error,'shapes':[],'evidence':[]}
        p['methods'].append(saved)
    saved['attempts']+=1;saved['successes']+=int(met);saved['best_error_mm']=min(saved['best_error_mm'],error)
    shape=decision.get('creation_shape','orb')
    if met and shape not in saved['shapes']:saved['shapes'].append(shape)
    predicted=raw.get('predicted_success')
    if type(predicted) is not bool:predicted=None
    expected=raw.get('expected_error_mm')
    if type(expected) not in [int,float] or not math.isfinite(expected):expected=None
    trial={'id':p['next_trial_id'],'hypothesis':str(raw.get('hypothesis',''))[:300],
           'intention':decision.get('intention','')[:300], 'method_id':signature,
           'parameters':method,'shape':shape,'target_error_mm':target,
           'predicted_success':predicted,'expected_error_mm':expected,
           'actual_error_mm':error,'goal_met':met,'fatigue':round(fatigue(state),3),
           'prediction_error_mm':round(error-expected,2) if expected is not None else None,
           'source_id':None,'adjustment':''}
    p['next_trial_id']+=1;p['trials'].append(trial)
    return trial


def bind_trial(state, trial, memory):
    trial['source_id']=memory['id'];trial['at']=memory['at']
    method=next(m for m in state['practical']['methods'] if m['id']==trial['method_id'])
    method['evidence'].append(memory['id'])


def appraise(state, memory, result):
    ensure(state)
    def bounded(key,default,lo,hi):
        value=result.get(key,default)
        if type(value) not in [int,float] or not math.isfinite(value):raise ValueError('Invalid appraisal '+key)
        return clamp(value,lo,hi)
    # The evidence is fixed by the executor, never supplied as a made-up model ID.
    signal={'source_id':memory['id'],'concern':memory.get('intention') or memory.get('reason',''),
            'meaning':str(result.get('meaning',''))[:300],
            'valence':bounded('valence',0,-1,1),'arousal':bounded('arousal',0,0,1),
            'importance':bounded('importance',0,0,1),'age_hours':0.}
    state['affect']['signals'].append(signal)
    trial=next((t for t in state['practical']['trials'] if t['source_id']==memory['id']),None)
    if trial:trial['adjustment']=str(result.get('adjustment',''))[:300]
    refresh_affect(state)
    return signal


def refresh_affect(state):
    affect=state['affect'];signals=affect['signals']
    signals[:]=[s for s in signals if s['importance']*math.exp(-s['age_hours']/(1+8*s['importance']))>.005][-100:]
    weights=[s['importance']*math.exp(-s['age_hours']/(1+8*s['importance'])) for s in signals]
    total=max(1.,sum(weights))
    affect['valence']=round(sum(s['valence']*w for s,w in zip(signals,weights))/total,3)
    affect['arousal']=round(sum(s['arousal']*w for s,w in zip(signals,weights))/total,3)


def learning_context(state):
    ensure(state);p=state['practical']
    return {'methods':[{'id':m['id'],'parameters':m['parameters'],'tested_shapes':m['shapes'],
                        'attempts':m['attempts'],'successes':m['successes'],'best_error_mm':m['best_error_mm']}
                       for m in sorted(p['methods'],key=lambda m:m['evidence'][-1] if m['evidence'] else 0)[-3:]],
            'recent_trials':[{**{k:t[k] for k in ['id','hypothesis','method_id','actual_error_mm','target_error_mm','goal_met','adjustment']},
                              **({'note':t['note']} if t.get('note') else {})}
                             for t in p['trials'][-2:]],
            'trials_whose_method_may_differ_from_the_hypothesis':[{'id':t['id'],'method_used':t['method_id'],'note':t['note']}
                             for t in p['trials'] if t.get('note')][-6:]}


_ASKED = re.compile(r'\b(?:to|with) (hand|bench|light|deep|along|across)\b|\b(hand|bench) support\b|\b(light|deep) passes\b', re.I)
_GROUP = {'hand': 'support', 'bench': 'support', 'light': 'passes', 'deep': 'passes', 'along': 'direction', 'across': 'direction'}


def annotate_overridden_trials(state):
    """Once: mark past carving trials whose hypothesis names a setting that was not the one used.

    Before v0.21.1, reusing a saved method silently replaced the settings he stated. His
    requested settings were not stored, so this is an inference from his own wording and
    is labelled as uncertain; measured results are left exactly as they were."""
    ensure(state)
    p = state['practical']
    if p.get('override_annotated'):
        return 0
    marked = 0
    for t in p['trials']:
        text = str(t.get('hypothesis', ''))
        named = {}
        for m in _ASKED.finditer(text):
            word = next(g for g in m.groups() if g).lower()
            named.setdefault(_GROUP[word], set()).add(word)
        used = t.get('parameters') or {}
        differ = [f'{g}: {", ".join(sorted(v))} named, {used.get(g)} used' for g, v in named.items()
                  if used.get(g) and used.get(g) not in v]
        if differ:
            t['note'] = ('Possibly not the method he meant to test (' + '; '.join(differ) + '). A reused saved method '
                         'overrode stated settings until v0.21.1. The measured error is real for the method used.')
            marked += 1
    p['override_annotated'] = True
    return marked


def archery_session(state, seconds, seed):
    """Twelve arrows at the range's target, 18 m away. Results are measured, not judged.

    Spread shrinks with hours of practice (earlier unmeasured sessions count as practice too),
    and grows with fatigue and darkness. The target face is 122 cm across in ten rings."""
    ensure(state)
    p = state['practical']
    if 'archery_hours' not in p:
        p['archery_hours'] = round(.5 * state.get('skills', {}).get('archery', 0), 3)
    rng = random.Random(seed)
    spread = 40 / (1 + math.sqrt(p['archery_hours'])) * (1 + fatigue(state) * .6)
    dark = state.get('daylight', 1) < .12
    if dark:
        spread *= 1.6 if state.get('possessions', {}).get('lantern') else 2.6
    dists = sorted(round(math.hypot(rng.gauss(0, spread), rng.gauss(0, spread)), 1) for _ in range(12))
    on_face = [d for d in dists if d <= 61]
    gold = sum(d <= 12.2 for d in dists)
    p['archery_hours'] = round(p['archery_hours'] + max(0, seconds) / 3600 / (1 + fatigue(state)), 3)
    record = {'arrows': 12, 'on_target': len(on_face), 'in_gold': gold,
              'mean_cm_from_centre': round(sum(on_face) / len(on_face), 1) if on_face else None,
              'closest_cm': dists[0], 'dark': dark}
    p.setdefault('archery', []).append(record)
    p['archery'] = p['archery'][-40:]
    text = (f'Shot 12 arrows at the target 18 m away{" in the dark" if dark else ""}. {len(on_face)} hit the face, '
            f'{gold} in the gold.' + (f' Hits averaged {record["mean_cm_from_centre"]} cm from the centre; the closest was '
            f'{dists[0]} cm.' if on_face else ' None landed on the face.'))
    return {'success': True, 'text': text, 'archery': record}


# Building craft. Every shape can be attempted from the start; how true it comes out depends on
# practice with that kind of shape (with some carry-over from handiwork in general), on fatigue
# and on light. These difficulty figures are authored world properties, not shown to Crow.
SHAPE_FAMILY = {'box': 'straight', 'cylinder': 'turned', 'cone': 'turned', 'sphere': 'turned', 'wedge': 'angled', 'arch': 'curved'}
SHAPE_DIFFICULTY = {'box': 1., 'cylinder': 1.5, 'cone': 1.8, 'sphere': 2.2, 'wedge': 2., 'arch': 3.5}
SHAPE_FAILS_AT_CM = {'box': 30., 'cylinder': 25., 'cone': 22., 'sphere': 20., 'wedge': 16., 'arch': 11.}


def building(state):
    return ensure(state) and state['practical'].setdefault('building', {'hours': {}, 'parts': []})


def build_practice(state, parts, minutes):
    """Time actually spent building adds practice to the kinds of shape being worked."""
    record = building(state)
    if not parts or minutes <= 0:
        return
    share = minutes / 60 * .5 / (1 + fatigue(state)) / len(parts)
    for p in parts:
        fam = SHAPE_FAMILY.get(p['shape'], 'straight')
        record['hours'][fam] = round(record['hours'].get(fam, 0.) + share, 4)


def build_parts(state, plan_id, parts):
    """Execute a finished plan's parts: returns (placed, failed, report). Deterministic per plan."""
    import hashlib
    record = building(state)
    hours = record['hours']
    general = sum(hours.values())
    dark = state.get('daylight', 1) < .12 and not state.get('possessions', {}).get('lantern')
    placed, failed, notes = [], [], []
    for i, p in enumerate(parts):
        fam = SHAPE_FAMILY.get(p['shape'], 'straight')
        practice = hours.get(fam, 0.) + .3 * (general - hours.get(fam, 0.))
        jitter = .6 + int(hashlib.sha1(f'{plan_id}:{i}'.encode()).hexdigest()[:6], 16) / 0xffffff * .8
        err = 5 * SHAPE_DIFFICULTY.get(p['shape'], 1.) / (1 + math.sqrt(practice / 3)) * (1 + .7 * fatigue(state)) * (1.5 if dark else 1) * jitter
        err = round(err, 1)
        outcome = {'shape': p['shape'], 'error_cm': err, 'plan': plan_id}
        if err >= SHAPE_FAILS_AT_CM.get(p['shape'], 30.):
            failed.append(p)
            outcome['held'] = False
            notes.append(f'the {p["shape"]} ({p.get("id", "part")}) did not hold and came apart')
        else:
            angle = int(hashlib.sha1(f'{plan_id}:{i}:a'.encode()).hexdigest()[:4], 16) / 0xffff * 2 * math.pi
            p['x'] = round(p['x'] + math.cos(angle) * err / 200, 3)
            p['z'] = round(p['z'] + math.sin(angle) * err / 200, 3)
            p['rotation_z'] = round(p.get('rotation_z', 0) + (err / 250) * (1 if i % 2 else -1), 3)
            p['finish'] = 'fine' if err < 2 else 'fair' if err < 6 else 'rough'
            placed.append(p)
            outcome['held'] = True
            notes.append(f'{p["shape"]} {p.get("id", "part")} {p["finish"]}, about {err:g} cm off true')
        record['parts'] = (record['parts'] + [outcome])[-80:]
    report = f'{len(placed)} of {len(parts)} parts held: ' + '; '.join(notes) + '.'
    if failed:
        report += ' Half the material of what fell apart was recoverable as offcuts.'
    return placed, failed, report


def building_record(state):
    """His own evidence about building, by shape: attempts, how many held, typical accuracy."""
    out = {}
    for o in building(state)['parts']:
        s = out.setdefault(o['shape'], {'attempts': 0, 'held': 0, 'cm_off': []})
        s['attempts'] += 1
        s['held'] += int(o['held'])
        s['cm_off'].append(o['error_cm'])
    return {k: {'attempts': v['attempts'], 'held': v['held'], 'recent_cm_off_true': v['cm_off'][-3:]} for k, v in out.items()}
