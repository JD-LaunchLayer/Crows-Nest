"""Cloud model with local fallback, a daily spending cap, and a key that never leaves the config."""
import importlib.util, io, json, shutil, sys, tempfile, urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
KEY='sk-ant-test-not-real'
with tempfile.TemporaryDirectory() as td:
    folder=Path(td);shutil.copy(ROOT/'crow.py',folder/'crow.py')
    (folder/'crow-config.json').write_text(json.dumps({'model_provider':'anthropic','anthropic_api_key':KEY,'daily_budget_usd':1.0}))
    spec=importlib.util.spec_from_file_location('crow_provider_test',folder/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    assert app.PROVIDER=='anthropic' and app.ANTHROPIC_MODEL=='claude-haiku-5-5' and app.CONTEXT_BUDGET>=16000
    sent=[];mode={'cloud':'ok'}
    class Reply(io.BytesIO):
        def __enter__(self):return self
        def __exit__(self,*a):pass
    def urlopen(req,timeout):
        body=json.loads(req.data);sent.append((req.full_url,body,dict(req.header_items())))
        if 'anthropic' in req.full_url:
            if mode['cloud']=='down':raise urllib.error.HTTPError(req.full_url,529,'Overloaded',{},None)
            return Reply(json.dumps({'content':[{'type':'tool_use','name':'respond','input':{'answer':'cloud'}}],
                                     'usage':{'input_tokens':1000,'output_tokens':200}}).encode())
        return Reply(json.dumps({'message':{'content':json.dumps({'answer':'local'})},'prompt_eval_count':50,'eval_count':5}).encode())
    app.urllib.request.urlopen=urlopen
    schema=app.fields_schema({'answer':{'type':'string'}})
    data,_=app.model_call('Say something.',schema,100,'test')
    url,body,headers=sent[-1]
    assert data=={'answer':'cloud'} and body['tool_choice']=={'type':'tool','name':'respond'} and body['tools'][0]['input_schema']==schema
    assert body['model']=='claude-haiku-5-5' and headers.get('X-api-key')==KEY
    ledger=app.state['model_spend'];assert abs(ledger['usd']-(1000/1e6*.10+200/1e6*.50))<1e-9 and ledger['calls']==1
    # Outage: the call falls back to the local model instead of stopping his life.
    mode['cloud']='down';data,_=app.model_call('Again.',schema,100,'test')
    assert data=={'answer':'local'} and app.state['model_spend']['fallbacks']==1 and '11434' in sent[-1][0]
    # Budget: once today's spend reaches the cap, no cloud request is even made.
    mode['cloud']='ok';app.state['model_spend']['usd']=1.0;count=len(sent)
    data,_=app.model_call('Third.',schema,100,'test')
    assert data=={'answer':'local'} and len(sent)==count+1 and '11434' in sent[-1][0]
    # A new real day resets the daily figure but keeps the running total.
    app.state['model_spend']['date']='2000-01-01';total=app.state['model_spend']['total_usd']
    app.model_call('Fourth.',schema,100,'test');assert app.state['model_spend']['usd']>0 and app.state['model_spend']['total_usd']>total
    # The key is never part of his saved life or the observer API.
    app.persist();assert KEY not in (folder/'crow-save.json').read_text() and KEY not in json.dumps(app.runtime)
print('PASS: Haiku via forced structured tool call; real token cost ledger; outage and over-budget fall back to local; daily reset; key never saved in his life.')
