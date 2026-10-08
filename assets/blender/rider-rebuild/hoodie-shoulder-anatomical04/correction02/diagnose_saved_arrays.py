"""Readonly numeric tests on actual saved-panel arrays, no mesh authoring."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inside(points,vertices,faces):
 # Odd ray parity against the COMPLETE canonical surface, fixed non-axis ray.
 # No nearest-point sign or projection; coincident ray-edge hits are deduped.
 tris=vertices[faces];a=tris[:,0];e1=tris[:,1]-a;e2=tris[:,2]-a
 direction=np.array([1.,.317,.173]);direction/=np.linalg.norm(direction)
 h=np.cross(direction,e2);det=np.einsum('ij,ij->i',e1,h);valid=np.abs(det)>1e-12
 inv=np.zeros_like(det);inv[valid]=1/det[valid];result=[]
 for p in points:
  s=p-a;u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1)
  v=inv*(q@direction);t=inv*np.einsum('ij,ij->i',e2,q)
  hits=np.sort(t[valid&(u>=0)&(v>=0)&(u+v<=1)&(t>1e-8)])
  count=0 if not len(hits)else 1+int(np.count_nonzero(np.diff(hits)>1e-7))
  result.append(bool(count%2))
 return np.asarray(result)
def main():
 p=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();assert not out.exists()
 d=np.load(p);v=d['vertices'];starts=d['polygonStarts'];counts=d['polygonCounts'];corners=d['cornerVertexIds'];old=d['_panel04_original_vertex_id'];faceold=d['_panel04_original_face_id'];uv=d['UV']
 newfaces=np.flatnonzero(faceold==-1);newverts=np.flatnonzero(old==-1)
 records=[];centers=[]
 for fi in newfaces:
  ids=corners[starts[fi]:starts[fi]+counts[fi]];q=v[ids];assert len(q)==4
  n1=np.cross(q[1]-q[0],q[2]-q[0]);n2=np.cross(q[2]-q[0],q[3]-q[0]);den=np.linalg.norm(n1)*np.linalg.norm(n2)
  cosine=float(np.dot(n1,n2)/den)if den>1e-20 else -1.
  records.append({'face':int(fi),'vertices':ids.tolist(),'triangleNormalCosine':cosine,'minimumTriangleArea':float(min(np.linalg.norm(n1),np.linalg.norm(n2))*.5),'UVSpan':float(np.ptp(uv[starts[fi]:starts[fi]+4],axis=0).max())});centers.append(q.mean(0))
 bodyin=inside(v[newverts],d['canonicalBodyVertices'],d['canonicalBodyFaces']);centerin=inside(centers,d['canonicalBodyVertices'],d['canonicalBodyFaces'])
 for row,yes in zip(records,centerin):row['quadCenterInsideCanonicalBodyByRayParity']=bool(yes)
 result={'accepted':False,'stage':'ACTUAL_SAVED_PANEL_FOLD_AND_CANONICAL_BODY_PARITY_DIAGNOSIS','arraySHA256':sha(p),'newVertices':len(newverts),'newFaces':len(newfaces),'opposedFanTriangleNormals':[r for r in records if r['triangleNormalCosine']<0],'degenerateFanTriangles':[r for r in records if r['minimumTriangleArea']<1e-10],'newVerticesInsideCanonicalBody':newverts[bodyin].tolist(),'newFaceCentersInsideCanonicalBody':[r for r in records if r['quadCenterInsideCanonicalBodyByRayParity']],'allActualPanelFaceTests':records,'limits':['Ray parity tests actual points against complete canonical torso-equivalent body; it does not classify every pixel or certify wearing.','Opposed triangle normals identify severe local folded triangulations; original globally consistent seam winding remains distinct.']}
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:len(result[k])for k in ('opposedFanTriangleNormals','degenerateFanTriangles','newVerticesInsideCanonicalBody','newFaceCentersInsideCanonicalBody')}))
if __name__=='__main__':main()
