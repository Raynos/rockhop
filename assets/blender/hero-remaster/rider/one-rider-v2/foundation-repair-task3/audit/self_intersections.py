"""Independent CPU Blender BVH + exact segment/triangle test; no scene/render."""
import sys,json,hashlib,time
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'));from glb import GLB
g=GLB(root/'baseline/rider.glb');pr=g.j['meshes'][0]['primitives'][0];base=g.array(pr['attributes']['POSITION']).astype(float);tri=g.array(pr['indices']).reshape(-1,3)
mask=((base[tri][:,:,1]>.69)&(base[tri][:,:,1]<1.08)&(abs(base[tri][:,:,2])<.245)).all(1);ids=np.flatnonzero(mask);rt=tri[ids];_,alias=np.unique(base,axis=0,return_inverse=True);aliases=alias[rt]
EPS=1e-9

def crossing(t1,t2):
 # Six edge/triangle strict-interior tests (double precision). Excludes tangent
 # or endpoint-only touches; finite non-coplanar transverse intersections counted.
 hit=np.zeros(len(t1),bool)
 for aa,bb in [(t1,t2),(t2,t1)]:
  e1=bb[:,1]-bb[:,0];e2=bb[:,2]-bb[:,0]
  for i,k in [(0,1),(1,2),(2,0)]:
   o=aa[:,i];d=aa[:,k]-o;p=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,p);valid=abs(det)>1e-14;invd=np.divide(1,det,out=np.zeros_like(det),where=valid);s=o-bb[:,0];u=np.einsum('ij,ij->i',s,p)*invd;q=np.cross(s,e1);v=np.einsum('ij,ij->i',d,q)*invd;t=np.einsum('ij,ij->i',e2,q)*invd
   hit|=valid&(u>EPS)&(v>EPS)&(u+v<1-EPS)&(t>EPS)&(t<1-EPS)
 return hit

def audit(p):
 raw=p.read_bytes();pose=np.load(p)['p0'] if p.suffix=='.npz' else np.frombuffer(raw,dtype='<f4').reshape(-1,3).astype(float);assert len(pose)==len(base);bvh=BVHTree.FromPolygons(pose.tolist(),rt.tolist(),all_triangles=True,epsilon=0.0);pairs=np.array(sorted(set(tuple(sorted(x)) for x in bvh.overlap(bvh) if x[0]!=x[1])),dtype=int).reshape(-1,2)
 count0=len(pairs);keep=np.array([not set(aliases[a]).intersection(aliases[b]) for a,b in pairs],dtype=bool);pairs=pairs[keep];adj=count0-len(pairs);t1=pose[rt[pairs[:,0]]];t2=pose[rt[pairs[:,1]]]
 hit=crossing(t1,t2);n1=np.cross(t1[:,1]-t1[:,0],t1[:,2]-t1[:,0]);n2=np.cross(t2[:,1]-t2[:,0],t2[:,2]-t2[:,0]);ln1=np.linalg.norm(n1,axis=1);ln2=np.linalg.norm(n2,axis=1);unit1=np.divide(n1,ln1[:,None],out=np.zeros_like(n1),where=ln1[:,None]>1e-14);unit2=np.divide(n2,ln2[:,None],out=np.zeros_like(n2),where=ln2[:,None]>1e-14);parallel=np.linalg.norm(np.cross(unit1,unit2),axis=1)<1e-8;plane=abs(np.einsum('ij,ij->i',t2[:,0]-t1[:,0],unit1))<1e-8;coplanar=parallel&plane
 # Explicitly report coplanar candidates unclassified; not silently clear them.
 witnesses=pairs[hit];faces=np.unique(witnesses);return {'file':str(p.relative_to(root)),'sha256':hashlib.sha256(raw).hexdigest(),'roi_triangles':len(rt),'bvh_overlap_pairs':count0,'excluded_shared_source_geometric_vertex_pairs':adj,'nonadjacent_bvh_candidates':len(pairs),'strict_transverse_intersection_pairs':int(hit.sum()),'distinct_intersecting_roi_faces':len(faces),'coplanar_candidates_unclassified':int(coplanar.sum()),'witness_triangle_pairs_global':ids[witnesses].tolist()[:30],'posed_degenerate_roi_triangles':int((np.linalg.norm(np.cross(pose[rt[:,1]]-pose[rt[:,0]],pose[rt[:,2]]-pose[rt[:,0]]),axis=1)<1e-14).sum())}
ta=np.array([[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]]);tb=np.array([[[.2,.2,-1],[.2,.2,1],[.8,.2,0.]]]);assert crossing(ta,tb)[0];assert not crossing(ta,tb+np.array([2.,0,0]))[0]
args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else []
manifest_path=root/'runtime/comparison-manifest.json';manifest=json.loads(manifest_path.read_text());refmeta={}
for variant in manifest['variants']:
 for item in variant['expected']:
  if item['clip']=='rigid_length_stand_to_sit' and item['mesh_index']==0 and item['primitive_index']==0 and 'holdout' in item['path']:
   refmeta[str(root/'runtime'/item['path'])]={'variant':variant['id'],'time_s':item['time'],'reference_origin':item['reference_origin']}
paths=[root/x for x in args] if args else [root/'audit/exact-source-rest.npz']+[root/'experiments'/f'{n}-rigid_length_stand_to_sit-{k:03d}.npz' for n in ['A','B','C19','C'] for k in range(25)]+[Path(p)for p in refmeta]
report={'method':'CPU Blender BVHTree overlap broad phase; float64 six-edge Moller-Trumbore strict interior narrow phase','sourceSHA256':hashlib.sha256(g.raw).hexdigest(),'roi':'source body primitive0 only; all face corners .69<y<1.08 and |z|<.245','exclusions':'All pairs sharing any exact original source position excluded, not just same exported vertex index. Endpoint/tangent-only intersections excluded. Coplanar candidates reported unclassified.','limits':'No thickness, intersection depth or volume, garment/body layer labels, full body, seat or bike collision certification; near contacts are not penetration. Adjacent folds can be severe but this metric excludes them.','runtime_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),'final_variant_glb_sha256':{v['id']:hashlib.sha256(Path(v['path']).read_bytes()).hexdigest() for v in manifest['variants']},'rows':[]}
for p in paths:
 row=audit(p);row.update(refmeta.get(str(p),{}));report['rows'].append(row);print(json.dumps(row),flush=True)
(root/'audit/self-intersections.json').write_text(json.dumps(report,indent=2))
