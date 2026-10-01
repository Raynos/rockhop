"""Coherent radial panel fit from actual triangle-plane sections; no nearest-point snapping."""
from pathlib import Path
import hashlib, json, time
import numpy as np

repo=Path('/Users/raynos/projects/games/rockhop')
root=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01')
run=root/'cage04';out=repo/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/cage04'
run.mkdir(exist_ok=True);out.mkdir(exist_ok=True)
assert not (run/'fit04.npz').exists(),'Preserve frozen cage04; use an owned reproduction directory'
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
tri=np.concatenate([Q[:,[0,1,2]],Q[:,[0,2,3]]])
def sourceFaces(key):return t['positions'][t['triangles'][t[key]]]
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
        return np.stack([np.einsum('...j,j->...',d,direction)/length,
                         np.einsum('...j,j->...',d,forward),np.einsum('...j,j->...',d,lateral)],axis=-1)
    nc=coords(native);sc=coords(target);records=[]
    for station in stations:
        samples=[]
        for points in [nc,sc]:
            # Exact triangle-plane intersections avoid sparse ring sampling.
            pieces=[]
            for edge in range(3):
                p0=points[:,edge];p1=points[:,(edge+1)%3]
                d0=p0[:,0]-station;d1=p1[:,0]-station
                hit=(d0*d1<=0)&(abs(d0-d1)>1e-10)
                alpha=d0[hit]/(d0[hit]-d1[hit])
                pieces.append(p0[hit,1:]+alpha[:,None]*(p1[hit,1:]-p0[hit,1:]))
            section=np.unique(np.round(np.concatenate(pieces),8),axis=0)
            assert len(section)>=8,(name,station,'Incomplete section',len(section))
            lo,hi=section.min(0),section.max(0)
            center=(lo+hi)/2;radius=(hi-lo)/2;count=len(section)
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
            failure={'status':'No field exported; Exact triangle section radius failed guard',
                     'panel':name,'scaleMinMax':[float(scale.min()),float(scale.max())],
                     'records':records,'allProfiles':profiles,
                     'next':'Reject this cage before export and inspect actual source/native section geometry; keep the radius guard.'}
            path=out/'triangle-section-failure01.json'
            assert not path.exists();path.write_text(json.dumps(failure,indent=2)+'\n')
            raise RuntimeError(f'Unreliable triangle cross-section in {name}: no export')
        radial=(c[:,1:]-ncenter)*scale+scenter
        delta=radial-c[:,1:]
        return delta[:,0,None]*forward+delta[:,1,None]*lateral
    return apply

shirtCore=shirt & (core>.35)
torso=cage('torso',newP[tri[shirtCore[tri].any(1)]],sourceFaces('shirtTorso'),np.array([.64,.90,0]),np.array([.64,1.48,0]),np.linspace(.05,.90,7))
delta=np.zeros_like(P);delta[shirt]+=core[shirt,None]*torso(newP[shirt])
for side,upper,lower in [('L',6,7),('R',10,11)]:
    membership=shirt & ((armL if side=='L' else armR)>.35)
    for role,index,child,weights in [('upperArm',upper,'forearm',W[:,upper]+W[:,upper-1]),
                                     ('forearm',lower,'hand',W[:,lower]+W[:,lower+1])]:
        a,b=T[role+'.'+side],T[child+'.'+side]
        axis=b-a;axis2=axis@axis
        native=newP[tri[membership[tri].any(1)]]
        target=sourceFaces('shirt'+side)
        # Reviewed source branch cuts the proximal armpit sections. Use distal
        # sections for upper-arm radial shape; torso retains the join region.
        stations=np.array([.50,.65,.85]) if role=='upperArm' else np.array([.10,.30,.50,.70,.85])
        transfer=cage(role+'.'+side,native,target,a,b,stations)
        delta[shirt]+=weights[shirt,None]*transfer(newP[shirt])

waistPoints=jeans & (P[:,1]>.78)
waistSource=S['jeans'][S['jeans'][:,1]>.78]
waist=cage('jeansWaist',P[tri[waistPoints[tri].any(1)]],sourceFaces('jeans'),np.array([.64,.78,0]),np.array([.64,1.01,0]),np.array([.10,.25,.40,.50]))
waistWeight=W[:,:13].sum(1)
delta[jeans]+=waistWeight[jeans,None]*waist(P[jeans])
for side,sign,weights in [('L',1,leftLeg),('R',-1,rightLeg)]:
    mask=jeans & (sign*P[:,2]>0)
    source=S['jeans'][sign*S['jeans'][:,2]>.025]
    # Longitudinal torso-independent leg cage; no height band assigns
    # weights or edits an unrelated body panel.
    a=np.array([.64,.20,sign*.18]);b=np.array([.64,.96,sign*.11])
    source=sourceFaces('jeans');source=source[sign*source[:,:,2].mean(1)>.025]
    transfer=cage('jeans'+side,P[tri[mask[tri].all(1)]],source,a,b,np.linspace(.05,.85,8))
    delta[jeans]+=weights[jeans,None]*transfer(P[jeans])
result=newP+delta
tri=np.concatenate([Q[:,[0,1,2]],Q[:,[0,2,3]]])
before=np.cross(P[tri[:,1]]-P[tri[:,0]],P[tri[:,2]]-P[tri[:,0]])
after=np.cross(result[tri[:,1]]-result[tri[:,0]],result[tri[:,2]]-result[tri[:,0]])
dots=(before*after).sum(1)/np.maximum(np.linalg.norm(before,axis=1)*np.linalg.norm(after,axis=1),1e-20)
edgeBefore=np.linalg.norm(P[tri]-np.roll(P[tri],-1,axis=1),axis=2)
edgeAfter=np.linalg.norm(result[tri]-np.roll(result[tri],-1,axis=1),axis=2)
path=run/'fit04.npz';assert not path.exists()
np.savez_compressed(path,positions=result,weights=W,quads=Q,uvLoops=f['uvLoops'])
assert (root/'fit01.npz').read_bytes()==sourceBytes
report={'status':'Coherent source cross-section cage fit; unaccepted before gray/actual pose review',
        'sourceFit01SHA256':hashlib.sha256(sourceBytes).hexdigest(),
        'fit04SHA256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'weightsUVTopologyExact':True,'vertices':len(P),'quads':len(Q),
        'restNormalOpposition':int((dots<-.2).sum()),
        'restEdgeChangeQuantiles':np.quantile(edgeAfter/np.maximum(edgeBefore,1e-20),[0,.5,.9,.99,1]).tolist(),
        'displacementQuantilesM':np.quantile(np.linalg.norm(result-P,axis=1),[0,.5,.9,.99,1]).tolist(),
        'hemShiftM':float(hemShift),'seconds':time.monotonic()-start,
        'settings':{'crossSectionExtent':'Exact triangle-plane intersection min/max, deduplicated at1e-8',
                    'minimumIntersectionPoints':8,'nativeRoleBlend':'Exact fit01 anatomical weights; no hard per-vertex panel snapping',
                    'upperArmStations':[.50,.65,.85],'forearmStations':[.10,.30,.50,.70,.85],
                    'waistStations':[.10,.25,.40,.50],'legStationRange':[.05,.85],'radiusScaleGuard':[.35,3.],
                    'detail':'Low-frequency coherent cage only; original source surface not altered or decimated'},
        'profiles':profiles,'limits':['No texture bake or continuous interface join; head/hood/gloves/shoes original sources protected.',
                                    'Actual C19 pose probes, gray turntable and eventual game motion required.']}
(out/'fit-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='profiles'}))
