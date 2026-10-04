"""Fit simple affine branches to measured donor/body lumen constraints.

Avoid high-frequency profile curvature that demanded excessive refinement.
Fit linear air/body centre lines and a single conservative radial bound per
branch from every measured direction. Retain actual donor topology/UV/PBR.
This is one constrained construction, not a radius search or accepted art.
"""
import argparse, gzip, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','profiles','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field,profiles,out,evidence=[Path(getattr(a,k)).resolve() for k in ['source','field','profiles','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True);assert not (out/'affine-envelopes.blend').exists(),'Keep frozen controls'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field,profiles]}
assert pins[str(source)]=='b545229e52c4fc5bcb97b4fbc81ccc3a0e5a2f9c87fe3c7338691317d965e449';assert pins[str(field)]=='4885dc1f16cc7873d0b44ed69e79658c042adb43f33d4e97ce9c92ad6b8badf0'
f=np.load(field);profileRows=json.loads(gzip.decompress(profiles.read_bytes()));bpy.ops.wm.open_mainfile(filepath=str(source));old=bpy.data.objects['Actual selected donor, measured lumen registration, unaccepted'];failed=bpy.data.objects['Actual selected donor, measured clearance profiles, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
g=old.copy();g.data=old.data.copy();bpy.context.collection.objects.link(g);g.name='Actual selected donor, affine measured envelopes, unaccepted';g.hide_set(False);g.hide_render=False;native=np.array([v.co[:] for v in old.data.vertices]);assert np.array_equal(native,f['previousNativeXYZ']);display=f['sourceDisplayXYZ'];alpha=f['armSeamWeight'];fore=f['forearmBlendWeight'];branches={};reports={}
for part in sorted({r['part'] for r in profileRows}):
    rows=sorted([r for r in profileRows if r['part']==part and r.get('usableCenteredRadialPair')],key=lambda r:r['station']);t=np.array([r['station'] for r in rows]);design=np.column_stack([np.ones(len(t)),t]);ac=np.array([r['sourceAirCentroidM'] for r in rows]);bc=np.array([r['bodyOuterCentroidM'] for r in rows]);airCoef=np.linalg.lstsq(design,ac,rcond=None)[0];bodyCoef=np.linalg.lstsq(design,bc,rcond=None)[0]
    if part=='torso':head=np.zeros(3);axis=np.array([0.,0.,1.]);length=1.
    else:b=rig.data.bones[part];head=np.array(b.head_local);axis=np.array(b.tail_local)-head;length=np.linalg.norm(axis);axis/=length
    airResidual=ac-design@airCoef;bodyResidual=bc-design@bodyCoef;airResidual-=np.outer(airResidual@axis,axis);bodyResidual-=np.outer(bodyResidual@axis,axis);ae=np.linalg.norm(airResidual,axis=1);be=np.linalg.norm(bodyResidual,axis=1)
    airR=np.array([r['sourceAirRays']['firstRadiusM'] for r in rows]);bodyR=np.array([r['bodyOuterRays']['firstRadiusM'] for r in rows]);denom=airR-ae[:,None];assert np.all(denom>0),'No positive conservative affine envelope bound'
    requirement=(bodyR+.004+be[:,None])/denom;scale=max(1.,float(requirement.max()));guarantee=scale*denom-bodyR-be[:,None];assert float(guarantee.min())>=.004-1e-12
    branches[part]={'head':head,'axis':axis,'length':length,'airCoef':airCoef,'bodyCoef':bodyCoef,'scale':scale}
    reports[part]={'sections':len(rows),'measuredStationRange':t[[0,-1]].tolist(),'linearAirCentreCoefficientsM':airCoef.tolist(),'linearBodyCentreCoefficientsM':bodyCoef.tolist(),'airCentreResidualMPercentiles':np.percentile(ae,[0,50,95,100]).tolist(),'bodyCentreResidualMPercentiles':np.percentile(be,[0,50,95,100]).tolist(),'conservativeUniformRadialScale':scale,'minimumConservativeSectionClearanceM':float(guarantee.min()),'maximumAxialCentreDifferenceM':float(np.abs(((design@bodyCoef)-(design@airCoef))@axis).max()),'boundsMeaning':'lambda*(airRadius-|airCentreResidual|)>=bodyRadius+4mm+|bodyCentreResidual|; positive denominators, all64directions/all local sections. This conservative centred-section bound is not a native whole-mesh clearance proof.'}
def branch(part,p):
    b=branches[part];t=float((p-b['head'])@b['axis']/b['length']);ac=b['airCoef'][0]+t*b['airCoef'][1];bc=b['bodyCoef'][0]+t*b['bodyCoef'][1];r=p-ac;r-=b['axis']*(r@b['axis']);return(bc-ac)+(b['scale']-1)*r
rows=[]
for i,p in enumerate(native):
    side='R' if display[i,0]>=0 else 'L';td=branch('torso',p);ud=branch('upperArm.'+side,p);fd=branch('forearm.'+side,p);d=(1-alpha[i])*td+alpha[i]*((1-fore[i])*ud+fore[i]*fd);rows.append((d,td,ud,fd))
delta=np.array([r[0] for r in rows]);proposed=native+delta
for v,p in zip(g.data.vertices,proposed):v.co=p
g.data.update();g.data.calc_loop_triangles();old.data.calc_loop_triangles();p=np.array([v.co[:] for v in g.data.vertices]);tri=[tuple(t.vertices) for t in g.data.loop_triangles];oldTri=[tuple(t.vertices) for t in old.data.loop_triangles];assert len(tri)==len(oldTri);assert [v.vertices[:] for v in g.data.polygons]==[v.vertices[:] for v in old.data.polygons];assert [[v.uv[:] for v in layer.data] for layer in g.data.uv_layers]==[[v.uv[:] for v in layer.data] for layer in old.data.uv_layers];assert g.data.materials[0] is old.data.materials[0]
body.data.calc_loop_triangles();bp=np.array([v.co[:] for v in body.data.vertices]);btri=[tuple(t.vertices) for t in body.data.loop_triangles]
def tree(points,tris):return BVHTree.FromPolygons([Vector(v) for v in points],tris,all_triangles=True)
def selfpairs(t,tris):return sorted((i,j) for i,j in t.overlap(t) if i<j and not set(tris[i])&set(tris[j]))
gt=tree(p,tri);fixed=tree(p,oldTri);bt=tree(bp,btri);sp=selfpairs(gt,tri);fixedSp=selfpairs(fixed,oldTri);bop=sorted(gt.overlap(bt));fixedBop=sorted(fixed.overlap(bt))
counts={}
for ids in tri:
    for i,j in zip(ids,ids[1:]+ids[:1]):e=tuple(sorted((i,j)));counts[e]=counts.get(e,0)+1
boundaryIDs=sorted({i for e,c in counts.items() if c==1 for i in e});old.hide_set(True);old.hide_render=True;failed.hide_set(True);failed.hide_render=True;g['accepted']=False;g['constructionStage']='Actual donor affine measured branch-envelope construction, unrigged/unqualified'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'affine-envelopes.blend'),compress=True)
np.savez_compressed(out/'affine-envelope-field.npz',sourceDisplayXYZ=display,previousNativeXYZ=native,finalNativeXYZ=p,registrationDelta=delta,torsoDelta=np.array([r[1] for r in rows]),upperArmDelta=np.array([r[2] for r in rows]),forearmDelta=np.array([r[3] for r in rows]),armSeamWeight=alpha,forearmBlendWeight=fore,previousTriangles=np.array(oldTri),triangles=np.array(tri),bodyTrianglePairs=np.array(bop),selfTrianglePairs=np.array(sp),fixedTessellationBodyPairs=np.array(fixedBop),fixedTessellationSelfPairs=np.array(fixedSp),boundaryVertexIDs=np.array(boundaryIDs))
report={'status':'UNACCEPTED actual donor constrained affine envelopes','pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'affine-envelopes.blend'),'fieldSHA256':sha(out/'affine-envelope-field.npz'),'method':'Linear least-squares air/body centres and one conservative radial bound per anatomical branch from all measured64-direction constraints. Constant positive branch scales avoid high-frequency profile curvature. Same source18 seam/elbow vertex weights blend the affine branch deltas. One direct bound construction, no radius/density/cap sweep.',
        'branches':reports,'vertices':len(p),'triangles':len(tri),'maximumDeltaM':float(np.linalg.norm(delta,axis=1).max()),'maximumBoundaryDeltaM':float(np.linalg.norm(delta[boundaryIDs],axis=1).max()),'bodyPairs':len(bop),'selfPairs':len(sp),'fixedPreviousTessellationBodyPairs':len(fixedBop),'fixedPreviousTessellationSelfPairs':len(fixedSp),'changedLoopTriangles':sum(x!=y for x,y in zip(tri,oldTri)),'boundaryEdgeCount':sum(c==1 for c in counts.values()),'otherNonManifoldEdges':sum(c>2 for c in counts.values()),'polygonCyclesUVOriginalMaterialExact':True,
        'limits':['Affine branches are applied beyond measured local section ranges as an explicit construction hypothesis, including torso/hood and garment ends. Missing/merged sections remain unqualified, not filled with invented constraints.','Conservative64-direction section inequalities do not guarantee blended native/body clearance, wearer-port validity or played silhouette. Dimensions and finite-wall thickness change; original donor folds/UV/PBR remain but art is unaccepted.','No rig/skin/motion/collision response/capture/inference/worker/body-head-51bind replacement, Library/player promotion or art/wearing/mobile/M0-M5 acceptance. All prior controls frozen; parent alone judges.']}
assert pins=={p:sha(p) for p in pins};(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print('AFFINE_DONOR_ENVELOPES_READY','body',len(bop),'self',len(sp),'scales',{k:v['conservativeUniformRadialScale'] for k,v in reports.items()},flush=True)
