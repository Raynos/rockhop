"""Integrate one ambient smooth velocity field around measured garment lumens.

Use the affine-envelope controls as infinitesimal generators, normalized by
spatial Gaussian kernels derived from measured air contours. Every material
point follows the same ambient law; no source-attribute displacement blending.
32-step RK4, inverse roundtrip and sampled Jacobians qualify numerics separately
from native triangle contacts. No continuum theorem is a native acceptance.
"""
import argparse, gzip, hashlib, json, math, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','affine-report','field','profiles','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,control,field,profiles,out,evidence=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','affine-report','field','profiles','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True);assert not (out/'ambient-flow.blend').exists(),'Keep frozen controls'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,control,field,profiles]}
assert pins[str(source)]=='a42f7d18c365f1939cd3d55857064357fc54176bef4b52c4470a40cf764d0982';assert pins[str(field)]=='c9d89909d9c41bc3910fec8b822d661c4346c7972387546d98d266bcce186012'
f=np.load(field);cr=json.loads(control.read_text());profileRows=json.loads(gzip.decompress(profiles.read_bytes()));bpy.ops.wm.open_mainfile(filepath=str(source));old=bpy.data.objects['Actual selected donor, measured lumen registration, unaccepted'];failed=bpy.data.objects['Actual selected donor, affine measured envelopes, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
g=old.copy();g.data=old.data.copy();bpy.context.collection.objects.link(g);g.name='Actual selected donor, ambient measured-lumen flow, unaccepted';g.hide_set(False);g.hide_render=False;native=np.array([v.co[:] for v in old.data.vertices]);assert np.array_equal(native,f['previousNativeXYZ']);generators=[];kernels=[];reports={}
for part,record in sorted(cr['branches'].items()):
    rows=sorted([r for r in profileRows if r['part']==part and r.get('usableCenteredRadialPair')],key=lambda r:r['station']);s=np.array([r['station'] for r in rows]);air=np.array(record['linearAirCentreCoefficientsM']);bc=np.array(record['linearBodyCentreCoefficientsM']);scale=record['conservativeUniformRadialScale']
    if part=='torso':head=np.zeros(3);axis=np.array([0.,0.,1.]);length=1.
    else:b=rig.data.bones[part];head=np.array(b.head_local);axis=np.array(b.tail_local)-head;length=np.linalg.norm(axis);axis/=length
    projection=np.eye(3)-np.outer(axis,axis);slope=projection@(bc[1]-air[1]-(scale-1)*projection@air[1]);shear=slope/length;offset=projection@(bc[0]-air[0]-(scale-1)*projection@air[0]-slope*(head@axis/length));kappa=math.log(scale);ratio=kappa/(scale-1) if abs(scale-1)>1e-12 else 1.
    matrix=kappa*projection+ratio*np.outer(shear,axis);vector=ratio*offset;affineMatrix=np.eye(3)+(scale-1)*projection+np.outer(shear,axis)
    center=air[0]+float(s.mean())*air[1];sigmaAxial=float((s[-1]-s[0])*length/2);radii=[math.sqrt(abs(r['garmentSection']['contours'][r['selectedGarmentContourIndex']]['signedPlaneArea'])/math.pi) for r in rows];sigmaRadial=float(np.median(radii));assert sigmaAxial>0 and sigmaRadial>0
    generators.append((matrix,vector,affineMatrix,offset));kernels.append((center,axis,sigmaAxial,sigmaRadial));reports[part]={'scaleFromConservativeControl':scale,'velocityMatrix':matrix.tolist(),'velocityOffsetM':vector.tolist(),'isolatedAffineMatrix':affineMatrix.tolist(),'isolatedAffineOffsetM':offset.tolist(),'kernelCenterM':center.tolist(),'kernelAxis':axis.tolist(),'kernelAxialSigmaM':sigmaAxial,'kernelRadialSigmaM':sigmaRadial,'radialSigmaMethod':'Median equivalent-area radius of actual selected air contours','axialSigmaMethod':'Half measured station-span length'}
def velocity(points):
    logs=[];vectors=[]
    for (matrix,offset,am,ao),(center,axis,sax,srad) in zip(generators,kernels):
        d=points-center;along=d@axis;rad=d-np.outer(along,axis);logs.append(-.5*((along/sax)**2+(rad*rad).sum(1)/srad**2));vectors.append(points@matrix.T+offset)
    logs=np.array(logs).T;weights=np.exp(logs-logs.max(1)[:,None]);weights/=weights.sum(1)[:,None];return np.einsum('nb,bnc->nc',weights,np.array(vectors))
def integrate(points,sign=1,only=None):
    p=points.copy();h=sign/32
    def v(q):return velocity(q) if only is None else q@generators[only][0].T+generators[only][1]
    for step in range(32):
        k1=v(p);k2=v(p+h*k1/2);k3=v(p+h*k2/2);k4=v(p+h*k3);p+=h*(k1+2*k2+2*k3+k4)/6
    return p
isolatedErrors=[]
for i,(matrix,offset,am,ao) in enumerate(generators):
    q=integrate(native,only=i);expected=native@am.T+ao;err=float(np.linalg.norm(q-expected,axis=1).max());assert err<1e-6;isolatedErrors.append(err)
proposed=integrate(native);back=integrate(proposed,sign=-1);roundtrip=np.linalg.norm(back-native,axis=1);assert roundtrip.max()<1e-6
# Fixed finite-difference volume samples at every original garment vertex.
epsilon=1e-5;columns=[]
for k in range(3):
    e=np.eye(3)[k]*epsilon;columns.append((integrate(native+e)-integrate(native-e))/(2*epsilon))
jacobian=np.stack(columns,axis=2);determinants=np.linalg.det(jacobian);assert np.all(np.isfinite(determinants))
for v,p in zip(g.data.vertices,proposed):v.co=p
g.data.update();g.data.calc_loop_triangles();old.data.calc_loop_triangles();p=np.array([v.co[:] for v in g.data.vertices]);tri=[tuple(t.vertices) for t in g.data.loop_triangles];oldTri=[tuple(t.vertices) for t in old.data.loop_triangles];assert len(tri)==len(oldTri);assert [v.vertices[:] for v in g.data.polygons]==[v.vertices[:] for v in old.data.polygons];assert [[v.uv[:] for v in layer.data] for layer in g.data.uv_layers]==[[v.uv[:] for v in layer.data] for layer in old.data.uv_layers];assert g.data.materials[0] is old.data.materials[0]
body.data.calc_loop_triangles();bp=np.array([v.co[:] for v in body.data.vertices]);bt=[tuple(t.vertices) for t in body.data.loop_triangles]
def tree(points,tris):return BVHTree.FromPolygons([Vector(v) for v in points],tris,all_triangles=True)
def selfpairs(t,tris):return sorted((i,j) for i,j in t.overlap(t) if i<j and not set(tris[i])&set(tris[j]))
gt=tree(p,tri);fixed=tree(p,oldTri);bvhBody=tree(bp,bt);sp=selfpairs(gt,tri);fixedSp=selfpairs(fixed,oldTri);bop=sorted(gt.overlap(bvhBody));fixedBop=sorted(fixed.overlap(bvhBody));old.hide_set(True);old.hide_render=True;failed.hide_set(True);failed.hide_render=True;g['accepted']=False;g['constructionStage']='Actual donor ambient smooth-flow construction, unrigged/unqualified'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'ambient-flow.blend'),compress=True)
np.savez_compressed(out/'ambient-flow-field.npz',sourceDisplayXYZ=f['sourceDisplayXYZ'],previousNativeXYZ=native,finalNativeXYZ=p,idealIntegratedXYZ=proposed,inverseIntegratedXYZ=back,roundtripErrorsM=roundtrip,sampledJacobians=jacobian,sampledJacobianDeterminants=determinants,triangles=np.array(tri),previousTriangles=np.array(oldTri),bodyTrianglePairs=np.array(bop),selfTrianglePairs=np.array(sp),fixedTessellationBodyPairs=np.array(fixedBop),fixedTessellationSelfPairs=np.array(fixedSp))
report={'status':'UNACCEPTED actual donor ambient measured-lumen flow','pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'ambient-flow.blend'),'fieldSHA256':sha(out/'ambient-flow-field.npz'),'method':'One stationary ambient field: normalized smooth spatial Gaussian kernels from measured air contours blend affine-log infinitesimal generators. 32-step RK4 forward and inverse; source alpha/forearm attributes are not used as displacement blend weights. One construction, fixed controls/integration, no radius/density/cap search.',
        'reference':{'url':'https://arxiv.org/abs/2410.10997','use':'SVF/invertible flow mathematical motivation only; no neural model, training, package or published clinical pipeline reproduction.'},'generators':reports,'isolatedAffineGeneratorClosureMaxM':max(isolatedErrors),'isolatedAffineGeneratorClosureByBranchM':isolatedErrors,'maximumForwardInverseRoundtripM':float(roundtrip.max()),'finiteDifferenceEpsilonM':epsilon,'sampledJacobianDeterminantPercentiles':np.percentile(determinants,[0,50,95,100]).tolist(),'nonPositiveSampledJacobians':int((determinants<=0).sum()),'vertices':len(p),'triangles':len(tri),'maximumDeltaM':float(np.linalg.norm(p-native,axis=1).max()),'bodyPairs':len(bop),'selfPairs':len(sp),'fixedPreviousTessellationBodyPairs':len(fixedBop),'fixedPreviousTessellationSelfPairs':len(fixedSp),'changedLoopTriangles':sum(x!=y for x,y in zip(tri,oldTri)),'polygonCyclesUVOriginalMaterialExact':True,
        'limits':['Exact smooth velocity flows motivate global invertibility; numerical RK4, finite Jacobian samples and inverse consistency do not prove an entire rendered triangulated surface is free of contacts. Native contact results remain gates.','Spatial kernel widths are measured area/coverage proxies, not verified physical cages; blended flow need not retain individual isolated4mm section guarantees. Unsupported wearer regions and actual ports remain open.','Dimensions/wall thickness/hood silhouette change; chosen source folds/UV/PBR retained, played appearance unaccepted. No rig/skin/motion/runtime collision response/capture/inference/worker/body-head-51bind replacement, Library/player promotion or M0-M5/mobile acceptance. Parent alone judges.']}
assert pins=={p:sha(p) for p in pins};(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print('AMBIENT_DONOR_FLOW_READY','body',len(bop),'self',len(sp),'roundtripM',float(roundtrip.max()),'jacobianMin',float(determinants.min()),flush=True)
