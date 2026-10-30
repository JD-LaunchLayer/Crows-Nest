import importlib.util,json,pathlib,shutil,tempfile,threading,urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
src=pathlib.Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(src))
with tempfile.TemporaryDirectory() as temp:
 d=pathlib.Path(temp)
 for f in ['crow.py','index.html','world.js']:shutil.copy(src/f,d/f)
 shutil.copytree(src/'vendor',d/'vendor')
 old={'day':4,'materials':6,'objects':['old carving'],'skills':{'archery':7,'craft':2},'decisions':42,'memories':[{'day':2,'time':'12:00','event':'Explored the woods.','reason':'Curious.'}]}
 (d/'crow-save.json').write_text(json.dumps(old))
 spec=importlib.util.spec_from_file_location('crow03',d/'crow.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 assert json.loads((d/'crow-save-before-v0.4.json').read_text())==old
 assert m.state['memories'][0]['legacy_time'] and m.state['materials']==6
 tz=ZoneInfo('Europe/London')
 m.clock(datetime(2026,10,28,23,15,0,tzinfo=tz));assert m.state['clock']['night'] and m.state['daylight']==0
 m.clock(datetime(2026,6,15,13,15,0,tzinfo=tz));assert m.state['daylight']>.9
 def decision(action):return {'action':action,'reason':'I want to try this.','intention':'Make a collection.','wish':'','wish_reason':'','library_query':'Wood carving','creation_name':'A small bowl','creation_shape':'bowl','project_id':0,'project_title':'Make two carvings','project_status':'active','target_action':'craft','target_sessions':2}
 m.CLOCK_OVERRIDE=lambda:datetime(2026,10,28,12,0,0,tzinfo=tz)  # daylight, so outdoor work runs at normal pace
 m.state['paused']=False
 m.start_action(decision('craft'),1.2)
 assert m.state['materials']==6 and m.state['pending']['remaining']==2700
 m.tick(60);assert m.state['pending']['remaining']==2640 and m.state['materials']==6
 m.state['paused']=True;m.tick(100);assert m.state['pending']['remaining']==2640
 m.state['paused']=False;m.tick(2640);memory=m.finish_action()
 assert m.state['materials']==5 and m.state['projects'][0]['progress']==1 and m.state['creations'][0]['shape']=='bowl'
 dd=decision('craft');dd['project_id']=1;m.start_action(dd,1);m.tick(2700);m.finish_action();assert m.state['projects'][0]['status']=='completed'
 result={'feeling':'I am pleased with this small improvement.','lesson':'I like working carefully with wood.','topic':'wood carving','enjoyment':2,'personality_note':'I may enjoy patient craftwork.'}
 result.update({k:1 for k in ['joy_delta','calm_delta','curiosity_delta','frustration_delta','loneliness_delta']})
 original=m.model_call;m.model_call=lambda *a,**k:(result,1)
 m.reflect(memory);assert m.state['long_term'][-1]['source_id']==memory['id'];assert m.state['interests']['wood carving']==2
 m.model_call=original
 read=decision('read');read['project_title']='';read['project_id']=0
 source={'query':'Wood carving','title':'Wood carving','url':'https://en.wikipedia.org/wiki/Wood_carving','text':'Wood carving is a form of woodworking.','retrieved':'2026-10-28'}
 m.start_action(read,1,source);m.tick(900);mem=m.finish_action();assert mem['source']['title']=='Wood carving';assert list((d/'crow-reading').glob('*.json'))
 # Wikipedia transport contract using realistic API responses, without trusting model-generated text.
 oldopen=m.urllib.request.urlopen
 class Reply:
  def __init__(self,obj):self.obj=obj
  def __enter__(self):return self
  def __exit__(self,*a):pass
  def read(self,*a):return json.dumps(self.obj).encode()
 def fake(req,timeout):
  if 'list=search' in req.full_url:return Reply({'query':{'search':[{'pageid':123,'title':'Wood carving'}]}})
  return Reply({'query':{'pages':[{'title':'Wood carving','fullurl':source['url'],'extract':source['text']}]}})
 m.urllib.request.urlopen=fake;assert m.wikipedia('Wood carving')['text']==source['text'];m.urllib.request.urlopen=oldopen
 server=m.ThreadingHTTPServer(('127.0.0.1',0),m.Handler);threading.Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(server.server_port)
 for path in ['/','/world.js','/vendor/three.module.js','/api/state']:
  with urllib.request.urlopen(base+path) as r:assert r.status==200;r.read()
 with urllib.request.urlopen(base+'/api/state') as r:assert json.load(r)['clock']['timezone']=='Europe/London'
 server.shutdown()
 print('PASS: migration/backup, UK clock and seasonal daylight, real-duration effects, pause, projects, grounded reflections, Wikipedia contract/cache, HTTP interface.')
