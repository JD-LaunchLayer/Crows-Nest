"""v0.30: Crow sees his own life in the first person, with no machinery; feelings in words; dreams and who he is;
he dozes instead of a stand-in mind acting for him; stand-in hours are marked, not changed."""
import contextlib, copy, importlib.util, io, json, re, shutil, sys, tempfile, time
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import inner, lived_fixture
assert inner.first_person('Finished a quiet rest in his cabin.')=='I finished a quiet rest in my cabin.'
assert inner.tidy('The promise I made to Edda (promises 112, 115).')=='The promise I made to Edda.'
assert 'simulated' not in inner.IDENTITY and 'Crow' in inner.IDENTITY
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_inner',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    lived_fixture.populate(app.state);app.state['paused']=False
    app.CLOCK_OVERRIDE=lambda:datetime(2026,12,8,8,0,tzinfo=app.TZ);app.clock();st=app.state
    # The moment as he knows it.
    seen=[]
    app.model_call=lambda p,s,l,*a:(seen.append((p,s)) or ({'action':'rest','intention':'rest','reason':'tired','next_step':'','wish':'','wish_reason':'','project':'none','which_project':''},1))
    app.choose_action();prompt,schema=seen[0]
    assert "I'm in my cabin" in prompt and 'What comes to mind' in prompt and 'In my purse' in prompt
    assert not re.search(r'\{"|\bid\b|valence|arousal|held, \d|\(\w+, \d+ steps', prompt)
    assert 'memory_ids_used' not in schema['properties'] and 'which_project' in schema['properties']
    # Feelings in words: the numbers are worked out from them.
    m=app.event('Talked with Edda Thorne at the trading post. Crow: “Hello.” Edda: “Morning.”','r',action='talk')
    asked=[]
    def reflect_model(p,s,l,*a):
        asked.append((p,s));return {'feeling':'Glad she smiled.','how_it_felt':'good','how_stirred':'a little stirred','how_much_it_matters':'quite a lot',
            'meaning':'She is warming to me.','lesson':'','topic':'Edda','personality_note':'','next_step':'','reading_summary':'',
            'answer_status':'not_applicable','left_open':'','thread_followed':'none','promise_kept':'none','adjustment':''},1
    app.model_call=reflect_model;assert app.reflect(m)
    p,s=asked[0];assert 'I said: “Hello.”' in p and 'valence' not in s['properties'] and 'how_it_felt' in s['properties']
    a=st['appraisals'][-1];assert a['valence']==.6 and a['importance']==.65 and a['enjoyment']==1
    # Asleep: a dream and who he is, in his own words.
    app.model_call=lambda p,s,l,*a:({'dream':'I was carrying crates that turned into birds.','who_i_am':'I am a careful, curious elf who likes the woods.'},1)
    app.dream_and_self();assert st['dreams'][-1]['text'].startswith('I was carrying') and 'curious elf' in st['self_portrait']['text']
    seen.clear();app.model_call=lambda p,s,l,*a:(seen.append((p,s)) or ({'action':'rest','intention':'rest','reason':'tired','next_step':'','wish':'','wish_reason':'','project':'none','which_project':''},1))
    app.choose_action();assert 'Last night I dreamt: I was carrying crates' in seen[0][0] and 'curious elf' in seen[0][0]
    # Stand-in hours are marked and kept out of his own voice.
    app.event('Finished a quiet rest in his cabin.','The body reports...',action='rest');st['memories'][-1]['stand_in']=True
    st['diary'].append({'at':st['clock']['iso'],'text':'neutral','stand_in':True})
    assert all(not t.get('stand_in') for t in app.inner_extras()['thoughts'])
# Dozing: when his mind is out of reach he dozes and his world waits; no local stand-in is asked.
with tempfile.TemporaryDirectory() as td:
    folder=Path(td);shutil.copy(ROOT/'crow.py',folder/'crow.py')
    (folder/'crow-config.json').write_text(json.dumps({'model_provider':'anthropic','anthropic_api_key':'sk-test','daily_budget_usd':1.0}))
    spec=importlib.util.spec_from_file_location('crow_doze',folder/'crow.py');app=importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(app)
    def down(*a,**k):raise RuntimeError('Anthropic HTTP 400: credit balance too low')
    app.anthropic_call=down;asked=[]
    app.ollama_call=lambda *a,**k:asked.append(1)
    try:app.model_call('x',app.fields_schema({'a':app.STRING}),50,'test');raise AssertionError('should doze')
    except app.MindAway:pass
    assert not asked
print('PASS v0.30: first-person life with no machinery; feelings in words; dreams and who he is; dozing, never a stand-in.')
# v0.30.1: a stretch of the same thing is one memory; near-repeats shown once; nothing cut mid-word; stray numbers gone.
r=inner.runs([{'time':'00:26','event':'Finished a quiet rest in his cabin.'},{'time':'00:45','event':'Finished a quiet rest in his cabin.'},
              {'time':'01:04','event':'Finished a quiet rest in his cabin.'},{'time':'01:10','event':'Drank 0.40 litres from the spring basin.'}])
assert r==['00:26–01:04 I finished a quiet rest in my cabin, again and again (3 times).','01:10 I drank 0.40 litres from the spring basin.'], r
assert len(inner.distinct(['Woodland Plant Sculpture','woodland plant interactions sculpture','RootWeb Sculpture (Day 6)'],overlap=.75))==2
assert inner.clip('make another copy attempt likely to s',30).endswith('…') and 'likely to s' not in inner.clip('make another copy attempt likely to s',30)
assert '115' not in inner.tidy('the cord bundle check promises (115–120) remain')
print('PASS v0.30.1: runs remembered as one; near-repeats once; clean cuts; no stray numbers.')
