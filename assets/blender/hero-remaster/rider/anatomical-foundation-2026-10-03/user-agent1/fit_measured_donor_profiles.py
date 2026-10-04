"""Fit actual donor with one measured continuous lumen-profile field.

Separate branch maps preserve axial position and scale radial coordinates
around measured air centres to measured body centres. Blend using the frozen
source construction seam/elbow weights; no nearest-body vertex snaps, sweeps,
stock-pattern reconstruction or source UV/PBR replacement.
"""
import argparse, gzip, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','registration','profiles','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,registration,profiles,out,evidence=[Path(getattr(a,k)).resolve() for k in ['source','registration','profiles','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True);assert not (out/'profile-fit.blend').exists(),'Keep frozen controls'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,registration,profiles]}
assert pins[str(source)]=='d97e5cb3e31110d1e6aa104032ab818094a170bc46cf9e0a612f4dd9ec8c680a';assert pins[str(registration)]=='30eb90954010bc12a10e9a773e9580207a403c5710ead18302028a4bd7a4b3c6'
profileRows=json.loads(gzip.decompress(profiles.read_bytes()));frozen=np.load(registration)
bpy.ops.wm.open_mainfile(filepath=str(source));old=bpy.data.objects['Actual selected donor, measured lumen registration, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
g=old.copy();g.data=old.data.copy();bpy.context.collection.objects.link(g);g.name='Actual selected donor, measured clearance profiles, unaccepted';g.hide_set(False);g.hide_render=False
native=np.array([v.co[:] for v in old.data.vertices]);display=np.array([v.vector[:] for v in old.data.attributes['actual_donor_display_xyz'].data]);assert np.array_equal(native,frozen['finalNativeXYZ']);assert np.array_equal(display,frozen['sourceDisplayXYZ'])
alpha=frozen['armSeamWeight'];foreWeight=frozen['forearmBlendWeight'];branches={}
for part in sorted({r['part'] for r in profileRows}):
    rows=sorted([r for r in profileRows if r['part']==part and r.get('usableCenteredRadialPair')],key=lambda r:r['station']);stations=np.array([r['station'] for r in rows]);assert len(rows)>=10 and np.all(np.diff(stations)>0)
    assert np.max(np.diff(stations))<=.061 if part!='torso' else np.max(np.diff(stations))<=.015
    if part=='torso':head=np.array([0.,0.,0.]);axis=np.array([0.,0.,1.]);length=1.
    else:
        b=rig.data.bones[part];head=np.array(b.head_local);axis=np.array(b.tail_local)-head;length=np.linalg.norm(axis);axis/=length
    branches[part]={'station':stations,'air':np.array([r['sourceAirCentroidM'] for r in rows]),'body':np.array([r['bodyOuterCentroidM'] for r in rows]),'scale':np.maximum(1,np.array([r['maximumRequiredUniformCrossSectionScale'] for r in rows])),'head':head,'axis':axis,'length':length,'fadeWidth':float(np.median(np.diff(stations)))}
def branch(part,p):
    b=branches[part];t=float((p-b['head'])@b['axis']/b['length']);s=b['station'];fade=b['fadeWidth'];weight=float(np.clip(min((t-s[0]+fade)/fade,(s[-1]+fade-t)/fade,1),0,1));weight=weight*weight*(3-2*weight)
    ac=np.array([np.interp(t,s,b['air'][:,k]) for k in range(3)]);bc=np.array([np.interp(t,s,b['body'][:,k]) for k in range(3)]);scale=float(np.interp(t,s,b['scale']));r=p-ac;r-=b['axis']*(r@b['axis'])
    return weight*((bc-ac)+(scale-1)*r),weight,t,scale
rows=[]
for i,p in enumerate(native):
    side='R' if display[i,0]>=0 else 'L';torso=branch('torso',p);upper=branch('upperArm.'+side,p);fore=branch('forearm.'+side,p)
    d=(1-alpha[i])*torso[0]+alpha[i]*((1-foreWeight[i])*upper[0]+foreWeight[i]*fore[0]);rows.append((d,torso,upper,fore))
delta=np.array([r[0] for r in rows]);proposed=native+delta
for v,p in zip(g.data.vertices,proposed):v.co=p
g.data.update();g.data.calc_loop_triangles();old.data.calc_loop_triangles();p=np.array([v.co[:] for v in g.data.vertices]);tri=[tuple(t.vertices) for t in g.data.loop_triangles];oldTri=[tuple(t.vertices) for t in old.data.loop_triangles]
assert len(tri)==len(oldTri);assert [f.vertices[:] for f in g.data.polygons]==[f.vertices[:] for f in old.data.polygons];assert [[v.uv[:] for v in l.data] for l in g.data.uv_layers]==[[v.uv[:] for v in l.data] for l in old.data.uv_layers];assert g.data.materials[0] is old.data.materials[0]
body.data.calc_loop_triangles();bp=np.array([v.co[:] for v in body.data.vertices]);btri=[tuple(t.vertices) for t in body.data.loop_triangles]
def tree(points,tris):return BVHTree.FromPolygons([Vector(v) for v in points],tris,all_triangles=True)
def selfpairs(t,tris):return {(i,j) for i,j in t.overlap(t) if i<j and not set(tris[i])&set(tris[j])}
ot=tree(native,oldTri);gt=tree(p,tri);fixedTree=tree(p,oldTri);bt=tree(bp,btri);oldSelf=selfpairs(ot,oldTri);newSelf=selfpairs(gt,tri);fixedSelf=selfpairs(fixedTree,oldTri);oldBody=ot.overlap(bt);newBody=gt.overlap(bt);fixedBody=fixedTree.overlap(bt)
counts={}
for f in g.data.polygons:
    ids=list(f.vertices)
    for i,j in zip(ids,ids[1:]+ids[:1]):e=tuple(sorted((i,j)));counts[e]=counts.get(e,0)+1
boundaryIDs=sorted({v for e,c in counts.items() if c==1 for v in e})
def witnesses(pairs,other,otherTri):return [{'garmentTriangle':i,'otherTriangle':j,'garmentVertexIDs':list(tri[i]),'otherVertexIDs':list(otherTri[j]),'nativeXYZ':p[list(tri[i])].tolist(),'otherNativeXYZ':other[list(otherTri[j])].tolist(),'sourceDisplayXYZ':display[list(tri[i])].tolist()} for i,j in sorted(pairs)[:64]]
old.hide_set(True);old.hide_render=True;g['accepted']=False;g['constructionStage']='Actual donor measured continuous clearance profile field, unrigged/unqualified'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'profile-fit.blend'),compress=True)
np.savez_compressed(out/'profile-field.npz',sourceDisplayXYZ=display,previousNativeXYZ=native,finalNativeXYZ=p,registrationDelta=delta,torsoDelta=np.array([r[1][0] for r in rows]),upperArmDelta=np.array([r[2][0] for r in rows]),forearmDelta=np.array([r[3][0] for r in rows]),branchSupport=np.array([[r[j][1] for j in [1,2,3]] for r in rows]),branchStation=np.array([[r[j][2] for j in [1,2,3]] for r in rows]),branchScale=np.array([[r[j][3] for j in [1,2,3]] for r in rows]),armSeamWeight=alpha,forearmBlendWeight=foreWeight,previousTriangles=np.array(oldTri),triangles=np.array(tri),previousSelfPairs=np.array(sorted(oldSelf)),finalSelfPairs=np.array(sorted(newSelf)),fixedTessellationSelfPairs=np.array(sorted(fixedSelf)),previousBodyPairs=np.array(oldBody),finalBodyPairs=np.array(newBody),fixedTessellationBodyPairs=np.array(fixedBody),boundaryVertexIDs=np.array(boundaryIDs))
branchReport={part:{'usableSections':len(b['station']),'stationRange':b['station'][[0,-1]].tolist(),'fixedFadeWidthStation':b['fadeWidth'],'maximumScale':float(b['scale'].max()),'minimumScale':float(b['scale'].min()),'airCentresM':b['air'].tolist(),'bodyCentresM':b['body'].tolist(),'scales':b['scale'].tolist()} for part,b in branches.items()}
report={'status':'UNACCEPTED actual donor continuous measured clearance construction','pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'profile-fit.blend'),'fieldSHA256':sha(out/'profile-field.npz'),'method':'Piecewise-linear local air/body centroid and uniform radial scale profiles, scale clamped to one; preserves each branch axial coordinate. Smoothstep fade through one measured spacing outside usable support; no unsupported extrapolation. Frozen source seam/elbow weights blend torso/upper/fore fields into one delta on actual donor surface. One construction, no iteration or radius sweep.',
        'profiles':branchReport,'vertices':len(p),'triangles':len(tri),'changedVerticesAbove1Micrometre':int((np.linalg.norm(delta,axis=1)>1e-6).sum()),'maximumDeltaM':float(np.linalg.norm(delta,axis=1).max()),'maximumBoundaryDeltaM':float(np.linalg.norm(delta[boundaryIDs],axis=1).max()),'previousBodyPairs':len(oldBody),'finalBodyPairs':len(newBody),'previousSelfPairs':len(oldSelf),'finalSelfPairs':len(newSelf),'fixedPreviousTessellationBodyPairs':len(fixedBody),'fixedPreviousTessellationSelfPairs':len(fixedSelf),'changedLoopTriangles':sum(x!=y for x,y in zip(tri,oldTri)),'boundaryEdgeCount':sum(c==1 for c in counts.values()),'otherNonManifoldEdges':sum(c>2 for c in counts.values()),'polygonCyclesUVOriginalMaterialExact':True,'finalBodyWitnesses':witnesses(newBody,bp,btri),'finalSelfWitnesses':witnesses(newSelf,p,tri),
        'limits':['Measured profile field retains selected donor geometry, source UV/PBR and fold detail but changes dimensions and finite-wall thickness; played parent likeness is not implied.','Section4mm proposals do not guarantee the complete blended native surface or unsupported end/join regions. Existing wearer cuts and air ports remain separate prerequisites.','No skin/rig/motion/collision response/capture/inference/worker/body-head-51bind replacement, Library or normal-player promotion. All art/wearing/mobile/M0-M5 gates open; parent alone judges.']}
assert pins=={p:sha(p) for p in pins};(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print('MEASURED_PROFILE_FIT_READY','body',len(oldBody),len(newBody),'self',len(oldSelf),len(newSelf),'maximumDeltaM',report['maximumDeltaM'],flush=True)
