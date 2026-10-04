"""Repair discrete source-elbow registration on the actual donor surface.

Blend the existing two arm maps continuously in a fixed source station band.
Retain saved cut geometry ancestry, polygon cycles, source UV/PBR and all
original native data. This is construction registration, not garment skinning.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','registration-recipe','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,recipe,out,evidence=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','registration-recipe','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'continuous-arm.blend').exists(),'Keep frozen source controls'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,recipe]}
assert pins[str(source)]=='862e93a943799115be7620bffb2be0c51d13a7c2c56e34d699519c8c5e33d1f1'
bpy.ops.wm.open_mainfile(filepath=str(source));old=bpy.data.objects['Actual selected donor surface with wearer cuts, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
g=old.copy();g.data=old.data.copy();bpy.context.collection.objects.link(g);g.name='Actual selected donor, continuous elbow registration, unaccepted'
g.hide_render=False;g.hide_set(False);native=np.array([v.co[:] for v in old.data.vertices]);display=np.array([v.vector[:] for v in old.data.attributes['actual_donor_display_xyz'].data])
definition=recipe.read_text();definition=definition[definition.index('height=.472'):definition.index('lineage=[]')];exec(compile(definition,str(recipe),'exec'))
width=.12
def connected(p):
    torso=(torso_matrix@np.r_[p,1])[:3];side='R' if p[0]>=0 else 'L';s=source_anchors[side];target=target_anchors[side];options=[];axes=[]
    for i in [0,1]:
        axis=s[i+1]-s[i];u=np.clip(np.dot(p-s[i],axis)/np.dot(axis,axis),0,1);center=s[i]+u*axis;axes.append(axis/np.linalg.norm(axis))
        rotation=np.array(Vector(display_to_native@axis).rotation_difference(Vector(target[i+1]-target[i])).to_matrix())@display_to_native
        options.append(target[i]+u*(target[i+1]-target[i])+rotation@(p-center)*.50)
    common=axes[0]+axes[1];common/=np.linalg.norm(common);station=float((p-s[1])@common)
    t=float(np.clip(station/width+.5,0,1));weight=t*t*(3-2*t)
    distance=(abs(p[0])-.36)-max(.46-p[2],0)*.22;alpha=float(np.clip(distance/.15,0,1));alpha=alpha*alpha*(3-2*alpha)
    arm=options[0]*(1-weight)+options[1]*weight
    return (1-alpha)*torso+alpha*arm,station,weight,alpha
oldMapped=np.array([register(p)[0] for p in display]);rows=[connected(p) for p in display];newMapped=np.array([r[0] for r in rows]);station=np.array([r[1] for r in rows]);weight=np.array([r[2] for r in rows]);alpha=np.array([r[3] for r in rows])
delta=newMapped-oldMapped;proposed=native+delta
for v,p in zip(g.data.vertices,proposed):v.co=p
g.data.update();g.data.calc_loop_triangles();p=np.array([v.co[:] for v in g.data.vertices]);tri=[tuple(t.vertices) for t in g.data.loop_triangles]
counts={}
for f in g.data.polygons:
    ids=list(f.vertices)
    for i,j in zip(ids,ids[1:]+ids[:1]):e=tuple(sorted((i,j)));counts[e]=counts.get(e,0)+1
boundaryIDs=sorted({v for e,c in counts.items() if c==1 for v in e})
assert [f.vertices[:] for f in g.data.polygons]==[f.vertices[:] for f in old.data.polygons]
assert [[v.uv[:] for v in layer.data] for layer in g.data.uv_layers]==[[v.uv[:] for v in layer.data] for layer in old.data.uv_layers]
assert g.data.materials[0] is old.data.materials[0]
gt=BVHTree.FromPolygons([Vector(v) for v in p],tri,all_triangles=True);ot=BVHTree.FromPolygons([Vector(v) for v in native],tri,all_triangles=True)
def selfpairs(tree):return {(i,j) for i,j in tree.overlap(tree) if i<j and not set(tri[i])&set(tri[j])}
oldSelf=selfpairs(ot);newSelf=selfpairs(gt)
body.data.calc_loop_triangles();bp=np.array([v.co[:] for v in body.data.vertices]);btri=[tuple(t.vertices) for t in body.data.loop_triangles];bt=BVHTree.FromPolygons([Vector(v) for v in bp],btri,all_triangles=True)
oldBody=ot.overlap(bt);newBody=gt.overlap(bt)
def witnesses(pairs,other,otherTri):
    return [{'garmentTriangle':i,'otherTriangle':j,'garmentVertexIDs':list(tri[i]),'otherVertexIDs':list(otherTri[j]),'nativeXYZ':p[list(tri[i])].tolist(),'otherNativeXYZ':other[list(otherTri[j])].tolist(),'sourceDisplayXYZ':display[list(tri[i])].tolist()} for i,j in sorted(pairs)[:64]]
old.hide_render=True;old.hide_set(True);g['accepted']=False;g['constructionStage']='Actual donor continuous source-elbow registration; unrigged and still unqualified wearer fit'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'continuous-arm.blend'),compress=True)
np.savez_compressed(out/'continuous-registration.npz',sourceDisplayXYZ=display,previousNativeXYZ=native,finalNativeXYZ=p,oldRegisteredSourceXYZ=oldMapped,newRegisteredSourceXYZ=newMapped,registrationDelta=delta,sourceElbowStation=station,forearmBlendWeight=weight,armSeamWeight=alpha,triangles=np.array(tri),previousSelfPairs=np.array(sorted(oldSelf)),finalSelfPairs=np.array(sorted(newSelf)),finalBodyPairs=np.array(newBody),boundaryVertexIDs=np.array(boundaryIDs))
norm=np.linalg.norm(delta,axis=1);outside=np.abs(station)>=width/2
report={'status':'UNACCEPTED actual donor continuous source-elbow construction registration','pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'continuous-arm.blend'),'fieldSHA256':sha(out/'continuous-registration.npz'),
        'method':'Same two frozen source-to-body arm maps and torso seam blend, smoothstep across fixed0.12source-unit station interval about source elbow, station along source segment-axis bisector. No discrete nearest segment selection. Delta applied to frozen native cut vertices, retained nonlinear cut ancestry residual.',
        'vertices':len(p),'triangles':len(tri),'changedVerticesAbove1Micrometre':int((norm>1e-6).sum()),'maximumRegistrationDeltaM':float(norm.max()),'outsideSourceElbowBandMaximumDeltaM':float(norm[outside].max()),'maximumOpeningBoundaryDeltaM':float(norm[boundaryIDs].max()),
        'previousSelfPairs':len(oldSelf),'finalSelfPairs':len(newSelf),'removedSelfPairs':len(oldSelf-newSelf),'introducedSelfPairs':len(newSelf-oldSelf),'previousBodyPairs':len(oldBody),'finalBodyPairs':len(newBody),
        'polygonCyclesUVOriginalMaterialExact':True,'otherNonManifoldEdges':sum(c>2 for c in counts.values()),'boundaryEdgeCount':sum(c==1 for c in counts.values()),'finalBodyWitnesses':witnesses(newBody,bp,btri),'finalSelfWitnesses':witnesses(newSelf,p,tri),
        'limits':['This source construction field is not garment rig weights, simulation or runtime collision. No broad native motion or new capture.','Existing ten opening loops and remaining body/self contacts still require qualification; no art/wearing/rig/mobile pass.','All original body/head/51bind and failed source13/14/15/16 controls preserved; original selected donor UV/PBR exact. AllM0-M5/root sole judge, no normal-player promotion.']}
assert pins=={p:sha(p) for p in pins};(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print('CONTINUOUS_SOURCE_ARM_READY','self',len(oldSelf),len(newSelf),'body',len(oldBody),len(newBody),'maxDelta',float(norm.max()),flush=True)
