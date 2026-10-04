"""Localize actual donor surface defects without altering source16 geometry."""
import argparse, collections, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','registration-recipe','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,recipe,out=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','registration-recipe','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,recipe]}
assert pins[str(source)]=='862e93a943799115be7620bffb2be0c51d13a7c2c56e34d699519c8c5e33d1f1'
bpy.ops.wm.open_mainfile(filepath=str(source));g=bpy.data.objects['Actual selected donor surface with wearer cuts, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
g.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in g.data.loop_triangles]);native=np.array([v.co[:] for v in g.data.vertices]);display=np.array([x.vector[:] for x in g.data.attributes['actual_donor_display_xyz'].data])
definition=recipe.read_text();definition=definition[definition.index('height=.472'):definition.index('lineage=[]')];exec(compile(definition,str(recipe),'exec'))
recomputed=np.array([register(p)[0] for p in display]);ancestryError=np.linalg.norm(native-recomputed,axis=1)
segmentChoice=np.array([register(p)[2] for p in display],dtype=np.int32)
segmentMixed=np.array([len(set(segmentChoice[ids]))>1 for ids in tri])
def pairs(points):
    t=BVHTree.FromPolygons([Vector(p) for p in points],tri.tolist(),all_triangles=True)
    return {(i,j) for i,j in t.overlap(t) if i<j and not set(tri[i])&set(tri[j])},t
originalSelf,dt=pairs(display);nativeSelf,nt=pairs(native)
center=display[tri].mean(1);normal=np.cross(display[tri[:,1]]-display[tri[:,0]],display[tri[:,2]]-display[tri[:,0]])
normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-15)
region=[];orientation=[];radial=[]
for p,n in zip(center,normal):
    part='hood' if p[2]>.62 else 'sleeve.R' if p[0]>.43 else 'sleeve.L' if p[0]<-.43 else 'shoulder.R' if p[0]>.35 else 'shoulder.L' if p[0]<-.35 else 'torso'
    side='R' if p[0]>=0 else 'L'
    if part.startswith(('sleeve','shoulder')):
        s=source_anchors[side];options=[]
        for i in [0,1]:
            axis=s[i+1]-s[i];u=np.clip(np.dot(p-s[i],axis)/np.dot(axis,axis),0,1);q=s[i]+u*axis;options.append((np.linalg.norm(p-q),q))
        q=min(options,key=lambda x:x[0])[1];r=p-q
    else:r=np.array([p[0],p[1],0])
    r/=max(np.linalg.norm(r),1e-12);dot=float(n@r)
    region.append(part);radial.append(dot);orientation.append('outward' if dot>.15 else 'inward' if dot<-.15 else 'tangent')
body.data.calc_loop_triangles();bp=np.array([v.co[:] for v in body.data.vertices]);btri=np.array([t.vertices[:] for t in body.data.loop_triangles]);bt=BVHTree.FromPolygons([Vector(p) for p in bp],btri.tolist(),all_triangles=True);contacts=nt.overlap(bt)
dominant=[]
for vertex in body.data.vertices:
    weights=[(float(x.weight),body.vertex_groups[x.group].name) for x in vertex.groups if body.vertex_groups[x.group].name in rig.data.bones and rig.data.bones[body.vertex_groups[x.group].name].use_deform]
    dominant.append(max(weights)[1] if weights else 'unweighted')
def classes(ps):return dict(collections.Counter('/'.join(sorted([region[i],region[j]])) for i,j in ps))
def witness(i,j):
    return {'triangles':[i,j],'regions':[region[i],region[j]],'sourceRadialOrientation':[orientation[i],orientation[j]],'nativeXYZ':native[tri[[i,j]]].tolist(),'originalDisplayXYZ':display[tri[[i,j]]].tolist(),'sourceParentPolygons':[int(g.data.attributes['simplified_donor_polygon'].data[g.data.loop_triangles[t].polygon_index].value) for t in [i,j]]}
bodyClasses=collections.Counter();bodyOrientation=collections.Counter()
for i,j in contacts:
    bone=collections.Counter(dominant[v] for v in btri[j]).most_common(1)[0][0];bodyClasses[region[i]+'/'+bone]+=1;bodyOrientation[region[i]+'/'+orientation[i]]+=1
report={'status':'UNACCEPTED readonly donor surface/registration fit localization','pins':pins,'recipeSHA256':sha(__file__),'sameSavedConnectivityComparisons':True,'vertices':len(native),'triangles':len(tri),
        'originalDisplaySelfPairs':len(originalSelf),'registeredSelfPairs':len(nativeSelf),'sharedPairs':len(originalSelf&nativeSelf),'registrationOnlyPairs':len(nativeSelf-originalSelf),'displayOnlyPairs':len(originalSelf-nativeSelf),
        'originalDisplayClasses':classes(originalSelf),'registeredClasses':classes(nativeSelf),'registrationOnlyClasses':classes(nativeSelf-originalSelf),
        'registrationOnlyPairsTouchingMixedNearestSegmentTriangles':int(sum(segmentMixed[i] or segmentMixed[j] for i,j in nativeSelf-originalSelf)),
        'bodyContactPairs':len(contacts),'bodyContactsBySourceRegionAndDominantBone':dict(bodyClasses),'bodyContactsBySourceRegionAndOriginalRadialOrientation':dict(bodyOrientation),
        'postCutLineageRecomputedRegistrationErrorMPercentiles':np.percentile(ancestryError,[0,50,95,100]).tolist(),
        'registrationOnlyWitnesses':[witness(i,j) for i,j in sorted(nativeSelf-originalSelf)[:64]],'originalDisplayWitnesses':[witness(i,j) for i,j in sorted(originalSelf)[:64]],
        'classification':'Hood originaldisplayZ>0.62; sleeves |X|>0.43, shoulders0.35..0.43; others torso. Inward/outward sign relative original torsoXY or closest sourcearm segment, geometric diagnostic only.',
        'limits':['Same final cut connectivity in original-display and registered coordinates isolates deformation crossing; it is not an audit of uncut original high topology.','Radial inward sign does not by itself prove an unwanted inner wall. No deletion or fit change from these labels.','Post-registration cuts interpolate source ancestry; nonlinear registration recomputation need not equal those final interpolated cut vertices.','No source rewrite, new capture, rig/motion/inference/worker/player promotion; allM0-M5/mobile open, root sole judge.']}
assert pins=={p:sha(p) for p in pins};out.write_text(json.dumps(report,indent=2)+'\n');print('DONOR_FIT_LOCALIZED','display',len(originalSelf),'native',len(nativeSelf),'registrationOnly',len(nativeSelf-originalSelf),'body',len(contacts),flush=True)
