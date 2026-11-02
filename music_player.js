// Plays Crow's harp music in the browser: a plucked-string sound made with the Web Audio API.
// Nothing here changes his world; it only makes what he played audible. Sound starts only after
// the viewer turns it on (browsers block sound until someone clicks).
export function createPlayer(){
 let ctx=null,timer=null,playingKey='',enabled=false;
 function audio(){ctx??=new (globalThis.AudioContext||globalThis.webkitAudioContext)();if(ctx.state==='suspended')ctx.resume();return ctx}
 function pluck(ac,midi,when,length,volume){
  const f=440*Math.pow(2,(midi-69)/12),out=ac.createGain(),tone=ac.createBiquadFilter();
  tone.type='lowpass';tone.frequency.setValueAtTime(Math.min(8000,f*7),when);tone.frequency.exponentialRampToValueAtTime(Math.max(300,f*1.5),when+Math.min(1.8,length+.6));
  out.gain.setValueAtTime(0,when);out.gain.linearRampToValueAtTime(volume,when+.004);out.gain.exponentialRampToValueAtTime(.0008,when+Math.min(2.6,length+1.2));
  // A harp string: a fundamental with a few soft overtones that die away faster.
  for(const [mult,amp,type] of [[1,1,'triangle'],[2,.35,'sine'],[3,.12,'sine']]){
   const o=ac.createOscillator(),g=ac.createGain();o.type=type;o.frequency.setValueAtTime(f*mult,when);g.gain.value=amp;
   o.connect(g).connect(tone);o.start(when);o.stop(when+Math.min(2.8,length+1.4));
  }
  tone.connect(out).connect(ac.destination);
 }
 // notes: [[midi|null, beats], ...]; tempo in beats a minute. Returns the length in seconds.
 function play(notes,tempo,{volume=.18}={}){
  const ac=audio(),beat=60/Math.max(30,tempo||80);let t=ac.currentTime+.08;
  for(const [n,b] of notes){if(n!=null)pluck(ac,n,t,b*beat,volume);t+=b*beat;}
  return t-ac.currentTime;
 }
 function stop(){clearTimeout(timer);timer=null;playingKey='';if(ctx){ctx.close();ctx=null}}
 // While he is playing, his performance repeats softly (like hearing him from nearby).
 function follow(state){
  const m=state?.pending?.decision?.action==='play_music'?state.pending.music:null;
  const key=m&&m.performance?`${state.pending.start}:${m.piece_id}`:'';
  if(!enabled||!key){if(playingKey&&!key){clearTimeout(timer);timer=null;playingKey=''}return}
  if(key===playingKey)return;playingKey=key;clearTimeout(timer);
  const loop=()=>{if(playingKey!==key)return;const seconds=play(m.performance.played,m.tempo,{volume:.12});timer=setTimeout(loop,(seconds+2.5)*1000)};loop();
 }
 function setEnabled(on){enabled=on;if(!on)stop();else audio();}
 return {play,stop,follow,setEnabled,get enabled(){return enabled}};
}
