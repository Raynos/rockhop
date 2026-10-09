"""Independent exterior cuff containment over every recorded native pose.

All rest-covered canonical cuff rows are tested. Identical POSITION+carrier
aliases are evaluated once and explicitly account for all underlying rows.
Retained source internal caps are not claimed to be open cloth.
"""
import runpy,sys,json,time,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
D=runpy.run_path(str(Path(__file__).with_name('fit.py')))

def main(intake,fit_path,out_path):
    start=time.monotonic();out=Path(out_path);assert not out.exists();out.mkdir(parents=True)
    fit_path=Path(fit_path);report=json.loads((fit_path/'report.json').read_text());patch=np.load(fit_path/'patch.npz')
    receipt,comps=D['load'](Path(intake));h=comps['RiderHoodie'];p=h['POSITION'].astype(float);f=h['indices'];names=h['names']
    cp=patch['positionsAfter'].astype(float);cj=patch['jointsAfter'];cw=patch['weightsAfter']
    classify,canonical=D['load_canonical'](Path.cwd(),names);rest=np.linalg.inv(h['ib']);sides={};policies=[]
    for policy in report['policies']:
        side=policy['side'];g=comps['ActualSelectedGlove.'+side];gp=g['POSITION'].astype(float)
        head=np.array(policy['nativeWrist']);axis=np.array(policy['nativeForearmAxis'])
        ext=np.zeros(len(p),bool);ext[policy['sourceExteriorRowIDs']]=True
        candidates=np.flatnonzero(np.any(ext[f],axis=1));centers=p[f[candidates]].mean(1)
        normals=np.cross(p[f[candidates,1]]-p[f[candidates,0]],p[f[candidates,2]]-p[f[candidates,0]])
        radial=centers-head-((centers-head)@axis)[:,None]*axis
        _,_,_,body_signed=classify(centers,side)
        faces=candidates[(np.sum(normals*radial,axis=1)>0)&(body_signed>=0)]
        st=D['tree'](p,f[faces]);ownership,*_=classify(gp,side)
        cuff_faces=np.flatnonzero(np.any(ownership[g['indices']],axis=1));rows=np.unique(g['indices'][cuff_faces])
        # Exact geometry+carrier aliasing only; no sampling or proximity merge.
        keys=np.column_stack([gp[rows],g['JOINTS_0'][rows],g['WEIGHTS_0'][rows]])
        _,first,inverse=np.unique(keys,axis=0,return_index=True,return_inverse=True);unique_rows=rows[first]
        stations=(gp[unique_rows]-head)@axis;origins=head+stations[:,None]*axis;radial=gp[unique_rows]-origins
        radii=np.linalg.norm(radial,axis=1);directions=radial/radii[:,None];covered=[];source_margins=[]
        for k,(o,d,r) in enumerate(zip(origins,directions,radii)):
            hits=D['hits'](st,o,d,1.,1e-6);outward=[x[0] for x in hits if x[1]>0]
            if outward:covered.append(k);source_margins.append(max(outward)-r)
        covered=np.array(covered,dtype=int);covered_rows=unique_rows[covered]
        covered_aliases=rows[np.isin(inverse,covered)]
        witness_faces=[167304] if side=='L' else [74724,81481]
        for fi in witness_faces:assert np.isin(g['indices'][fi],covered_aliases).all(),'Observed cuff triangle outside coverage domain'
        sides[side]={'g':g,'faces':faces,'rows':covered_rows,'origins':origins[covered],'directions':directions[covered],'radii':radii[covered]}
        policies.append({'side':side,'sourceExteriorTriangles':len(faces),'canonicalCuffRows':len(rows),
            'restCoveredRows':len(covered_aliases),'exactGeometryCarrierRepresentatives':len(covered_rows),
            'restCoverageRowIDsSHA256':hashlib.sha256(covered_aliases.astype('<u4').tobytes()).hexdigest(),
            'restSourceRadialClearanceMeters':np.percentile(source_margins,[0,50,100]).tolist(),
            'observedWitnessFacesIncluded':witness_faces})
    result={'accepted':False,'schema':'selected-cuff-exterior-validation-v1','candidatePatchSHA256':D['sha'](fit_path/'patch.npz'),
        'fitReportSHA256':D['sha'](fit_path/'report.json'),'policies':policies,'samples':[],
        'scope':'All rest-covered canonical cuff vertices, with exact geometry and full carrier aliases accounted for, across both241-pose solver sequences. Source internal caps remain retained and are not an open-cloth acceptance.'}
    for bike,played in report['playedReports'].items():
        poses=json.loads(Path(played['path']).read_text())['played']['motionSamples'];assert len(poses)==241
        for pi,sample in enumerate(poses):
            byname={j['id']:j['worldMatrix'] for j in sample['joints']};world=np.array([byname[n] for n in names]).reshape(-1,4,4).transpose(0,2,1)
            mat=world@h['ib'];hp=D['skin'](cp,cj,cw,mat)
            for side,data in sides.items():
                ht=D['tree'](hp,f[data['faces']]);g=data['g'];rows=data['rows'];m=np.zeros((len(rows),4,4))
                for k in range(4):m+=mat[g['JOINTS_0'][rows,k]]*g['WEIGHTS_0'][rows,k,None,None]
                origins=np.einsum('nij,nj->ni',m[:,:3,:],np.column_stack([data['origins'],np.ones(len(rows))]))
                directions=np.einsum('nij,nj->ni',m[:,:3,:3],data['directions']);scales=np.linalg.norm(directions,axis=1);directions/=scales[:,None]
                margins=[];missing=[];worst=None
                for k,(o,d,r,scale) in enumerate(zip(origins,directions,data['radii'],scales)):
                    hits=D['hits'](ht,o,d,1.,1e-6);outward=[x[0] for x in hits if x[1]>0]
                    if not outward:missing.append(int(rows[k]));continue
                    clearance=max(outward)-r*scale;margins.append(clearance)
                    if worst is None or clearance<worst['clearanceMeters']:worst={'row':int(rows[k]),'clearanceMeters':float(clearance)}
                result['samples'].append({'bike':bike,'tick':sample['tick'],'side':side,'representatives':len(rows),
                    'missingSourceCoverage':len(missing),'missingRowIDs':missing,'negativeClearanceCount':int(np.sum(np.array(margins)<-1e-6)),
                    'clearanceMeters':np.percentile(margins,[0,50,100]).tolist(),'worst':worst})
            if pi%20==0:
                result['elapsedSeconds']=time.monotonic()-start;(out/'progress.json').write_text(json.dumps(result,indent=2)+'\n')
                print(json.dumps({'bike':bike,'tick':sample['tick'],'samples':len(result['samples'])}),flush=True)
    result['poseCount']=482;result['worstClearanceMeters']=min(s['clearanceMeters'][0] for s in result['samples'])
    result['missingCoverageCount']=sum(s['missingSourceCoverage'] for s in result['samples'])
    result['negativeClearanceCount']=sum(s['negativeClearanceCount'] for s in result['samples'])
    result['pass']=result['missingCoverageCount']==0 and result['negativeClearanceCount']==0
    result['elapsedSeconds']=time.monotonic()-start;(out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['samples','policies']}),flush=True)
    assert result['pass'],'Complete finite exterior clearance gate rejects candidate'
if __name__=='__main__':main(*sys.argv[sys.argv.index('--')+1:])
