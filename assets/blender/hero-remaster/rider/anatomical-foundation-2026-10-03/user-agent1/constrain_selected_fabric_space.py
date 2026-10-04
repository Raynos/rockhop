"""Constrain selected source relief by measured opposing fabric-sheet space.

Static construction bounds, not cloth simulation or consumed game collision.
Preserve exact rejected source and its selected-donor UV/PBR atlas.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field_path,out,evidence=[Path(getattr(a,k)).resolve() for k in ['source','field','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'fabric-space.blend').exists(),'Preserve frozen candidate'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field_path]}
assert pins[str(source)]=='3859ffbe0716d1a6d87705c8f84fc4838527128b509ebc9244042199dcf91d34'
bpy.ops.wm.open_mainfile(filepath=str(source))
original=bpy.data.objects['Selected Hunyuan radial exterior wearable, unrigged'];data=np.load(field_path)
seed=data['seedXYZ'];direction=data['direction'];edges=data['edges'];target=data['targetRelief'];old=data['connectedRelief'];ease=data['boundaryEase']
original.data.calc_loop_triangles();triangles=[tuple(t.vertices) for t in original.data.loop_triangles]
st=BVHTree.FromPolygons([Vector(p) for p in seed],triangles,all_triangles=True)
neighbors=[set() for _ in seed];incident=[set() for _ in seed]
for i,j in edges:neighbors[i].add(int(j));neighbors[j].add(int(i))
for tri,ids in enumerate(triangles):
    for i in ids:incident[i].add(tri)
bounds=np.full(len(seed),.025);records=[]
for i,(p,d) in enumerate(zip(seed,direction)):
    near={i}|neighbors[i]
    near|={j for k in list(near) for j in neighbors[k]}
    excluded={tri for k in near for tri in incident[k]}
    origin=Vector(p+d*1e-6);travel=1e-6
    for step in range(20):
        q,n,tri,distance=st.ray_cast(origin,Vector(d),.080-travel)
        if q is None:break
        travel+=float(distance)
        if tri not in excluded:
            # Both facing patches may move. Allocate less than half their
            # actual ray gap, retaining4mm shared static construction room.
            cap=max(0.,(travel-.004)*.45);bounds[i]=min(.025,cap)
            records.append({'vertex':i,'opposingSeedTriangle':int(tri),'rayGapM':travel,'scalarBoundM':float(bounds[i])})
            break
        origin=q+Vector(d)*1e-6;travel+=1e-6
        if travel>=.080:break
degree=np.zeros(len(seed));np.add.at(degree,edges[:,0],1);np.add.at(degree,edges[:,1],1)
field=np.zeros(len(seed));weight=8.;iterations=40
for step in range(iterations):
    accum=np.zeros(len(seed));np.add.at(accum,edges[:,0],field[edges[:,1]]);np.add.at(accum,edges[:,1],field[edges[:,0]])
    proposed=(target+weight*accum)/(1+weight*degree)*ease
    field=np.minimum(proposed,bounds)
garment=original.copy();garment.data=original.data.copy();garment.name='Selected Hunyuan fabric-space wearable, unrigged';bpy.context.collection.objects.link(garment)
final=seed+direction*field[:,None]
for vertex,p in zip(garment.data.vertices,final):vertex.co=p
garment.data.update();original.hide_render=True;original.hide_set(True)
garment['accepted']=False;garment['constructionStage']='Actual selected source relief constrained by seed fabric-space rays, unrigged; independent source/rest/game/art qualification pending'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'fabric-space.blend'),compress=True)
assert pins=={p:sha(p) for p in pins}
np.savez_compressed(out/'fabric-space.npz',seedXYZ=seed,finalXYZ=final,direction=direction,targetRelief=target,
                    originalConnectedRelief=old,connectedRelief=field,scalarBounds=bounds,boundaryEase=ease,edges=edges,region=data['region'],
                    sourceTriangle=data['sourceTriangle'],barycentric=data['barycentric'])
report={'status':'UNACCEPTED selected-source fabric-space constrained construction',
        'pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'fabric-space.blend'),'fieldSHA256':sha(out/'fabric-space.npz'),
        'method':'Same selected-source scalar targets/directions and connected40step/weight8 solver; bound from actual nonlocal seed cloth ray gap, two-ring incident triangles excluded',
        'sharedGapReserveM':.004,'perFacingSheetShare':.45,'changedScalarBounds':int(sum(bounds<.025)),
        'maximumReliefM':float(field.max()),'maximumReductionM':float((old-field).max()),'rayWitnesses':records,
        'textures':'Source10exact selected-donor UV and base/roughness/metallic atlas retained; geometric morph does not rebake appearance',
        'limits':['Static cloth-space ray constraint is consumed in construction only, not runtime skin/collision or full surface separation proof.',
                  'Triangle interiors/direction changes can defeat a vertex ray bound; independent body/self/coverage verification required.',
                  'All original source meshes/body/head/51bind/controls preserved. No rig/game/Library/player handoff or M0-M5 acceptance; root alone judges played art.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['changedScalarBounds','maximumReliefM','maximumReductionM']}),flush=True)
