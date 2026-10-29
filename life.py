"""Small authored body model and evidence-based practical learning.

Values and rates are simulation choices, not clinical physiology. Only active
elapsed time advances them. This module never chooses Crow's intentions.
"""
import copy
import math


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def ensure(state):
    state.setdefault('body', {'reserve': float(state.get('energy',85)), 'stomach': 12.,
        'hydration': 85., 'sleep_debt': 1., 'exertion': 0., 'active_hours': 0.})
    state.setdefault('provisions', {'pantry': 24., 'berries': 8., 'berry_capacity': 12.,
        'water_litres': 40., 'water_capacity': 40.})
    state.setdefault('practical', {'control_hours': 0., 'methods': [], 'trials': [], 'next_trial_id': 1})
    state.setdefault('affect', {'valence': 0., 'arousal': 0., 'signals': []})
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


def effort(action):
    return {'sleep':0.,'rest':.05,'read':.08,'reflect':.08,'observe':.1,
            'eat':.1,'drink':.05,'inspect':.12,'test_object':.2,'plan':.25,
            'craft':.55,'construct':.75,'gather':.65,'explore':.45,
            'practise':.65,'move_object':.8,'fell_tree':1.,'browse':.08,'trade':.3}.get(action,.15)


def advance(state, seconds, action):
    body=ensure(state)
    # Small integration steps keep digestion and recovery independent of tick size.
    remaining=max(0.,float(seconds))
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
        supplies['berries']=min(supplies['berry_capacity'],supplies['berries']+.25*dt)
        supplies['water_litres']=min(supplies['water_capacity'],supplies['water_litres']+2*dt)
        for signal in state['affect']['signals']:signal['age_hours']+=dt
    refresh_affect(state)
    sync_energy(state)


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
            'supplies':{k:round(state['provisions'][k],2) for k in ['pantry','berries','water_litres']},
            'sources':{'food_store':'Ready-to-eat provisions; finite stock.',
                       'berry_patch':'Edible fruit; regrows slowly during active time.',
                       'spring':'Drinkable spring basin; replenishes during active time.'}}


def consume(state, action, ident):
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
        amount=min(1.,stock[key],max(0,(55-b['stomach'])/22))
        if amount<=.001:return {'success':False,'text':'No food was consumed; the source is empty or the stomach is full.'}
        stock[key]-=amount;b['stomach']+=22*amount
        text=f'Ate {amount:.2f} serving from {obj["name"]}. Nourishment will become available through digestion.'
    sync_energy(state)
    return {'success':True,'text':text,'source_id':ident,'consumed':round(amount,3)}


def method_parameters(state, decision):
    practical=state['practical'];saved=next((m for m in practical['methods'] if m['id']==decision.get('method_id')),None)
    if decision.get('method_id') and saved is None:raise ValueError('That saved method does not exist')
    raw=decision.get('attempt') or {}
    parameters=copy.deepcopy(saved['parameters']) if saved else {
        'support':raw.get('support','bench'),'passes':raw.get('passes','light'),
        'direction':raw.get('direction','along')}
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
    if state.get('possessions',{}).get('whetstone'):error*=.85  # a keen blade: an owned tool, not practice
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
            'recent_trials':[{k:t[k] for k in ['id','hypothesis','method_id','actual_error_mm','target_error_mm','goal_met','adjustment']}
                             for t in p['trials'][-2:]]}
