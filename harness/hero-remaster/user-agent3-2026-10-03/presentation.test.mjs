import test from 'node:test';
import assert from 'node:assert/strict';
import { Group, Mesh, BoxGeometry, MeshBasicMaterial } from 'three';
import { bikeFreeAnatomyPresentation, requireActualBikeContactEvidence } from './presentation.mjs';
const mesh=()=>new Mesh(new BoxGeometry(),new MeshBasicMaterial());
await test('Bike frame may parent rider: hide siblings and shadows, preserve rider and transforms',()=>{
  const root=new Group(),frame=new Group(),bike=new Group(),rider=new Group(),body=mesh(),shadow=mesh();
  root.add(frame,shadow);frame.add(bike,rider);bike.add(mesh());rider.add(body);shadow.visible=false;
  rider.position.set(.2,.4,.6);root.updateMatrixWorld(true);const world=rider.matrixWorld.toArray();
  const fixture=bikeFreeAnatomyPresentation(root,rider);fixture.assertPresentation();root.updateMatrixWorld(true);
  assert.equal(root.visible,true);assert.equal(frame.visible,true);assert.equal(bike.visible,false);assert.equal(body.visible,true);assert.deepEqual(rider.matrixWorld.toArray(),world);
  fixture.restore();assert.equal(bike.visible,true);assert.equal(shadow.visible,false);
});
await test('Detached rider keeps visible; stale visibility changes invalidate fixture',()=>{
  const root=new Group(),rider=new Group();root.add(mesh());rider.add(mesh());
  const fixture=bikeFreeAnatomyPresentation(root,rider);assert.equal(root.visible,false);assert.equal(rider.visible,true);
  root.visible=true;assert.throws(()=>fixture.assertPresentation(),/Bike branch visible/);fixture.restore();
});
await test('Synthetic pose and four sockets cannot stand in for five visible contacts',()=>{
  assert.throws(()=>requireActualBikeContactEvidence({poseInjection:true}),/pose injection/);
  const sample={poseInjection:false,bikeVisible:true,driver:'recorded-game-input',contacts:{},phase:'riding'};
  for(const id of ['hand.L','hand.R','foot.L','foot.R'])sample.contacts[id]={status:'measured',sampleCount:4,evidence:'owned mapping',reviewAuthority:'parent'};
  assert.throws(()=>requireActualBikeContactEvidence(sample),/saddle/);
  sample.contacts.saddle={status:'measured',sampleCount:4,evidence:'reviewed pelvis/saddle surfaces',reviewAuthority:'parent'};
  assert.match(requireActualBikeContactEvidence(sample).status,/no acceptance/);
});
