"""Named-digit C2 fitting and explicit full/four skin fields, source unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def q(t):
    t=np.clip(t,0,1);return t**3*(10-15*t+6*t*t)


def normal(v):return v/np.maximum(np.linalg.norm(v,axis=-1),1e-15)[...,None]


def transported_frames(tangent,reference):
    y=normal(tangent);x=np.repeat(reference[None,:],len(y),axis=0)
    x=normal(x-y*(x*y).sum(1)[:,None]);z=np.cross(x,y)
    return np.stack([x,y,z],axis=-1)


def source_parameter(v,a,b):
    d=b-a;t=np.clip((v-a)@d/(d@d),0,1)
    center=a+t[:,None]*d;return t,center,np.linalg.norm(v-center,axis=1)


def vertex_normals(v,f):
    n=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);a=np.zeros_like(v)
    for i in range(3):np.add.at(a,f[:,i],n)
    return normal(a)


def evaluate_skin(v,weights,rest,hierarchy,names,angles):
    posed={};inverse=np.linalg.inv(rest);transforms=[]
    for i,name in enumerate(names):
        parent=hierarchy[i]['parent'];mat=rest[i].copy()
        if parent:mat=np.linalg.inv(rest[names.index(parent)])@mat
        theta=angles.get(name,0);c,s=np.cos(theta),np.sin(theta)
        rotation=np.array([[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1.]])
        posed[name]=(posed[parent] if parent else np.eye(4))@mat@rotation
        transforms.append(posed[name]@inverse[i])
    homogeneous=np.c_[v,np.ones(len(v))];result=np.zeros_like(v)
    for i,m in enumerate(transforms):
        active=weights[:,i]>0
        result[active]+=((homogeneous[active]@m.T)[:,:3])*weights[active,i,None]
    return result,np.array([posed[n]for n in names])


def main():
    p=argparse.ArgumentParser();p.add_argument('--wardrobe-data',required=True)
    p.add_argument('--semantics',required=True);p.add_argument('--foundation',required=True)
    p.add_argument('--contract',required=True);p.add_argument('--driver',required=True)
    p.add_argument('--out',required=True);p.add_argument('--evidence',required=True);a=p.parse_args()
    out,ev=Path(a.out),Path(a.evidence);assert not out.exists();out.mkdir(parents=True);ev.mkdir(parents=True,exist_ok=True)
    sourcefile=Path(a.wardrobe_data)/'gloves/retopology-prototype.npz';source=np.load(sourcefile)
    sv,sf=source['vertices'],source['faces'];sem=json.loads(Path(a.semantics).read_text())['gloves']
    foundation=np.load(a.foundation);rest=foundation['boneRest'].astype(float);names=foundation['boneNames'].tolist()
    contract=json.loads(Path(a.contract).read_text());hierarchy=contract['hierarchy']
    driver=json.loads(Path(a.driver).read_text());assert sha(a.driver)=='8c40c42af362a8d3d8ae44d27a0b07570f600b26adc66d325239413f66c7625b'
    for name in names:assert np.array_equal(np.array(driver['restBonesBlender'][name]['matrixRows'],np.float32),foundation['boneRest'][names.index(name)])
    all_reports=[]
    for side in ('R','L'):
        coarse=np.array(sem['coarsePalmRegistration'][side]['matrix']);scale=sem['coarsePalmRegistration'][side]['uniformScale']
        base=sv@coarse[:3,:3].T+coarse[:3,3];target_x=normal(rest[names.index('hand.'+side),:3,0])
        positions=[];kernels=[];channels=[];station_reports={}
        for digit in ['pinky','ring','middle','index','thumb']:
            knots=np.array(sem['digits'][digit]['fourSourceKnots']);s0,s1=knots[0],knots[-1]
            t,center,radius=source_parameter(sv,s0,s1)
            source_frame=transported_frames(np.repeat((s1-s0)[None,:],len(sv),axis=0),np.array([1.,0,0]))
            target=np.array([driver['restBonesBlender'][f'{digit}_{i:02}.{side}']['head']for i in (1,2,3)]+
                            [driver['restBonesBlender'][f'{digit}_03.{side}']['tail']])
            # The final closed shell extends slightly past actual bone tail.
            target[-1]+=.002*normal(target[-1]-target[-2])
            lengths=np.linalg.norm(np.diff(target,axis=0),axis=1);stations=np.r_[0,np.cumsum(lengths)]/lengths.sum()
            curve=CubicSpline(stations,target,axis=0,bc_type='natural')
            tc,dt=curve(t),curve(t,1);tf=transported_frames(dt,target_x)
            if side=='L':tf[:,:,2]*=-1  # Entire L radial frame is an explicit reflection.
            radial=np.einsum('nji,nj->ni',source_frame,sv-center)*scale
            # Preserve source radial coordinates while curving onto named chain.
            fitted=tc+np.einsum('nij,nj->ni',tf,radial)
            longitudinal=q(t/.30)
            support=1-q((radius-.115)/.065)
            # Thumb is deliberately localized to its separated branch; cuff/palm excluded.
            if digit=='thumb':support*=q((sv[:,0]-.23)/.12)*q((sv[:,1]+.45)/.16)
            else:support*=q((sv[:,1]-.10)/.12)
            kernel=longitudinal*support;kernels.append(kernel);positions.append(fitted)
            centers=(stations[:-1]+stations[1:])/2
            ww=np.exp(-((t[:,None]-centers[None,:])/.22)**2);ww/=ww.sum(1)[:,None]
            field=np.zeros((len(sv),51))
            for i in range(3):field[:,names.index(f'{digit}_{i+1:02}.{side}')]=ww[:,i]
            channels.append(field)
            ts=np.linspace(0,1,33);frames=transported_frames(curve(ts,1),target_x)
            if side=='L':frames[:,:,2]*=-1
            station_reports[digit]={'sourceKnots':knots.tolist(),'targetBoneKnotsMeters':target.tolist(),
                'targetStations':stations.tolist(),'stations':[{'t':float(ti),'center':ci.tolist(),'basisColumns':fi.tolist()}for ti,ci,fi in zip(ts,curve(ts),frames)],
                'activeCoreVertices':int((kernel>.9).sum()),'transitionVertices':int(((kernel>0)&(kernel<.9)).sum()),
                'radiusPolicy':'Original radial coordinates times fixed coarse palm scale; no capsule inflation/clamp.',
                'minimumFrameDeterminant':float(np.linalg.det(frames).min())}
        k=np.array(kernels).T;palm=np.prod(1-k,axis=1);denom=palm+k.sum(1)
        pweight=palm/denom;digitweights=k/denom[:,None]
        fitted=base*pweight[:,None]
        full=np.zeros((len(sv),51))
        wrist=q((-.55-sv[:,1])/.4)
        full[:,names.index('forearm.'+side)]=pweight*wrist*.85
        full[:,names.index('hand.'+side)]=pweight*(1-wrist*.85)
        for i in range(5):fitted+=positions[i]*digitweights[:,i,None];full+=channels[i]*digitweights[:,i,None]
        full/=full.sum(1)[:,None]
        top=np.argsort(-full,axis=1,kind='stable')[:,:4];w4=np.take_along_axis(full,top,axis=1)
        lost=1-w4.sum(1);w4/=w4.sum(1)[:,None];four=np.zeros_like(full)
        np.put_along_axis(four,top,w4,axis=1)
        faces=sf[:,::-1].copy() if side=='L' else sf.copy();normals=vertex_normals(fitted,faces)
        targetfile=out/('glove-'+side+'.npz')
        np.savez_compressed(targetfile,vertices=fitted,faces=faces,normals=normals,uv=source['uv'],
            jointIndices4=top.astype(np.uint16),weights4=w4.astype(np.float32),fullWeights=full.astype(np.float32),
            originalTriangleRows=source['originalTriangleRows'],barycentric=source['barycentric'],
            sourceXYZ=sv,sourceFaces=sf,sourceNormals=source['normals'],boneRest=rest.astype(np.float32),boneNames=np.array(names),
            branchWeights=digitweights.astype(np.float32),palmWeight=pweight.astype(np.float32),wristBlend=wrist.astype(np.float32))
        poses=[];loss=[];finite=True;rest_parity=0
        for frame in range(49):
            phase=2*np.pi*frame/48;flex=.5-.5*np.cos(phase)
            angles={f'{digit}_{i:02}.{side}':np.deg2rad((35 if i==1 else 55)*flex)for digit in sem['digits']for i in (1,2,3)}
            pose,mat=evaluate_skin(fitted,four,rest,hierarchy,names,angles)
            fullpose,_=evaluate_skin(fitted,full,rest,hierarchy,names,angles)
            poses.append(pose);loss.append(float(np.linalg.norm(pose-fullpose,axis=1).max()));finite&=bool(np.isfinite(pose).all())
            if frame==0:rest_parity=float(np.linalg.norm(pose-fitted,axis=1).max())
        motion=out/('flex-'+side+'.npz');np.savez_compressed(motion,positions=np.array(poses,np.float32),faces=faces,times=np.linspace(0,4,49),normals=normals)
        coverage={f'{digit}_{i:02}.{side}':int((four[:,names.index(f'{digit}_{i:02}.{side}')]>1e-5).sum())for digit in sem['digits']for i in (1,2,3)}
        assert min(coverage.values())>0 and finite and rest_parity<1e-9
        report={'side':side,'accepted':False,'candidate':{'path':str(targetfile),'sha256':sha(targetfile)},
            'motion':{'path':str(motion),'sha256':sha(motion),'frames':49,'seconds':4,'scope':'ManualLBS generic namedfingerflex 0->35/55degrees->0; no bike/grip/native/GPU claim'},
            'stations':station_reports,'mirrored':side=='L','windingReversed':side=='L','coarseDeterminant':float(np.linalg.det(coarse[:3,:3])),
            'all15FingerSegmentCoverage':coverage,'weights4SumMaxError':float(abs(w4.sum(1)-1).max()),
            'discardedFullWeightMassMax':float(lost.max()),'fullVsFourFlexMaxMeters':max(loss),'restCancellationMaxMeters':rest_parity,
            'palmCoreVertices':int((pweight>.9).sum()),'palmDigitTransitionVertices':int(((pweight>0)&(pweight<.9)).sum()),
            'wristBlendVertices':int((wrist>0).sum()),'finite':finite,
            'limits':['Semantic fitting prototype, not native or product qualification.',
                'Cavity/innerclearance and actualself/body crossings must be independently checked; radial preservation does not prove fit.',
                'Source-pervertexUV prototype aliases seams; original4096maps/densecornerUV authoritative finalbake.',
                'No propercrossing, deformedgrip, actualbike, mobile, likeness or art acceptance.']}
        all_reports.append(report);print(json.dumps({'side':side,'restParity':rest_parity,'fourLoss':max(loss),'fingerCoverage':coverage}),flush=True)
    result={'accepted':False,'status':'SEMANTIC_FITTING_FOUR_SKIN_PROTOTYPE_READY_UNACCEPTED','recipeSHA256':sha(__file__),
            'sourcePrototype':{'path':str(sourcefile),'sha256':sha(sourcefile)},'foundation':{'path':a.foundation,'sha256':sha(a.foundation)},
            'driver':{'path':a.driver,'sha256':sha(a.driver)},'canonicalHierarchyUnchanged':True,
            'sourceUVPBR':'Originalglove890f8693 ancestry; sourceXYZ/barycentric/triangleRows preserved; no map edits.',
            'curve':'NaturalCubicSpline target centerline C2; quintic C2 palm-web/root kernel; radius-preserving orthonormal frames.',
            'items':all_reports}
    (ev/'fit.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
