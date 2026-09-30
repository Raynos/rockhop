"""Explicit local hood-rim retopology, never another colour graph cut.

Freeze a local geometric strip selection and bridge its actual boundary to
an authored smooth hood opening. Original faces/UVs outside the strip remain.
This is an unaccepted geometry trial, not a head join or texture bake.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from select_collar import boundary_loops, largest_region

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',required=True)
a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
assert not (out/'report.json').exists(), 'Frozen trial already exists'
runtime=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
source=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/hunyuan21/04/working-display2.glb')
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
before=sha(source)
assert before=='f657aa963f2e582a9f70291b3dbd160dafd6e944419d48b21b0425521d4cd63a'
sel=np.load(runtime/'collar-trial1/collar-selection.npz')
v=sel['verticesBlender'].copy();f=sel['faces'].copy();uv=sel['uv'].copy()
base_mask=sel['retainedFaceMask'];prior=json.loads((runtime/'collar-trial1/selection.json').read_text())
old_loop=np.array(prior['boundaryLoops'][0]['positions'])
pos,inv=np.unique(np.round(v,7),axis=0,return_inverse=True)
welded=trimesh.Trimesh(pos,inv[f],process=False)
# Explicit reviewed local strip: distance from failed rim plus a central
# upper envelope. This removes malformed rim/hair and rebuilds that strip.
centers=v[f].mean(axis=1)
dist=cKDTree(old_loop).query(centers)[0]
strip=(dist<.040)|((centers[:,2]>1.52)&(abs(centers[:,0])<.13)&(centers[:,1]<.155))
retained,components=largest_region(base_mask&~strip,welded.face_adjacency)
selected=welded.copy();selected.update_faces(retained)
# Keep original welded vertex indices until boundary walk finishes.
loops=boundary_loops(selected)
report={'status':'UNACCEPTED explicit rim retopology trial','source':str(source),'sourceSHA256':before,'recipeSHA256':sha(__file__),'removedLocalFaces':int((base_mask&~retained).sum()),'retainedFaces':int(retained.sum()),'boundaryCountsBeforeRebuild':[len(l) for l in loops],'stripRadiusMetres':.040,'components':components,'limits':['No head, skin join, deformation, bake or rig','New rim UVs are local donor coordinates, not a detail bake']}
if len(loops)!=1:
 report['status']='REJECTED local strip selection produces multiple boundaries; no rim built'
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 raise RuntimeError(report['status'])
loop=loops[0]
# Use each actual retained source boundary index. UV seam duplicates remain
# intact in original faces; bridges weld positionally at the exact boundary.
faces=f[retained].tolist();verts=v.tolist();tex=uv.tolist()
used=np.unique(f[retained]);original_by_weld={}
for i in used:original_by_weld.setdefault(int(inv[i]),int(i))
anchor=[original_by_weld[i] for i in loop];boundary=pos[loop]
# Walk orientation is inherited; unwrap source ring azimuth and retain its
# angular order, preserving the actual edge circuit rather than sorting it.
angles=np.unwrap(np.arctan2(boundary[:,1]-.015,boundary[:,0]))
clockwise=np.mean(np.diff(angles))<0
# Smooth hood rim: front low opening, rear raised hood silhouette.
outer=np.column_stack([.112*np.cos(angles),.015+.096*np.sin(angles),1.519+.027*np.sin(angles)])
# Local source material donor restricted to lower clean mustard cloth.
donor_ids=used[(v[used,2]>1.40)&(v[used,2]<1.475)&(abs(v[used,0])<.17)]
donor_tree=cKDTree(v[donor_ids]);donor_uv=uv[donor_ids[donor_tree.query(outer)[1]]]
prev=anchor;new_rings=[]
for t in [.33,.66,1.0]:
 ring=boundary*(1-t)+outer*t
 idx=list(range(len(verts),len(verts)+len(ring)));verts.extend(ring.tolist());tex.extend(donor_uv.tolist())
 for i in range(len(loop)):
  j=(i+1)%len(loop);faces.extend([[prev[i],prev[j],idx[j]],[prev[i],idx[j],idx[i]]])
 prev=idx;new_rings.append(idx)
# Explicit round-over and small inner facing: a cloth rim, not overlapping
# shells or a phantom skin attachment. The final edge stays open for review.
for radial,zoff in [(.985,.003),(.955,.001),(.935,-.004),(.925,-.012)]:
 ring=outer.copy();ring[:,:2]=np.array([0,.015])+(ring[:,:2]-[0,.015])*radial;ring[:,2]+=zoff
 idx=list(range(len(verts),len(verts)+len(ring)));verts.extend(ring.tolist());tex.extend(donor_uv.tolist())
 for i in range(len(loop)):
  j=(i+1)%len(loop);faces.extend([[prev[i],prev[j],idx[j]],[prev[i],idx[j],idx[i]]])
 prev=idx;new_rings.append(idx)
# Correct bridge orientation using retained boundary face direction.
edge=(anchor[0],anchor[1]);direction=0
for face in f[retained]:
 for i in range(3):
  if tuple(inv[face[[i,(i+1)%3]]])==(loop[0],loop[1]):direction=1
  elif tuple(inv[face[[i,(i+1)%3]]])==(loop[1],loop[0]):direction=-1
if direction==1:
 faces[len(f[retained]):]=[q[::-1] for q in faces[len(f[retained]):]]
verts=np.asarray(verts);faces=np.asarray(faces);tex=np.asarray(tex)
mesh=trimesh.load(source,process=False).to_geometry()
mesh=trimesh.Trimesh(verts,faces,visual=trimesh.visual.TextureVisuals(uv=tex,material=mesh.visual.material),process=False)
mesh.remove_unreferenced_vertices()
check=mesh.copy();check.merge_vertices(merge_tex=True,merge_norm=True,digits_vertex=7)
counts=np.bincount(check.edges_unique_inverse,minlength=len(check.edges_unique))
report.update(finalFaces=len(mesh.faces),newRimFaces=len(faces)-int(retained.sum()),finalBoundaryCounts=[len(l) for l in boundary_loops(check)],nonmanifoldEdges=int((counts>2).sum()),originalRetainedPositionsUVs='Exact source positions/UVs for every retained original triangle; donor UVs only on new rim',authoredOuterProfile={'xRadius':.112,'yCenter':.015,'yRadius':.096,'zCenter':1.519,'zRearRise':.027},bridgeOrientationReversed=direction==1)
np.savez(out/'retopo-data.npz',vertices=mesh.vertices,faces=mesh.faces,uv=mesh.visual.uv,sourceRetainedMask=retained)
mesh.vertices=mesh.vertices[:,[0,2,1]]*[1,1,-1]
mesh.export(out/'body-collar.glb')
assert sha(source)==before
report['outputSHA256']=sha(out/'body-collar.glb');report['sourceSHA256After']=sha(source)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
