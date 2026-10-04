"""Place actual donor lumens using measured shared-joint source axes.

Fit source shoulder/elbow/wrist centreline anchors jointly from oriented air
contours. Keep actual donor cut topology, UV/PBR and the original canonical
body rig. This construction checkpoint is unrigged and unaccepted.
"""
import argparse, gzip, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','registration-recipe','continuous-recipe','contours','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
source,recipe,continuous,archive,out,evidence=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','registration-recipe','continuous-recipe','contours','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'measured-lumens.blend').exists(),'Keep frozen controls'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={str(p):sha(p) for p in [source,recipe,continuous,archive]}
assert pins[str(source)]=='989855995983079d3207960f5e36feb734fe0e02987961d8f652c8cd26c3ae3f'
assert pins[str(archive)]=='ba74cad2b49cca57dffcbf6f49b98c4101db9b4f8e6fa94a37bd7e6b38090fd4'
sections=json.loads(gzip.decompress(archive.read_bytes()))
bpy.ops.wm.open_mainfile(filepath=str(source))
old=bpy.data.objects['Actual selected donor, continuous elbow registration, unaccepted']
body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
g=old.copy();g.data=old.data.copy();bpy.context.collection.objects.link(g)
g.name='Actual selected donor, measured lumen registration, unaccepted';g.hide_set(False);g.hide_render=False
native=np.array([v.co[:] for v in old.data.vertices]);display=np.array([v.vector[:] for v in old.data.attributes['actual_donor_display_xyz'].data])
definition=recipe.read_text();definition=definition[definition.index('height=.472'):definition.index('lineage=[]')];exec(compile(definition,str(recipe),'exec'))
definition=continuous.read_text();definition=definition[definition.index('width=.12'):definition.index('oldMapped=np.array')];exec(compile(definition,str(continuous),'exec'))
oldMapped=np.array([connected(p)[0] for p in display]);oldAnchors={s:v.copy() for s,v in source_anchors.items()}
selection=[];fits={}
for side in ['R','L']:
    design=[];centroids=[];chosen=[]
    for r in sections['sleeves']:
        if not r['part'].endswith('.'+side):continue
        candidates=[(i,c) for i,c in enumerate(r['sourceSection']['contours']) if c.get('orientation')=='airCavity' and c['centroidOffsetFromReference']<=.2]
        if not candidates:selection.append({'part':r['part'],'station':r['station'],'included':False,'reason':'No local air cavity; connected shoulder/torso section'});continue
        # Largest local lumen excludes tiny material pockets without deleting them.
        idx,c=max(candidates,key=lambda item:abs(item[1]['signedPlaneArea']))
        t=r['station'];design.append([1-t,t,0] if r['part'].startswith('upperArm.') else [0,1-t,t]);centroids.append(c['centroidXYZ'])
        chosen.append({'part':r['part'],'station':t,'included':True,'sourceContourIndex':idx,'signedPlaneArea':c['signedPlaneArea'],'centroidXYZ':c['centroidXYZ']});selection.append(chosen[-1])
    design=np.array(design);centroids=np.array(centroids);anchors,residuals,rank,singular=np.linalg.lstsq(design,centroids,rcond=None)
    assert rank==3 and len(chosen)>=20
    source_anchors[side]=anchors
    errors=np.linalg.norm(design@anchors-centroids,axis=1)
    fits[side]={'sourceShoulderElbowWristXYZ':anchors.tolist(),'oldSourceShoulderElbowWristXYZ':oldAnchors[side].tolist(),'selectedSections':len(chosen),'rank':int(rank),'singularValues':singular.tolist(),'centroidFitResidualOriginalUnitsPercentiles':np.percentile(errors,[0,50,95,100]).tolist()}
torsoPairs=[r for r in sections['torso'] if 'bodyMinusMappedSourceCentroidNativeM' in r]
torsoDelta=np.median([r['bodyMinusMappedSourceCentroidNativeM'] for r in torsoPairs],axis=0);torsoDelta[2]=0
oldTorso=torso_matrix.copy();torso_matrix[:3,3]+=torsoDelta
rows=[connected(p) for p in display];newMapped=np.array([r[0] for r in rows]);delta=newMapped-oldMapped;proposed=native+delta
for v,p in zip(g.data.vertices,proposed):v.co=p
g.data.update();g.data.calc_loop_triangles();old.data.calc_loop_triangles()
p=np.array([v.co[:] for v in g.data.vertices]);tri=[tuple(t.vertices) for t in g.data.loop_triangles]
oldTri=[tuple(t.vertices) for t in old.data.loop_triangles]
assert len(tri)==len(oldTri)
changedTessellation=sum(x!=y for x,y in zip(tri,oldTri))
assert [f.vertices[:] for f in g.data.polygons]==[f.vertices[:] for f in old.data.polygons]
assert [[v.uv[:] for v in layer.data] for layer in g.data.uv_layers]==[[v.uv[:] for v in layer.data] for layer in old.data.uv_layers]
assert g.data.materials[0] is old.data.materials[0]
assert [v.vector[:] for v in g.data.attributes['actual_donor_display_xyz'].data]==[v.vector[:] for v in old.data.attributes['actual_donor_display_xyz'].data]
body.data.calc_loop_triangles();bp=np.array([v.co[:] for v in body.data.vertices]);btri=[tuple(t.vertices) for t in body.data.loop_triangles]
def tree(points,tris):return BVHTree.FromPolygons([Vector(v) for v in points],tris,all_triangles=True)
ot=tree(native,oldTri);gt=tree(p,tri);fixedTree=tree(p,oldTri);bt=tree(bp,btri)
def selfpairs(t,tris):return {(i,j) for i,j in t.overlap(t) if i<j and not set(tris[i])&set(tris[j])}
oldSelf=selfpairs(ot,oldTri);newSelf=selfpairs(gt,tri);fixedSelf=selfpairs(fixedTree,oldTri);oldBody=ot.overlap(bt);newBody=gt.overlap(bt);fixedBody=fixedTree.overlap(bt)
counts={}
for f in g.data.polygons:
    ids=list(f.vertices)
    for i,j in zip(ids,ids[1:]+ids[:1]):e=tuple(sorted((i,j)));counts[e]=counts.get(e,0)+1
boundaryIDs=sorted({v for e,c in counts.items() if c==1 for v in e})
def witnesses(pairs,other,otherTri):
    return [{'garmentTriangle':i,'otherTriangle':j,'garmentVertexIDs':list(tri[i]),'otherVertexIDs':list(otherTri[j]),'nativeXYZ':p[list(tri[i])].tolist(),'otherNativeXYZ':other[list(otherTri[j])].tolist(),'sourceDisplayXYZ':display[list(tri[i])].tolist()} for i,j in sorted(pairs)[:64]]
def classes(pairs,tris):
    result={}
    for i,j in pairs:
        c=display[list(tris[i])].mean(0);side='R' if c[0]>=0 else 'L';s=source_anchors[side];distance=(abs(c[0])-.36)-max(.46-c[2],0)*.22
        part='torso/hood' if distance<=0 else ('arm-seam' if distance<.15 else ('upperArm.'+side if connected(c)[2]<.5 else 'forearm.'+side))
        result[part]=result.get(part,0)+1
    return result
old.hide_set(True);old.hide_render=True;g['accepted']=False;g['constructionStage']='Actual donor measured-lumen construction registration, unrigged/unqualified'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'measured-lumens.blend'),compress=True)
np.savez_compressed(out/'measured-registration.npz',sourceDisplayXYZ=display,previousNativeXYZ=native,finalNativeXYZ=p,previousRegisteredSourceXYZ=oldMapped,newRegisteredSourceXYZ=newMapped,registrationDelta=delta,sourceElbowStation=np.array([r[1] for r in rows]),forearmBlendWeight=np.array([r[2] for r in rows]),armSeamWeight=np.array([r[3] for r in rows]),triangles=np.array(tri),previousTriangles=np.array(oldTri),fixedTessellationSelfPairs=np.array(sorted(fixedSelf)),fixedTessellationBodyPairs=np.array(fixedBody),previousSelfPairs=np.array(sorted(oldSelf)),finalSelfPairs=np.array(sorted(newSelf)),previousBodyPairs=np.array(oldBody),finalBodyPairs=np.array(newBody),boundaryVertexIDs=np.array(boundaryIDs))
report={'status':'UNACCEPTED actual donor measured-lumen registration','pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'measured-lumens.blend'),'fieldSHA256':sha(out/'measured-registration.npz'),
        'method':'Joint least-squares source S/E/W fit, shared elbow, from largest local oriented air contour per measured section; exclude nonlocal connected torso contours. Existing continuous arm maps/seam/radial scale retained; torso centroid median translation only. New minus old map applied to frozen native cut geometry, preserves nonlinear cut-interpolation residual.',
        'fits':fits,'sectionSelection':selection,'torsoMedianTranslationM':torsoDelta.tolist(),'torsoSections':len(torsoPairs),'oldTorsoMatrix':oldTorso.tolist(),'newTorsoMatrix':torso_matrix.tolist(),
        'vertices':len(p),'triangles':len(tri),'changedVerticesAbove1Micrometre':int((np.linalg.norm(delta,axis=1)>1e-6).sum()),'maximumRegistrationDeltaM':float(np.linalg.norm(delta,axis=1).max()),'maximumBoundaryRegistrationDeltaM':float(np.linalg.norm(delta[boundaryIDs],axis=1).max()),
        'previousSelfPairs':len(oldSelf),'finalSelfPairs':len(newSelf),'samePreviousTessellationSelfPairs':len(fixedSelf),'samePreviousTessellationBodyPairs':len(fixedBody),'samePreviousTessellationRemovedSelfPairs':len(oldSelf-fixedSelf),'samePreviousTessellationIntroducedSelfPairs':len(fixedSelf-oldSelf),'changedLoopTriangles':changedTessellation,'previousBodyPairs':len(oldBody),'finalBodyPairs':len(newBody),'previousBodyConstructionClasses':classes(oldBody,oldTri),'finalBodyConstructionClasses':classes(newBody,tri),
        'polygonCyclesUVSourceAttributeOriginalMaterialExact':True,'boundaryEdgeCount':sum(c==1 for c in counts.values()),'otherNonManifoldEdges':sum(c>2 for c in counts.values()),'finalBodyWitnesses':witnesses(newBody,bp,btri),'finalSelfWitnesses':witnesses(newSelf,p,tri),
        'limits':['Measured construction registration is not garment skinning, cloth simulation or runtime collision. No radius/iteration sweep, independent vertex snaps, new texture or stock-pattern fallback.','Polygon cycles and UVs remain exact; Blender may retessellate deformed n-gons. Actual new triangles and a fixed previous-triangle causal diagnostic are both retained.','Existing cuts were made under previous registration; retained boundary cycles are not a new wearer-port proof. Actual finite-thickness donor ports and complete canonical-body containment need qualification.','No art/wearing/rig/broad native motion/mobile/M0-M5 acceptance, new capture, inference, worker, Library or normal-player promotion. Body/head/51bind and all prior controls remain immutable; parent alone judges.']}
assert pins=={path:sha(path) for path in pins}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print('MEASURED_LUMEN_REGISTRATION_READY','body',len(oldBody),len(newBody),'self',len(oldSelf),len(newSelf),'maxDelta',report['maximumRegistrationDeltaM'],flush=True)
