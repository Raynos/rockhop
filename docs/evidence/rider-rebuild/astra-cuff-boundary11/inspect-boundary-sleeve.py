"""CPU2 finite exact boundary segment intersections + vertex distances to hoodie."""
import numpy as np,json
from pathlib import Path
root=Path('/Users/raynos/projects/games/rockhop/harness/out/rider-rebuild/glove-cuff-construction07/inspection01')
r=json.load(open('/tmp/astra-cuff-boundary11-dorsal.json'));loop=r['boundaryLoops'][0];result={}
for side in ['L','R']:
 a=np.load(root/f'guide-{side}.npz');h=np.load(root/f'sleeve-{side}.npz');tri=h['worldXYZ'][h['faces']];p0,p1,p2=tri[:,0],tri[:,1],tri[:,2];e0=p1-p0;e1=p2-p0;n=np.cross(e0,e1);n2=np.sum(n*n,1)
 positions=np.array([sum(a['currentWorldXYZ'][int(i)]*w for i,w in e['start']['sourceVertexBarycentric'].items()) for e in loop]);distances=[];nearest=[];crossings=[]
 for k,p in enumerate(positions):
  # Exact point-triangle minimum, except discarded truly degenerate projected faces.
  signed=np.sum((p-p0)*n,1);q=p-signed[:,None]*n/np.maximum(n2[:,None],1e-40)
  d00=np.sum(e0*e0,1);d01=np.sum(e0*e1,1);d11=np.sum(e1*e1,1);w=q-p0;d20=np.sum(w*e0,1);d21=np.sum(w*e1,1);den=d00*d11-d01*d01
  u=(d11*d20-d01*d21)/np.maximum(den,1e-40);vv=(d00*d21-d01*d20)/np.maximum(den,1e-40);inside=(u>=0)&(vv>=0)&(u+vv<=1)&(den>1e-30)
  ds=np.where(inside,signed*signed/np.maximum(n2,1e-40),np.inf)
  for x,z in [(p0,p1),(p1,p2),(p2,p0)]:
   edge=z-x;t=np.clip(np.sum((p-x)*edge,1)/np.maximum(np.sum(edge*edge,1),1e-40),0,1);delta=p-(x+t[:,None]*edge);ds=np.minimum(ds,np.sum(delta*delta,1))
  j=int(ds.argmin());distances.append(float(np.sqrt(ds[j])));nearest.append(int(h['nativeTriangleIds'][j]))
  end=positions[(k+1)%len(positions)];direction=end-p;mask=np.all(tri.max(1)>=np.minimum(p,end)-1e-10,1)&np.all(tri.min(1)<=np.maximum(p,end)+1e-10,1);ids=np.flatnonzero(mask)
  if len(ids):
   aa=e0[ids];bb=e1[ids];cross=np.cross(np.broadcast_to(direction,aa.shape),bb);det=np.sum(aa*cross,1);valid=np.abs(det)>1e-15;iv=np.where(valid,1/np.where(valid,det,1),0);ss=p-p0[ids];uu=np.sum(ss*cross,1)*iv;qq=np.cross(ss,aa);vv=np.sum(direction*qq,1)*iv;tt=np.sum(bb*qq,1)*iv;hit=valid&(uu>1e-8)&(vv>1e-8)&(uu+vv<1-1e-8)&(tt>1e-8)&(tt<1-1e-8)
   for j in np.flatnonzero(hit):crossings.append({'boundaryEdge':k,'plane':loop[k]['plane'],'guideSourceFace':loop[k]['sourceFace'],'sleeveNativeTriangle':int(h['nativeTriangleIds'][ids[j]]),'segmentFraction':float(tt[j]),'sleeveTriangleUV':[float(uu[j]),float(vv[j])],'worldXYZ':(p+tt[j]*direction).tolist()})
 distances=np.array(distances);result[side]={'boundaryVertices':len(positions),'sleeveTriangles':len(tri),'boundaryVertexDistanceToSleeveMm':{'min':float(distances.min()*1000),'median':float(np.median(distances)*1000),'max':float(distances.max()*1000),'minimumAtBoundaryVertex':int(distances.argmin()),'minimumSleeveNativeTriangle':nearest[int(distances.argmin())]},'strictBoundarySegmentTriangleCrossings':crossings,'targetControls':[{ 'guideVertex':i,'insideWindow':bool(a['originalSourceXYZ'][i,1]<-.65 and a['originalSourceXYZ'][i,2]>0),'sourceXYZ':a['originalSourceXYZ'][i].tolist()} for i in [3384,3593,3635,4118]]}
result['limits']=['Finite boundary point distances, not continuous minimum clearance or sign/occupancy.','Strict segment-triangle tests exclude tangent/coplanar cases; any listed strict crossing is sufficient to reject a fixed retained boundary.','No patch, source or sleeve edit.']
Path('/tmp/astra-cuff-boundary11-boundary-sleeve.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
