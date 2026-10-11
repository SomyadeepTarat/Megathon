// Adapted from the supplied Kew London animation. UI and lifecycle belong to React.
import * as THREE from './vendor/three.module.js';

export function createJourneyScene(canvas) {
const renderer = new THREE.WebGLRenderer({canvas, antialias:true, powerPreference:'low-power'});
const smooth = (a,b,t) => THREE.MathUtils.smoothstep(t,a,b);
renderer.setPixelRatio(Math.min(window.devicePixelRatio,1.5));renderer.setClearColor('#eeeede');renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.18;
const scene=new THREE.Scene();scene.background=new THREE.Color('#eeeede');scene.fog=new THREE.Fog('#eeeede',95,200);
const camera=new THREE.PerspectiveCamera(40,1,.1,400);
scene.add(new THREE.HemisphereLight('#fff9e9','#769079',2.5));const sun=new THREE.DirectionalLight('#fff6da',3.0);sun.position.set(-40,85,45);scene.add(sun);
const material=(color,extra={})=>new THREE.MeshStandardMaterial({color,roughness:.85,metalness:0,...extra});
const ground=material('#dddcc7'),road=material('#eeeedd'),wall=material('#e8e2cd'),roof=material('#365446'),green=material('#648257'),riverMat=material('#94b6a5',{roughness:.4,metalness:.08}),gold=material('#b79e69');
function box(w,h,d,mat,x=0,y=0,z=0,parent=scene){const obj=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);obj.position.set(x,y,z);parent.add(obj);return obj;}
box(170,.25,170,ground,0,-.3,0);
const city=new THREE.Group();scene.add(city);
let randomState=127;const rnd=()=>{randomState=(randomState*16807)%2147483647;return(randomState-1)/2147483646;};
const riverX=z=>-17+9*Math.sin(z*.037);
const riverShape=new THREE.Shape();riverShape.moveTo(riverX(-82)-5,-82);for(let z=-80;z<=82;z+=2)riverShape.lineTo(riverX(z)-5,z);for(let z=82;z>=-82;z-=2)riverShape.lineTo(riverX(z)+5,z);riverShape.closePath();
riverMat.side=THREE.DoubleSide;
const water=new THREE.Mesh(new THREE.ShapeGeometry(riverShape),riverMat);water.rotation.x=Math.PI/2;water.position.y=.02;city.add(water);
for(let v=-66;v<=66;v+=12){box(140,.05,1.6,road,0,.015,v,city);box(1.6,.05,140,road,v,.025,0,city);}water.position.y=.09;
const pieces=[];
for(let x=-58;x<=58;x+=6)for(let z=-58;z<=58;z+=6){if(Math.abs(x-riverX(z))<9||Math.abs(x-18)<9&&Math.abs(z-12)<10||Math.abs(x+3)<6&&Math.abs(z+25)<10||Math.abs(x)<7&&Math.abs(z+10)<8)continue;const tall=x>26&&z<-5;const height=tall?5+rnd()*17:2+rnd()*5;pieces.push({x:x+(rnd()-.5)*.8,z:z+(rnd()-.5)*.8,h:height,w:3+rnd()*1.2,d:3+rnd()*1.2,color:new THREE.Color(['#c7c6b2','#c5cdba','#b9c0ad','#a7b6a2','#d3cdb6'][Math.floor(rnd()*5)])});}
const cityWallMat=material('#c7c6b2',{transparent:true});const blocks=new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1),cityWallMat,pieces.length);const rooftops=new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1),material('#8a9d87',{transparent:true}),pieces.length);const windows=new THREE.InstancedMesh(new THREE.BoxGeometry(1,1,1),material('#e5e4cf',{transparent:true}),pieces.length*6);const matrix=new THREE.Object3D();let wi=0;
pieces.forEach((p,i)=>{matrix.position.set(p.x,p.h/2,p.z);matrix.scale.set(p.w,p.h,p.d);matrix.rotation.set(0,0,0);matrix.updateMatrix();blocks.setMatrixAt(i,matrix.matrix);blocks.setColorAt(i,p.color);matrix.position.y=p.h+.15;matrix.scale.set(p.w+.15,.35,p.d+.15);matrix.updateMatrix();rooftops.setMatrixAt(i,matrix.matrix);for(let y=0;y<3;y++)for(let w=0;w<2;w++){matrix.position.set(p.x+(w-.5)*p.w*.5,Math.min(p.h-.4,.8+y*p.h*.26),p.z+p.d/2+.015);matrix.scale.set(.55,.55,.045);matrix.updateMatrix();windows.setMatrixAt(wi++,matrix.matrix);}});city.add(blocks,rooftops,windows);
const trunks=new THREE.InstancedMesh(new THREE.CylinderGeometry(.16,.22,1.3,5),material('#9e9e79',{transparent:true}),150);const foliage=new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1,1),material('#73946a',{transparent:true}),150);
for(let i=0;i<150;i++){let x=(rnd()-.5)*115,z=(rnd()-.5)*115;if(Math.abs(x-riverX(z))<6)x+=15;const s=.6+rnd()*.5;matrix.position.set(x,.8,z);matrix.scale.set(1,1,1);matrix.updateMatrix();trunks.setMatrixAt(i,matrix.matrix);matrix.position.y=2;matrix.scale.set(s,s*1.25,s);matrix.updateMatrix();foliage.setMatrixAt(i,matrix.matrix);}city.add(trunks,foliage);
// Recognizable London silhouettes: riverside clock tower, wheel and bridges.
const landmarks=new THREE.Group();city.add(landmarks);
for(const z of [-32,-8,22]){const x=riverX(z);box(18,.45,2.3,material('#c5c7ad'),x,.55,z,landmarks);for(const sx of [-6,6])box(.9,1.6,2.7,material('#a4b099'),x+sx,.8,z,landmarks);}
const clockTower=new THREE.Group();clockTower.position.set(-3,0,-27);landmarks.add(clockTower);box(2.4,13,2.4,gold,0,6.5,0,clockTower);box(3.1,2.2,3.1,wall,0,13.8,0,clockTower);const spire=new THREE.Mesh(new THREE.ConeGeometry(2.15,5,4),roof);spire.rotation.y=Math.PI/4;spire.position.y=17.4;clockTower.add(spire);
for(let k=0;k<4;k++){const clock=new THREE.Mesh(new THREE.CircleGeometry(.82,24),material('#f5f0d6'));clock.position.set(Math.sin(k*Math.PI/2)*1.56,14,Math.cos(k*Math.PI/2)*1.56);clock.rotation.y=k*Math.PI/2;clockTower.add(clock);const hand=box(.08,.65,.04,roof,0,.13,.015,clock);hand.rotation.z=.3;box(.6,.07,.04,roof,.23,0,.02,clock);}
for(let i=0;i<6;i++)box(2.1,4+i%2,3.6,wall,1+i*2.8,2,-29,landmarks);
const wheel=new THREE.Group();wheel.position.set(-.5,6,-9);landmarks.add(wheel);const rim=new THREE.Mesh(new THREE.TorusGeometry(5,.12,6,48),material('#f8f4df'));wheel.add(rim);for(let i=0;i<14;i++){const a=i*Math.PI*2/14;const capsule=box(.45,.65,.45,wall,Math.cos(a)*5,Math.sin(a)*5,0,wheel);const spoke=new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0,0,0),new THREE.Vector3(Math.cos(a)*5,Math.sin(a)*5,0)]),new THREE.LineBasicMaterial({color:'#d2d7bd'}));wheel.add(spoke);}box(.22,6,.22,roof,-1,-3,0,wheel);box(.22,6,.22,roof,1,-3,0,wheel);
// The destination home is kept separate from the wider city.
const home=new THREE.Group();home.position.set(18,0,12);scene.add(home);
const lawn=box(16,.13,13,material('#bac8a2'),0,.1,0,home);box(2,.16,8,road,0,.19,7,home);box(8,4.6,6,wall,0,2.4,0,home);
const roofGeo=new THREE.BufferGeometry();const verts=[-4.5,4.7,-3.5,0,7.2,-3.5,-4.5,4.7,3.5,0,7.2,-3.5,0,7.2,3.5,-4.5,4.7,3.5,0,7.2,-3.5,4.5,4.7,-3.5,0,7.2,3.5,4.5,4.7,-3.5,4.5,4.7,3.5,0,7.2,3.5,-4.5,4.7,-3.5,4.5,4.7,-3.5,0,7.2,-3.5,-4.5,4.7,3.5,0,7.2,3.5,4.5,4.7,3.5];roofGeo.setAttribute('position',new THREE.Float32BufferAttribute(verts,3));roofGeo.computeVertexNormals();const roofObj=new THREE.Mesh(roofGeo,material('#536b58',{side:THREE.DoubleSide}));home.add(roofObj);
box(1.15,2.3,.12,roof,0,1.3,3.07,home);box(.7,.14,.5,gold,0,2.5,3.1,home);
for(const x of [-2.4,2.4])for(const y of [1.5,3.55]){box(1.45,1.05,.12,material('#82988b'),x,y,3.08,home);box(1.54,.12,.22,material('#f4f2dd'),x,y-.58,3.09,home);box(.07,1.1,.17,wall,x,y,3.17,home);box(1.4,.06,.17,wall,x,y,3.17,home);}for(const z of [-1.5,1.5])box(.13,1.1,1.3,material('#799285'),4.05,2.7,z,home);
box(.85,1.5,.9,gold,2,6,0,home);
const solar=new THREE.Group();home.add(solar);const panelMat=material('#294c47',{metalness:.3,roughness:.4});
for(const x of [1.2,2.65])for(const z of [-1.9,0,1.9]){const panel=new THREE.Group();panel.position.set(x,7.2-x*2.5/4.5+.09,z);panel.rotation.z=-Math.atan(2.5/4.5);solar.add(panel);box(1.2,.09,1.6,panelMat,0,0,0,panel);for(const sx of [-.3,0,.3])box(.025,.016,1.52,material('#93b7aa'),sx,.055,0,panel);for(const sz of [-.4,0,.4])box(1.12,.016,.025,material('#93b7aa'),0,.055,sz,panel);}
const insulation=box(8.08,4.65,6.08,material('#8daf73',{transparent:true,opacity:0,depthWrite:false}),0,2.42,0,home);
const pump=new THREE.Group();pump.position.set(5,.2,1.5);home.add(pump);box(1.5,1.7,.75,material('#eeeede'),0,.85,0,pump);const fan=new THREE.Mesh(new THREE.TorusGeometry(.52,.05,8,30),roof);fan.position.set(0,.9,.4);pump.add(fan);const blades=new THREE.Group();blades.position.set(0,.9,.45);pump.add(blades);for(let i=0;i<3;i++){const blade=box(.2,.7,.035,roof,0,.12,0,blades);blade.rotation.z=i*Math.PI*2/3;}
const garden=new THREE.Group();home.add(garden);for(const [x,z,s] of [[-6,-4,1.4],[6,-4,1.7],[-6,3,.8],[5.5,4,.65]]){const tree=new THREE.Group();tree.position.set(x,0,z);garden.add(tree);box(.22,1.8,.22,material('#9b9873'),0,.9,0,tree);const crown=new THREE.Mesh(new THREE.IcosahedronGeometry(s,1),green);crown.position.y=2.6;tree.add(crown);}
const halo=new THREE.Mesh(new THREE.RingGeometry(9.1,9.17,80),new THREE.MeshBasicMaterial({color:'#718f61',side:THREE.DoubleSide,transparent:true,opacity:0}));halo.rotation.x=-Math.PI/2;halo.position.y=.2;home.add(halo);
const cameraPath=new THREE.CatmullRomCurve3([new THREE.Vector3(10,130,.01),new THREE.Vector3(36,90,53),new THREE.Vector3(42,48,49),new THREE.Vector3(37,24,37),new THREE.Vector3(28,16,30)]);
const targetPath=new THREE.CatmullRomCurve3([new THREE.Vector3(0,0,0),new THREE.Vector3(8,1,0),new THREE.Vector3(17,2,10),new THREE.Vector3(18,3,12),new THREE.Vector3(18,3,12)]);

let width = 1, height = 1;
return {
 resize(w,h) {
   width=w; height=h;
   renderer.setSize(w,h,false);
   camera.aspect=w/h;
   camera.updateProjectionMatrix();
 },
 render(p) {
   camera.position.copy(cameraPath.getPoint(p));
   const target = targetPath.getPoint(p);
   if(width<700) {
     // Pull back and frame the home below the mobile copy.
     camera.position.sub(target).multiplyScalar(1.35).add(target);
     camera.setViewOffset(width,height,0,-height*.14,width,height);
   } else camera.clearViewOffset();
   camera.lookAt(target);
   const cityOpacity=1-.76*smooth(.35,.62,p);
   [blocks,rooftops,windows,trunks,foliage].forEach(o=>o.material.opacity=cityOpacity);
   solar.scale.setScalar(Math.max(.001,smooth(.46,.57,p)));
   pump.scale.setScalar(Math.max(.001,smooth(.63,.75,p)));
   garden.scale.setScalar(.7+.3*smooth(.45,.75,p));
   blades.rotation.z=p*12;
   insulation.material.opacity=.2*(smooth(.54,.65,p)-smooth(.77,.86,p));
   halo.material.opacity=.55*smooth(.46,.7,p);
   renderer.render(scene,camera);
 },
 dispose(releaseContext = false) {
   const geometries=new Set(), materials=new Set();
   scene.traverse(object=>{
     if(object.geometry) geometries.add(object.geometry);
     if(object.material) {
       for(const material of Array.isArray(object.material)?object.material:[object.material]) materials.add(material);
     }
     if(object.isInstancedMesh) object.dispose();
   });
   geometries.forEach(geometry=>geometry.dispose());
   materials.forEach(material=>material.dispose());
   scene.clear();
   renderer.renderLists.dispose();
   renderer.dispose();
   // Retain the canvas context when changing reduced-motion preferences so the
   // same canvas can resume. Final unmount also releases the context itself.
   if (releaseContext) renderer.forceContextLoss();
 }
};
}
