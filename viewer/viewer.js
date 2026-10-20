import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
const $=id=>document.getElementById(id), host=$('canvas-host'), status=$('loading'), controlsField=$('controls');
const fields=Object.fromEntries(['toilet','dog','door','explode','fronts','top','envelopes','dimensions'].map(id=>[id,$(id)]));
const state={toilet:0,dog:0,door:0,explode:0,fronts:true,top:true,envelopes:true,dimensions:false};
const frontNames=new Set(['tank_access_door','sink_service_front','toilet_hinged_door','dog_front','drawer_1_front','drawer_2_front','upper_fixed_front','toe_kick_left_panel','toilet_kick_panel']);
const colors={wood:0xcba978,top:0x3d4d49,hardware:0x758078,toilet:0xcbd9d2,tank:0x76a79f,sink:0x97b3b5};
let scene,renderer,camera,orbit,dimensionsGroup,model,target,selected=null,records=[],frame=0,stopped=false,lastPointer;
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
const inch=v=>`${Number(v.toFixed(2))}″`, title=v=>v.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
function fail(message){status.hidden=false;status.classList.add('error');status.querySelector('strong').textContent='The model could not be displayed';status.querySelector('span:last-child').textContent=message;controlsField.disabled=true;}
function geometryFor(part){
 if(!Array.isArray(part.positions)||part.positions.length%3||!part.positions.every(Number.isFinite)||!Array.isArray(part.indices)||part.indices.length%3||!part.indices.every(i=>Number.isInteger(i)&&i>=0&&i<part.positions.length/3))throw Error('A model part contains invalid geometry.');
 const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(part.positions,3));geo.setIndex(part.indices);geo.computeVertexNormals();return geo;
}
function addPart(part,index){
 const envelope=['toilet','tank','sink'].includes(part.kind),geo=geometryFor(part);
 const material=new THREE.MeshStandardMaterial({color:colors[part.kind]??colors.wood,roughness:part.kind==='top'?.62:.84,metalness:part.kind==='hardware'?.3:0,transparent:envelope,opacity:envelope?.22:1,depthWrite:!envelope,side:THREE.DoubleSide,flatShading:true});
 const mesh=new THREE.Mesh(geo,material);mesh.castShadow=!envelope;mesh.receiveShadow=!envelope;
 const group=new THREE.Group(),pivot=part.moving==='door'?new THREE.Vector3(model.dimensions[0]-.0625,0,0):new THREE.Vector3();
 geo.translate(-pivot.x,-pivot.y,-pivot.z);group.position.copy(pivot);group.add(mesh);
 let edgeGeo;
 if(Array.isArray(part.edges)&&part.edges.length&&part.edges.every(Number.isFinite)){edgeGeo=new THREE.BufferGeometry();edgeGeo.setAttribute('position',new THREE.Float32BufferAttribute(part.edges,3));edgeGeo.translate(-pivot.x,-pivot.y,-pivot.z);}else{edgeGeo=new THREE.EdgesGeometry(geo,28);}
 const edges=new THREE.LineSegments(edgeGeo,new THREE.LineBasicMaterial({color:envelope?0x618d87:0x655c48,transparent:true,opacity:envelope?.6:.25,depthTest:part.kind!=='sink'}));
 if(part.kind==='sink')edges.renderOrder=5;group.add(edges);scene.add(group);
 const direction=new THREE.Vector3(...part.center).sub(new THREE.Vector3(model.dimensions[0]/2,model.dimensions[1]/2,model.dimensions[2]/2));direction.set(direction.x/Math.max(1,model.dimensions[0]/2),direction.y/Math.max(1,model.dimensions[1]/2),direction.z/Math.max(1,model.dimensions[2]/2));
 const record={part,group,mesh,edges,pivot,direction,envelope,index};mesh.userData.record=record;records.push(record);
 const option=document.createElement('option');option.value=String(index);option.textContent=title(part.name);$('part-select').append(option);
}
function select(record){
 if(selected){selected.edges.material.color.setHex(selected.envelope?0x618d87:0x655c48);selected.edges.material.opacity=selected.envelope?.6:.25;selected.mesh.material.emissive.setHex(0);selected.edges.material.depthTest=selected.part.kind!=='sink';selected.edges.renderOrder=selected.part.kind==='sink'?5:0;}
 selected=record;$('part-select').value=record?String(record.index):'';
 if(!record){$('part-name').textContent='Select a part';$('part-size').textContent='Click the cabinet to see part dimensions.';return;}
 record.edges.material.color.setHex(0xb87828);record.edges.material.opacity=1;record.edges.material.depthTest=false;record.edges.renderOrder=6;record.mesh.material.emissive.setHex(0x211607);
 $('part-name').textContent=title(record.part.name);$('part-size').textContent=`${record.part.size.map(inch).join(' × ')} (W × D × H)`+(record.envelope?' · Reserved component space':'');
}
function sync(){
 if(state.toilet>0&&state.door<90)state.door=95;
 for(const key of ['toilet','dog','door','explode']){fields[key].value=state[key];$(`${key}-value`).textContent=key==='door'?`${state[key]}°`:inch(state[key]);}
 for(const key of ['fronts','top','envelopes','dimensions'])fields[key].checked=state[key];
 const stowed=state.toilet===0&&state.dog===0&&state.door===0,deployed=state.toilet===Number(fields.toilet.max)&&state.dog===Number(fields.dog.max)&&state.door===95;
 $('stowed').classList.toggle('active',stowed);$('deployed').classList.toggle('active',deployed);$('stowed').setAttribute('aria-pressed',String(stowed));$('deployed').setAttribute('aria-pressed',String(deployed));
 for(const record of records){const {part,group,pivot,direction,envelope}=record;group.visible=(!frontNames.has(part.name)||state.fronts)&&(part.kind!=='top'||state.top)&&(!envelope||state.envelopes);group.position.copy(pivot).addScaledVector(direction,state.explode);group.rotation.z=part.moving==='door'?THREE.MathUtils.degToRad(state.door):0;if(part.moving==='toilet')group.position.y-=state.toilet;if(part.moving==='dog')group.position.y-=state.dog;}
 dimensionsGroup.visible=state.dimensions;if(selected&&!selected.group.visible)select(null);
}
function labelSprite(text){const canvas=document.createElement('canvas');canvas.width=512;canvas.height=128;const ctx=canvas.getContext('2d');ctx.fillStyle='#f9f7f0';ctx.fillRect(0,0,512,128);ctx.fillStyle='#53634f';ctx.textAlign='center';ctx.textBaseline='middle';ctx.font='500 44px sans-serif';ctx.fillText(text,256,65);const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,depthTest:false,transparent:true}));sprite.scale.set(7.3,1.825,1);sprite.renderOrder=10;return sprite;}
function addDimension(start,end,text,labelPosition){const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...start),new THREE.Vector3(...end)]),new THREE.LineBasicMaterial({color:0x8a967f,transparent:true,opacity:.8}));dimensionsGroup.add(line);const label=labelSprite(text);label.position.set(...labelPosition);dimensionsGroup.add(label);}
function makeDimensions(){const [w,d,h]=model.dimensions;dimensionsGroup=new THREE.Group();addDimension([0,-4,.1],[w,-4,.1],`${inch(w)} W`,[w/2,-4,.2]);addDimension([w+3,0,.1],[w+3,d,.1],`${inch(d)} D`,[w+3,d/2,.2]);addDimension([w+4,d,0],[w+4,d,h],`${inch(h)} H`,[w+4,d,h/2]);scene.add(dimensionsGroup);}
function setView(view){const [w,d,h]=model.dimensions;target.set(w/2,d/2-4,h/2);const distance=Math.max(w,d,h)*2.7;camera.up.set(0,0,1);if(view==='front'){camera.position.set(w/2,-distance,h/2);}else if(view==='top'){camera.position.set(w/2,target.y-.01,distance+h);}else{const scale=host.clientWidth<600?.73:1;camera.position.set(w/2+50*scale,(d/2-4)-85*scale,h/2+43*scale);}orbit.target.copy(target);camera.lookAt(target);orbit.update();for(const b of document.querySelectorAll('[data-view]'))b.setAttribute('aria-pressed',String(b.dataset.view===view));}
function wireControls(){
 for(const [key,field] of Object.entries(fields))field.addEventListener('input',()=>{state[key]=field.type==='checkbox'?field.checked:Number(field.value);sync();});
 $('stowed').addEventListener('click',()=>{Object.assign(state,{toilet:0,dog:0,door:0});sync();});$('deployed').addEventListener('click',()=>{Object.assign(state,{toilet:Number(fields.toilet.max),dog:Number(fields.dog.max),door:95});sync();});
 $('reset').addEventListener('click',()=>{Object.assign(state,{toilet:0,dog:0,door:0,explode:0,fronts:true,top:true,envelopes:true,dimensions:false});select(null);sync();setView('iso');});
 $('part-select').addEventListener('change',event=>{const record=event.target.value===''?null:records[Number(event.target.value)];if(record&&!record.group.visible){if(frontNames.has(record.part.name))state.fronts=true;if(record.part.kind==='top')state.top=true;if(record.envelope)state.envelopes=true;sync();}select(record);});
 for(const b of document.querySelectorAll('[data-view]'))b.addEventListener('click',()=>setView(b.dataset.view));
 renderer.domElement.addEventListener('pointerdown',e=>{lastPointer={x:e.clientX,y:e.clientY,button:e.button};});
 renderer.domElement.addEventListener('pointerup',e=>{if(!lastPointer||lastPointer.button!==0||Math.hypot(e.clientX-lastPointer.x,e.clientY-lastPointer.y)>5)return;const box=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-box.left)/box.width*2-1,-(e.clientY-box.top)/box.height*2+1);raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(records.filter(r=>r.group.visible).map(r=>r.mesh),false)[0];select(hit?.object.userData.record??null);});
 renderer.domElement.addEventListener('pointercancel',()=>{lastPointer=null;});
}
function resize(){const {width,height}=host.getBoundingClientRect();if(!width||!height)return;renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();}
async function init(){try{
 const response=await fetch('./model.json',{credentials:'same-origin'});if(!response.ok)throw Error('Model data is unavailable. Rebuild the viewer and reload this page.');model=await response.json();
 if(!Array.isArray(model.parts)||!model.parts.length||!Array.isArray(model.dimensions)||model.dimensions.length!==3||!model.dimensions.every(n=>Number.isFinite(n)&&n>0))throw Error('The model data is incomplete. Rebuild the viewer and reload this page.');
 try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});}catch{throw Error('This browser could not start WebGL. Enable hardware acceleration or open the viewer in another browser.');}
 renderer.setClearColor(0xeeeae2);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
 renderer.domElement.setAttribute('aria-label','Cabinet model. Drag to orbit and scroll to zoom. Use camera buttons and part selector for keyboard controls.');renderer.domElement.setAttribute('role','img');host.append(renderer.domElement);
 renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();stopped=true;cancelAnimationFrame(frame);fail('The graphics connection was interrupted. Reload this page to restore the model.');});
 scene=new THREE.Scene();scene.fog=new THREE.Fog(0xeeeae2,160,300);scene.add(new THREE.HemisphereLight(0xfffcf4,0x90977b,2.4));
 const key=new THREE.DirectionalLight(0xfff4df,3.3);key.position.set(-25,-45,90);key.castShadow=true;key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-65,right:65,top:65,bottom:-65,near:1,far:220});key.shadow.normalBias=.08;key.shadow.bias=-.00025;key.target.position.set(15,4,10);scene.add(key,key.target);
 const fill=new THREE.DirectionalLight(0xe0ebe8,1.4);fill.position.set(55,45,50);scene.add(fill);
 const floor=new THREE.Mesh(new THREE.PlaneGeometry(600,600),new THREE.MeshStandardMaterial({color:0xeeeae2,roughness:1}));floor.position.z=-.12;floor.receiveShadow=true;scene.add(floor);
 const grid=new THREE.GridHelper(140,28,0xc6ccbd,0xd9dcd1);grid.rotation.x=Math.PI/2;grid.position.set(15,0,-.1);grid.material.transparent=true;grid.material.opacity=.34;scene.add(grid);
 camera=new THREE.PerspectiveCamera(37,1,.1,500);camera.up.set(0,0,1);target=new THREE.Vector3();orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;orbit.dampingFactor=.08;orbit.minDistance=25;orbit.maxDistance=190;orbit.maxPolarAngle=Math.PI*.49;orbit.screenSpacePanning=true;
 model.parts.forEach(addPart);makeDimensions();const [w,d,h]=model.dimensions;$('width-value').textContent=inch(w);$('depth-value').textContent=inch(d);$('height-value').textContent=inch(h);
 if(Number.isFinite(model.parameters?.toilet_travel))fields.toilet.max=String(model.parameters.toilet_travel);if(Number.isFinite(model.parameters?.dog_travel))fields.dog.max=String(model.parameters.dog_travel);
 wireControls();sync();setView('iso');const observer=new ResizeObserver(resize);observer.observe(host);resize();window.addEventListener('resize',resize);controlsField.disabled=false;status.hidden=true;
 window.__cabinetViewer=Object.freeze({getState:()=>({...state,partCount:records.length,selected:selected?.part.name??null}),getPart:name=>{const r=records.find(r=>r.part.name===name);if(!r)return null;scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);const center=new THREE.Vector3(...r.part.center).sub(r.pivot).applyMatrix4(r.group.matrixWorld);const projected=center.clone().project(camera);return {name,visible:r.group.visible,position:r.group.position.toArray(),rotation:r.group.rotation.z,center:center.toArray(),screen:projected.toArray(),size:[...r.part.size]};},setView});
 function render(){if(stopped)return;orbit.update();renderer.render(scene,camera);frame=requestAnimationFrame(render);}render();
 }catch(error){fail(error instanceof Error?error.message:'Reload the page to try again.');}}
init();
