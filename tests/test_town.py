"""Café, trading post and unexplained decorations: real rules, honest results, safe web access."""
import copy, importlib.util, json, shutil, sys, tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import town, web, world_state, life, ecology
TZ=ZoneInfo('Europe/London')

s={'materials':7,'stone':0,'creations':[]};world_state.ensure(s);life.ensure(s);town.ensure(s)
objs=s['built_world']['objects']
for i in ['internet_cafe','trading_post','weathered_figure','bronze_dial','stone_ring','hanging_tubes']:assert i in objs
before=copy.deepcopy(objs);town.ensure(s);assert objs==before, 'added once only'
# Decorations describe what can be seen, never what they are for.
for i in ['weathered_figure','bronze_dial','stone_ring','hanging_tubes']:
    text=' '.join(objs[i]['details']).lower()
    assert not any(w in text for w in ['sundial','clock','tells the time','hare','calendar','solstice','wind chime']), i
noon=datetime(2026,6,21,13,0,tzinfo=TZ);evening=datetime(2026,6,21,17,0,tzinfo=TZ)
assert 'XII' in town.inspect(s,'bronze_dial',noon,.9)['text'] and 'IV' in town.inspect(s,'bronze_dial',evening,.6)['text']
assert 'Too dark' in town.inspect(s,'weathered_figure',noon,0)['text']
# Trading at posted rates.
assert not town.trade(s,'buy','lantern',1,'t')['success']
r=town.trade(s,'sell','wood',3,'t');assert r['success'] and s['trading']['credit']==2 and s['materials']==1
assert town.trade(s,'job','carry_crates',1,'t')['success'] and s['trading']['credit']==4
pantry=s['provisions']['pantry'];assert town.trade(s,'buy','provisions_bundle',1,'t')['success'] and s['provisions']['pantry']==pantry+4
r=town.trade(s,'ask','a sketchbook and some charcoal',1,'t');town.trade(s,'ask','A sketchbook and some charcoal',1,'t')
assert s['trading']['requests'][0]['times']==2 and 'Nothing appears' in r['text']
s['creations'].append({'id':1,'name':'Small orb','shape':'orb','quality':8});world_state.ensure(s)
credit=s['trading']['credit'];assert town.trade(s,'sell','carving-1',1,'t')['success'] and 'carving-1' not in objs and s['trading']['credit']==credit+3
assert not town.trade(s,'sell','weathered_figure',1,'t')['success'], 'cannot sell the decorations'
# Jordan restocks via an orders file; bad effects are ignored.
with tempfile.TemporaryDirectory() as td:
    (Path(td)/town.ORDERS).write_text(json.dumps([{'id':'sketchbook','name':'Sketchbook','price':5,'qty':2,'effect':'possession:sketchbook'},
                                                  {'id':'magic','name':'Wand','price':1,'qty':1,'effect':'grant:everything'}]))
    done=town.apply_stock_orders(s,Path(td),'t');assert len(done)==1 and s['trading']['stock']['sketchbook']['qty']==2 and not (Path(td)/town.ORDERS).exists()
# Owned tools have real, bounded effects: a whetstone narrows carving error; a lantern allows a little detail at night.
def attempt(st):
    d={'attempt':{'support':'bench','passes':'light','direction':'along','target_error_mm':10},'creation_shape':'orb','intention':''}
    return life.practical_attempt(copy.deepcopy(st),d,600)['actual_error_mm']
plain=attempt(s);s['possessions']['whetstone']=1;assert attempt(s)<plain
dark=ecology.observe(s,'grove','',302,0);assert dark['dark']
lit=ecology.observe(s,'grove','',302,0,lamp=True);assert lit['findings'] and len(lit['findings'])<=2

# Web safety: only public internet addresses, ordinary ports and schemes.
for bad in ['http://127.0.0.1:8765/api/state','http://192.168.0.227/','http://localhost/','file:///etc/passwd','ftp://example.com/','http://10.0.0.5/','http://example.com:22/']:
    try:web.public_url(bad);raise AssertionError('allowed '+bad)
    except web.Refused:pass
ddg='''<a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.org%2Fivy&amp;rut=x">Ivy &amp; insects</a>
<a class="result__snippet" href="x">Ivy flowers <b>feed</b> late insects.</a>
<a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.net%2Fb">Second</a>'''
page='<html><title>Ivy and pollinators</title><nav>menu</nav><article><p>'+('Ivy flowers in autumn and feeds insects. '*20)+'</p><a href="/more">More about ivy</a><a href="https://other.example/x">Elsewhere</a></article></html>'
orig=web._get
web._get=lambda url,data=None,headers=None:(ddg,'text/html','https://html.duckduckgo.com/html/')
res=web.search('ivy insects');assert res[0]=={'title':'Ivy & insects','url':'https://example.org/ivy','snippet':'Ivy flowers feed late insects.'} and len(res)==2
web._get=lambda url,data=None,headers=None:(page,'text/html; charset=utf-8','https://example.org/ivy')
p=web.read('https://example.org/ivy');assert p['title']=='Ivy and pollinators' and 'menu' not in p['text'] and p['links'][0]['url']=='https://example.org/more'
web._get=orig

# Crow integration: browsing reads a real page through his own choices; trading takes time and changes credit.
with tempfile.TemporaryDirectory() as td:
    shutil.copy(ROOT/'crow.py',Path(td)/'crow.py')
    spec=importlib.util.spec_from_file_location('crow_town_test',Path(td)/'crow.py');app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    app.CLOCK_OVERRIDE=lambda:datetime(2026,11,1,12,0,tzinfo=TZ);app.state['paused']=False
    app.web.search=lambda q,settings=None:[{'title':'Ivy & insects','url':'https://example.org/ivy','snippet':'...'}]
    app.web.read=lambda url:{'title':'Ivy and pollinators','url':url,'text':'Ivy flowers feed insects in autumn. '*30,'links':[]}
    base={'reason':'I want to know.','intention':'Learn what visits ivy','next_step':'','wish':'','wish_reason':'','project':'none','project_id':0,'memory_ids_used':[]}
    def model(prompt,schema,limit,purpose):
        if 'action' in schema['properties']:return {**base,'action':model.action},1
        if purpose=='select_web':return {'choice':1,'reason':'Looks relevant.'},1
        if purpose=='parameters:browse':return {'library_query':'ivy insects autumn','research_question':'What visits ivy flowers?'},1
        if purpose=='parameters:trade':return {'trade_mode':'job','trade_item':'sweep_post','trade_quantity':1},1
        return {},1
    app.model_call=model;model.action='browse'
    d=app.decide_and_start(app.runtime['generation']);assert d and app.state['pending']['reading']['kind']=='web'
    app.tick(app.state['pending']['remaining']);m=app.finish_action()
    assert m['event'].startswith('Read a web page at the café') and app.state['reading_log'][-1]['mode']=='web'
    app.web.search=lambda q,settings=None:(_ for _ in ()).throw(app.web.Refused('The search page refused an automated visitor.'))
    assert app.decide_and_start(app.runtime['generation']) is None and app.state['memories'][-1]['kind']=='research_feedback'
    model.action='trade';app.decide_and_start(app.runtime['generation'])
    assert app.state['pending']['remaining']==30*60
    app.tick(1800);m=app.finish_action();assert app.state['trading']['credit']==1 and 'posted job' in m['event']
print('PASS: café, post and decorations added once; details without explanations; dial shadow follows time; posted-rate buying, selling, jobs '
      'and requests; Jordan restocking; real tool effects; lantern light; web address safety; search and page parsing; browse and trade in his life.')
