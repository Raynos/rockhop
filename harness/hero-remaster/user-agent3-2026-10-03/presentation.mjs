/** Visibility-only anatomy presentation; keeps rider ancestors and physics intact. */
const ensure=(condition,message)=>{if(!condition)throw new Error(message);};
const same=(actual,expected,message)=>ensure(actual===expected,message);
const visible=node=>{for(let p=node;p;p=p.parent)if(!p.visible)return false;return true;};
const within=(node,ancestor)=>{for(let p=node;p;p=p.parent)if(p===ancestor)return true;return false;};
export function bikeFreeAnatomyPresentation(bikeRoot,riderScene){
  ensure(bikeRoot?.isObject3D&&riderScene?.isObject3D&&bikeRoot!==riderScene,'Need distinct live bike/rider objects');
  const riderNodes=new Map(), cuts=[];
  riderScene.traverse(node=>riderNodes.set(node,node.visible));
  function cut(node){
    if(node===riderScene)return;
    if(!within(riderScene,node)){cuts.push({node,visible:node.visible});node.visible=false;return;}
    for(const child of node.children)cut(child);
  }
  cut(bikeRoot);
  const assertPresentation=()=>{
    for(const {node}of cuts)same(node.visible,false,'Bike branch visible; presentation must be prepared again');
    for(const [node,visible]of riderNodes){ensure(within(node,riderScene),'Rider graph changed; prepare fresh fixture');same(node.visible,visible,'Presentation changed rider visibility');}
    for(let node=riderScene;node;node=node.parent)same(node.visible,true,'Rider ancestor hidden');
    bikeRoot.traverse(node=>{if(node.isMesh&&!within(node,riderScene))ensure(!visible(node),'Visible bike surface in anatomy fixture');});
  };
  assertPresentation();
  return{applyVisibility(){for(const {node}of cuts)node.visible=false;assertPresentation();},mode:'bike-free anatomical diagnostic',hiddenBranches:cuts.map(({node})=>node.name),assertPresentation,
    restore(){for(const {node,visible}of cuts)node.visible=visible;},
    limits:'Only visibility changes; no world transforms, skeleton, material, source geometry, physics or contact claim.'};
}
export function requireActualBikeContactEvidence(sample){
  ensure(sample?.poseInjection===false,'Actual-bike evidence cannot use authored pose injection');
  same(sample.phase,'riding','Actual bike pose must come from a riding game phase');
  ensure(sample.bikeVisible===true&&sample.driver==='recorded-game-input','Actual live bike and recorded game input required');
  for(const id of ['hand.L','hand.R','foot.L','foot.R','saddle']){
    const contact=sample.contacts?.[id];same(contact?.status,'measured','Unmeasured visible contact: '+id);
    ensure(Number.isSafeInteger(contact.sampleCount)&&contact.sampleCount>0,'Visible surface samples required: '+id);
    ensure(contact.evidence&&contact.reviewAuthority==='parent','Reviewed visible source patch/bike target required: '+id);
  }
  return{status:'measured inputs available for parent played review; no acceptance',phase:sample.phase};
}
