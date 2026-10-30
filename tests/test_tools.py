"""Tools in his life: inspecting blades, using what he owns, and Edda (not Crow) knowing what goods are for."""
import importlib.util, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_tools_test',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,1,12,0,tzinfo=app.TZ);app.state['paused']=False
    assert 'use_item' not in app.available_actions(), 'nothing to use yet'
    app.state['possessions']['whetstone']=1;app.state['tool_condition']['axe']=.3
    prompts=[]
    def model(prompt,schema,limit=650,purpose='other',system=None):
        prompts.append((purpose,prompt,schema))
        if 'action' in schema['properties']:
            return {'action':model.action,'intention':'See what this stone is','reason':'Curious.','next_step':'','wish':'','wish_reason':'',
                    'project':'none','project_id':0,'memory_ids_used':[]},1
        if purpose=='parameters:inspect':return {'object_id':'whetstone'},1
        if purpose=='parameters:use_item':return {'use_item':'whetstone','use_on':'axe','use_how':'rub the axe edge along it'},1
        return {},1
    app.model_call=model
    model.action='inspect';app.decide_and_start(app.runtime['generation']);app.tick(app.state['pending']['remaining']);m=app.finish_action()
    assert 'flat grey stone' in m['event'] and 'sharpen' not in m['event'].lower()
    use_prompt=None
    model.action='use_item';app.decide_and_start(app.runtime['generation'])
    use_prompt=next(p for p in prompts if p[0]=='parameters:use_item')[1]
    assert 'sharpen' not in use_prompt.lower() and app.state['pending']['remaining']==1200
    app.tick(1200);m=app.finish_action();assert app.state['tool_condition']['axe']==1 and 'bright and even' in m['event']
    # Edda is given what her goods are for; Crow's own prompts never contain it.
    assert all('dull blades make chopping slow' not in p[1] for p in prompts)
    assert 'dull blades make chopping slow' in app.town.ITEM_KNOWLEDGE['whetstone']
print('PASS: possessions inspected by appearance only; using the whetstone on the axe restores it after real time; '
      'use is only offered when he owns something; knowledge of what goods do is Edda\'s, not his.')
