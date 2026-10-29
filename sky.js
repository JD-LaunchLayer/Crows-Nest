// Local ephemeris calculations. The world uses Wickford, UK; +X east, -Z north.
export function celestialState(date, astronomy = globalThis.Astronomy, latitude = 51.61, longitude = .52) {
  const observer = new astronomy.Observer(latitude, longitude, 15);
  const position = body => {
    const eq = astronomy.Equator(body, date, observer, true, true);
    return astronomy.Horizon(date, observer, eq.ra, eq.dec, 'normal');
  };
  return {sun: position('Sun'), moon: position('Moon'), phase: astronomy.MoonPhase(date),
    sidereal: astronomy.SiderealTime(date), date: date.toISOString()};
}

export function horizonVector(altitude, azimuth) {
  const a = altitude * Math.PI / 180, z = azimuth * Math.PI / 180;
  return {x: Math.cos(a) * Math.sin(z), y: Math.sin(a), z: -Math.cos(a) * Math.cos(z)};
}

export function createSky({T,scene,camera,sun,skyLight}) {
  const root = new T.Group();scene.add(root);
  const uniforms={zenith:{value:new T.Color('#7cabc4')},horizon:{value:new T.Color('#d0d9c4')},sunDirection:{value:new T.Vector3(0,1,0)},twilight:{value:0}};
  const dome=new T.Mesh(new T.SphereGeometry(85,24,12),new T.ShaderMaterial({side:T.BackSide,depthWrite:false,uniforms,
    vertexShader:'varying vec3 direction;void main(){direction=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
    fragmentShader:'varying vec3 direction;uniform vec3 zenith;uniform vec3 horizon;uniform vec3 sunDirection;uniform float twilight;void main(){vec3 d=normalize(direction);float h=pow(max(0.0,d.y),0.45);vec3 c=mix(horizon,zenith,h);float glow=pow(max(0.0,dot(d,normalize(vec3(sunDirection.x,0.12,sunDirection.z)))),12.0)*(1.0-h)*twilight;c+=vec3(0.7,0.24,0.06)*glow;gl_FragColor=vec4(c,1.0);}' }));
  dome.renderOrder=-100;root.add(dome);
  const solar=new T.Mesh(new T.SphereGeometry(.42,12,8),new T.MeshBasicMaterial({color:'#fff1c5',fog:false}));root.add(solar);
  const lunar=new T.Mesh(new T.PlaneGeometry(1.0,1.0),new T.ShaderMaterial({transparent:true,depthWrite:false,
    uniforms:{lightDirection:{value:new T.Vector3(1,0,0)}},
    vertexShader:'varying vec2 uv0;void main(){uv0=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
    fragmentShader:'varying vec2 uv0;uniform vec3 lightDirection;void main(){vec2 q=uv0*2.0-1.0;float r=dot(q,q);if(r>1.0)discard;vec3 n=vec3(q,sqrt(1.0-r));float lit=max(0.0,dot(n,normalize(lightDirection)));float detail=0.88+0.08*sin(q.x*29.0)*sin(q.y*37.0);vec3 c=vec3(0.026,0.032,0.042)+vec3(0.86,0.86,0.79)*lit*detail;gl_FragColor=vec4(c,1.0);}' }));root.add(lunar);
  const coords=[];for(let i=0;i<700;i++){const y=1-2*(i+.5)/700,a=i*2.399963,r=Math.sqrt(1-y*y);coords.push(79*r*Math.cos(a),79*y,79*r*Math.sin(a))}
  const starGeometry=new T.BufferGeometry();starGeometry.setAttribute('position',new T.Float32BufferAttribute(coords,3));
  const stars=new T.Points(starGeometry,new T.PointsMaterial({color:'#e4ecff',size:.12,transparent:true,opacity:0,depthWrite:false,fog:false}));stars.renderOrder=-40;root.add(stars);
  let data=null,lastTime=0;const sunDirection=new T.Vector3(),moonDirection=new T.Vector3();
  function update(date){
    if(data&&Math.abs(date.getTime()-lastTime)<15000)return data;
    lastTime=date.getTime();data=celestialState(date);
    const a=horizonVector(data.sun.altitude,data.sun.azimuth),b=horizonVector(data.moon.altitude,data.moon.azimuth);
    sunDirection.set(a.x,a.y,a.z);moonDirection.set(b.x,b.y,b.z);
    solar.position.copy(sunDirection).multiplyScalar(65);lunar.position.copy(moonDirection).multiplyScalar(64);
    solar.visible=data.sun.altitude>-.8;lunar.visible=data.moon.altitude>0;
    sun.position.copy(sunDirection).multiplyScalar(40);sun.intensity=Math.max(0,Math.sin(data.sun.altitude*Math.PI/180))*3.2;
    const daylight=T.MathUtils.smoothstep(data.sun.altitude,-12,12);skyLight.intensity=.18+1.82*daylight;
    uniforms.zenith.value.set('#071021').lerp(new T.Color('#79a8c4'),daylight);
    uniforms.horizon.value.set('#111b2c').lerp(new T.Color('#d3d9bd'),daylight);
    uniforms.sunDirection.value.copy(sunDirection);uniforms.twilight.value=Math.max(0,1-Math.abs(data.sun.altitude+2)/12);
    const fogColor=uniforms.horizon.value.clone();scene.fog.color.copy(fogColor);scene.background.copy(fogColor);
    solar.material.color.set(data.sun.altitude<8?'#ffcf89':'#fff1c5');
    stars.material.opacity=1-T.MathUtils.smoothstep(data.sun.altitude,-15,-5);
    stars.rotation.set(.67,data.sidereal*Math.PI/12,0);
    return data;
  }
  function frame(){
    root.position.copy(camera.position);
    lunar.lookAt(camera.position);
    const inverse=lunar.getWorldQuaternion(new T.Quaternion()).invert();
    lunar.material.uniforms.lightDirection.value.copy(sunDirection).applyQuaternion(inverse);
  }
  return {update,frame};
}
