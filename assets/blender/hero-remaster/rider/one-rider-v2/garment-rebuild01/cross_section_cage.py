"""Coherent radial panel fit from source sections; no nearest-point snapping."""
from pathlib import Path
import hashlib, json, time
import numpy as np

repo=Path('/Users/raynos/projects/games/rockhop')
root=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01')
run=root/'cage03';out=repo/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/cage03'
run.mkdir(exist_ok=True);out.mkdir(exist_ok=True)
sourceBytes=(root/'fit01.npz').read_bytes();f=np.load(root/'fit01.npz')
P=f['positions'].copy();W=f['weights'];Q=f['quads'];t=np.load(root/'silhouette02/source-target.npz')
topo=json.loads((out.parent/'native02-topology-audit.json').read_text())
jeans=np.zeros(len(P),dtype=bool)
for component in topo['components']:
    if component['vertices']==886:jeans[np.unique(Q[component['sourceFaceIndices']])]=True
shirt=~jeans;assert jeans.sum()==886
def cloud(key):return np.unique(t['positions'][t['triangles'][t[key]]].reshape(-1,3),axis=0)
S={key:cloud(key) for key in ['shirtTorso','shirtL','shirtR','jeans']}
mapping=json.loads((out.parent/'fit01/fit-report.json').read_text())['mapping']
T={r['bone']:np.array(r['freshHeadGame']) for r in mapping}
start=time.monotonic();profiles=[]
armL=W[:,5:9].sum(1);armR=W[:,9:13].sum(1);core=W[:,:5].sum(1)
leftLeg=W[:,13:16].sum(1);rightLeg=W[:,16:19].sum(1)
# Lift the template's long crewneck hem toward the retained hoodie hem.
# Smoothly fades below the chest; arm panel longitudinal positions stay fixed.
newP=P.copy();hemShift=np.quantile(S['shirtTorso'][:,1],.01)-P[shirt,1].min()
u=np.clip((P[:,1]-P[shirt,1].min())/(1.265-P[shirt,1].min()),0,1)
fade=1-u*u*(3-2*u)
newP[shirt,1]+=hemShift*fade[shirt]*core[shirt]

def cage(name, native, target, a, b, stations):
    axis=b-a;length=np.linalg.norm(axis);direction=axis/length
    forward=np.array([1.,0,0]);forward-=direction*(forward@direction);forward/=np.linalg.norm(forward)
    lateral=np.cross(direction,forward)
    def coords(points):
        d=points-a
        return np.c_[np.einsum('ij,j->i',d,direction)/length,
                     np.einsum('ij,j->i',d,forward),np.einsum('ij,j->i',d,lateral)]
    nc=coords(native);sc=coords(target);records=[]
    for station in stations:
        samples=[]
        for points in [nc,sc]:
            # Use a fixed number of nearest longitudinal samples, always
            # measured from the correct semantic panel, never old skin.
            count=min(len(points),max(16,int(len(points)*.12)))
            indices=np.argsort(abs(points[:,0]-station),kind='stable')[:count]
            lo,hi=np.quantile(points[indices,1:],[.05,.95],axis=0)
            center=(lo+hi)/2;radius=(hi-lo)/2
            assert np.all(radius>.004),(name,station,radius)
            samples.append((center,radius,count))
        records.append({'station':float(station),'nativeCenter':samples[0][0].tolist(),
                        'nativeRadius':samples[0][1].tolist(),'sourceCenter':samples[1][0].tolist(),
                        'sourceRadius':samples[1][1].tolist(),
                        'nativeSamples':samples[0][2],'sourceSamples':samples[1][2]})
    profiles.append({'panel':name,'a':a.tolist(),'b':b.tolist(),'records':records})
    def apply(points):
        c=coords(points);ncenter=[];scenter=[];scale=[]
        for dim in [0,1]:
            ncenter.append(np.interp(c[:,0],stations,[r['nativeCenter'][dim] for r in records]))
            scenter.append(np.interp(c[:,0],stations,[r['sourceCenter'][dim] for r in records]))
            scale.append(np.interp(c[:,0],stations,[r['sourceRadius'][dim]/r['nativeRadius'][dim] for r in records]))
        ncenter=np.array(ncenter).T;scenter=np.array(scenter).T;scale=np.array(scale).T
        # Radius ratios outside a meaningful cage range are a failed fit,
        # never silently clamped or swept until they pass.
        if not np.all((scale>.35)&(scale<3.)):
            failure={'status':'No field exported; point-sampled section radius failed guard',
                     'panel':name,'scaleMinMax':[float(scale.min()),float(scale.max())],
                     'records':records,'allProfiles':profiles,
                     'next':'Measure actual triangle-plane section loops, rather than sparse vertex quantiles. Do not widen the radius guard.'}
            path=out/'point-section-failure01.json'
            assert not path.exists();path.write_text(json.dumps(failure,indent=2)+'\n')
            raise RuntimeError(f'Unreliable point cross-section in {name}: no export')
        radial=(c[:,1:]-ncenter)*scale+scenter
        delta=radial-c[:,1:]
        return delta[:,0,None]*forward+delta[:,1,None]*lateral
    return apply

shirtCore=shirt & (core>.35)
torso=cage('torso',newP[shirtCore],S['shirtTorso'],np.array([.64,.90,0]),np.array([.64,1.48,0]),np.linspace(0,1,7))
delta=np.zeros_like(P);delta[shirt]+=core[shirt,None]*torso(newP[shirt])
for side,upper,lower in [('L',6,7),('R',10,11)]:
    membership=shirt & ((armL if side=='L' else armR)>.35)
    for role,index,child,weights in [('upperArm',upper,'forearm',W[:,upper]+W[:,upper-1]),
                                     ('forearm',lower,'hand',W[:,lower]+W[:,lower+1])]:
        a,b=T[role+'.'+side],T[child+'.'+side]
        axis=b-a;axis2=axis@axis
        native=newP[membership];longitudinal=(native-a)@axis/axis2
        target=S['shirt'+side];sourceLong=(target-a)@axis/axis2
        native=native[(longitudinal>-.12)&(longitudinal<1.12)]
        target=target[(sourceLong>-.12)&(sourceLong<1.12)]
        transfer=cage(role+'.'+side,native,target,a,b,np.array([0.,.25,.5,.75,1.]))
        delta[shirt]+=weights[shirt,None]*transfer(newP[shirt])

waistPoints=jeans & (P[:,1]>.78)
waistSource=S['jeans'][S['jeans'][:,1]>.78]
waist=cage('jeansWaist',P[waistPoints],waistSource,np.array([.64,.78,0]),np.array([.64,1.01,0]),np.linspace(0,1,4))
waistWeight=W[:,:13].sum(1)
delta[jeans]+=waistWeight[jeans,None]*waist(P[jeans])
for side,sign,weights in [('L',1,leftLeg),('R',-1,rightLeg)]:
    mask=jeans & (sign*P[:,2]>0)
    source=S['jeans'][sign*S['jeans'][:,2]>.025]
    # Longitudinal torso-independent leg cage; no height band assigns
    # weights or edits an unrelated body panel.
    a=np.array([.64,.20,sign*.18]);b=np.array([.64,.96,sign*.11])
    transfer=cage('jeans'+side,P[mask],source,a,b,np.linspace(0,1,8))
    delta[jeans]+=weights[jeans,None]*transfer(P[jeans])
result=newP+delta
tri=np.concatenate([Q[:,[0,1,2]],Q[:,[0,2,3]]])
before=np.cross(P[tri[:,1]]-P[tri[:,0]],P[tri[:,2]]-P[tri[:,0]])
after=np.cross(result[tri[:,1]]-result[tri[:,0]],result[tri[:,2]]-result[tri[:,0]])
dots=(before*after).sum(1)/np.maximum(np.linalg.norm(before,axis=1)*np.linalg.norm(after,axis=1),1e-20)
edgeBefore=np.linalg.norm(P[tri]-np.roll(P[tri],-1,axis=1),axis=2)
edgeAfter=np.linalg.norm(result[tri]-np.roll(result[tri],-1,axis=1),axis=2)
path=run/'fit03.npz';assert not path.exists()
np.savez_compressed(path,positions=result,weights=W,quads=Q,uvLoops=f['uvLoops'])
assert (root/'fit01.npz').read_bytes()==sourceBytes
report={'status':'Coherent source cross-section cage fit; unaccepted before gray/actual pose review',
        'sourceFit01SHA256':hashlib.sha256(sourceBytes).hexdigest(),
        'fit03SHA256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'weightsUVTopologyExact':True,'vertices':len(P),'quads':len(Q),
        'restNormalOpposition':int((dots<-.2).sum()),
        'restEdgeChangeQuantiles':np.quantile(edgeAfter/np.maximum(edgeBefore,1e-20),[0,.5,.9,.99,1]).tolist(),
        'displacementQuantilesM':np.quantile(np.linalg.norm(result-P,axis=1),[0,.5,.9,.99,1]).tolist(),
        'hemShiftM':float(hemShift),'seconds':time.monotonic()-start,
        'settings':{'crossSectionQuantiles':[.05,.95],'nearestLongitudinalSampleFraction':.12,
                    'minimumSamples':16,'nativeRoleBlend':'Exact fit01 anatomical weights; no hard per-vertex panel snapping',
                    'longitudinalArmRange':[-.12,1.12],'radiusScaleGuard':[.35,3.],
                    'detail':'Low-frequency coherent cage only; original source surface not altered or decimated'},
        'profiles':profiles,'limits':['No texture bake or continuous interface join; head/hood/gloves/shoes original sources protected.',
                                    'Actual C19 pose probes, gray turntable and eventual game motion required.']}
(out/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='profiles'}))
