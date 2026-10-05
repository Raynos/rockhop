"""Geometry-derived semantic fitting inputs; no rig/body/source edits.

Digit branches are identified on the generated single glove, then mapped to
named canonical finger chains. These are fitting centerlines, not joint proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def clusters_at_y(v,y):
    sample=v[np.abs(v[:,1]-y)<.008]
    order=np.argsort(sample[:,0]); sample=sample[order]
    cuts=np.r_[0,np.flatnonzero(np.diff(sample[:,0])>.018)+1,len(sample)]
    return [q for a,b in zip(cuts[:-1],cuts[1:]) if len(q:=sample[a:b])>10]


def segment_distance(v,a,b):
    delta=b-a
    t=np.clip(((v-a)*delta).sum(1)/(delta@delta),0,1)
    return np.linalg.norm(v-a-t[:,None]*delta,axis=1),t


def affine(source,target):
    s=np.c_[source,np.ones(len(source))]
    answer=np.linalg.lstsq(s,target,rcond=None)[0].T
    residual=np.linalg.norm(s@answer.T-target,axis=1)
    return np.vstack([answer,[0,0,0,1]]),residual


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',required=True);parser.add_argument('--foundation',required=True)
    parser.add_argument('--evidence',required=True)
    args=parser.parse_args(); data,evidence=Path(args.data),Path(args.evidence)
    body=np.load(args.foundation); names=body['boneNames'].tolist();rest=body['boneRest']
    xyz,w=body['canonicalXYZ'],body['canonicalWeights']
    heads={name:rest[i,:3,3].astype(float) for i,name in enumerate(names)}
    def endpoint(name):
        i=names.index(name);points=xyz[w[:,i]>.3];axis=rest[i,:3,1]
        assert len(points)>0
        distance=(points-heads[name])@axis
        return heads[name]+axis*np.quantile(distance,.99)
    glove=np.load(data/'gloves/cleaned-donor.npz');gv=glove['vertices']
    sections=clusters_at_y(gv,.25);assert len(sections)==4
    digit_names=['pinky','ring','middle','index']
    branches={name:q.mean(0).astype(float) for name,q in zip(digit_names,sections)}
    cuts=[(branches[a][0]+branches[b][0])/2 for a,b in zip(digit_names[:-1],digit_names[1:])]
    domains=np.digitize(gv[:,0],cuts)
    digit_info={}
    for i,name in enumerate(digit_names):
        points=gv[(domains==i)&(gv[:,1]>.2)]
        ymax=float(points[:,1].max())
        tip=points[points[:,1]>ymax-.025].mean(0).astype(float)
        base=branches[name].copy();base[1]=.16
        near=gv[(domains==i)&(np.abs(gv[:,1]-.16)<.02)]
        base[0]=np.median(near[:,0]);base[2]=np.median(near[:,2])
        digit_info[name]={'base':base.tolist(),'tip':tip.tolist(),'branchAtY025':branches[name].tolist(),
                         'fourSourceKnots':np.linspace(base,tip,4).tolist()}
    thumb_points=gv[(gv[:,0]>.35)&(gv[:,1]>-.4)]
    ymax=thumb_points[:,1].max();tt=thumb_points[thumb_points[:,1]>ymax-.025].mean(0)
    tb=np.array([.30,-.29,float(np.median(gv[(gv[:,0]>.2)&(np.abs(gv[:,1]+.29)<.02),2]))])
    digit_info['thumb']={'base':tb.tolist(),'tip':tt.tolist(),'fourSourceKnots':np.linspace(tb,tt,4).tolist()}
    # Explicit semantic branches above the palm; nearest whole-body transfer is never used.
    p=np.load(data/'gloves/retopology-prototype.npz');pv=p['vertices']
    labels=np.zeros(len(pv),np.int16); longitudinal=np.zeros(len(pv));confidence=np.ones(len(pv))
    ids={'palm':0,'pinky':1,'ring':2,'middle':3,'index':4,'thumb':5,'cuff':6}
    labels[pv[:,1]<-.6]=6
    labels[(pv[:,1]>.16)&(pv[:,0]<.40)]=np.digitize(pv[(pv[:,1]>.16)&(pv[:,0]<.40),0],cuts)+1
    thumbdist,thumbt=segment_distance(pv,tb,tt)
    thumbmask=(pv[:,0]>.30)&(pv[:,1]>-.4)&(thumbdist<.18)
    labels[thumbmask]=5
    for name,info in digit_info.items():
        mask=labels==ids[name]; a,b=np.array(info['base']),np.array(info['tip'])
        _,t=segment_distance(pv[mask],a,b);longitudinal[mask]=t
        confidence[mask]=np.clip(np.abs(pv[mask,1]-.16)/.1,0,1) if name!='thumb' else .8
    destination={};hand_matrices={}
    wrist_points=gv[np.abs(gv[:,1]+.72)<.02];wrist=wrist_points.mean(0).astype(float)
    source_y=np.array(digit_info['middle']['base'])-wrist;source_y/=np.linalg.norm(source_y)
    source_x=np.array(digit_info['index']['base'])-np.array(digit_info['pinky']['base'])
    source_x-=source_y*(source_x@source_y);source_x/=np.linalg.norm(source_x)
    source_z=np.cross(source_x,source_y);source_frame=np.stack([source_x,source_y,source_z],axis=1)
    for side in ('R','L'):
        destination[side]={}
        for name in digit_info:
            chain=[heads[f'{name}_{i:02}.{side}'] for i in (1,2,3)]
            chain.append(endpoint(f'{name}_03.{side}'))
            destination[side][name]={'canonicalKnotsMeters':np.array(chain).tolist(),
                                    'bones':[f'{name}_{i:02}.{side}' for i in (1,2,3)],
                                    'sourceKnots':digit_info[name]['fourSourceKnots']}
        target_y=heads[f'middle_01.{side}']-heads[f'hand.{side}'];length=np.linalg.norm(target_y);target_y/=length
        target_x=heads[f'index_01.{side}']-heads[f'pinky_01.{side}'];target_x-=target_y*(target_x@target_y);target_x/=np.linalg.norm(target_x)
        target_z=np.cross(target_x,target_y)
        if side=='L':target_z=-target_z
        source_length=np.linalg.norm(np.array(digit_info['middle']['base'])-wrist)
        scale=length/source_length
        matrix=np.eye(4);matrix[:3,:3]=np.stack([target_x,target_y,target_z],axis=1)@source_frame.T*scale
        matrix[:3,3]=heads[f'hand.{side}']-matrix[:3,:3]@wrist
        hand_matrices[side]={'matrix':matrix.tolist(),'uniformScale':float(scale),'sourceWristCentre':wrist.tolist(),
                             'targetWrist':heads[f'hand.{side}'].tolist(),'mirrored':side=='L','reverseWinding':side=='L',
                             'determinant':float(np.linalg.det(matrix[:3,:3]))}
    semantic=data/'gloves/semantic-regions.npz'
    np.savez_compressed(semantic,region=labels,longitudinal=longitudinal,confidence=confidence,
                        originalTriangleRows=p['originalTriangleRows'],barycentric=p['barycentric'])
    result={'accepted':False,'foundation':{'path':args.foundation,'sha256':sha(args.foundation)},
            'units':'Source uncalibrated; target native Blender meters; +Xforward/+Zup/-Yleft. RootX+.65 handled by author once.',
            'gloves':{'sourceSemantics':'Single glove; +Yfingers, +Xthumb/radial side, +Zvisible dorsal/front in original orbit.',
                      'handedness':'Right-hand reference/dorsal thumb+X consistent; explicit canonicalR mapping retained. L requires mirrored source correspondence and reversed winding; not an independently generated left glove.',
                      'digits':digit_info,'targetNamedChains':destination,'semanticRegions':{'path':str(semantic),'sha256':sha(semantic),'ids':ids,'counts':{n:int((labels==i).sum())for n,i in ids.items()}},
                      'coarsePalmRegistration':hand_matrices,
                      'limits':['Branch centerlines are geometry-derived fitting controls; no generated anatomical joint centers claimed.',
                                'Palm/web/cuff require author handling and verified body coverage; lowconfidence junctions cannot be blindly skinned.',
                                'Finaltips measured along canonical03Y from canonicalbody weights; jointcoverage/contact/nativeparity remain open.']}}
    # Jeans: lateral sourceX and vertical sourceY; front/sourceZ retained.
    jeans=np.load(data/'jeans/retopology-prototype.npz');jv=jeans['vertices'];jr=np.zeros(len(jv),np.int16)
    jr[(jv[:,1]<.32)&(jv[:,0]<0)]=1;jr[(jv[:,1]<.32)&(jv[:,0]>=0)]=2
    jr[jv[:,1]>.86]=3;jr[jv[:,1]<-.85]=4
    jp=data/'jeans/semantic-regions.npz';np.savez_compressed(jp,region=jr)
    densejeans=np.load(data/'jeans/cleaned-donor.npz')['vertices']
    source_waist=float(densejeans[:,1].max());source_cuff=float(densejeans[:,1].min())
    target_waist=float(body['boxersXYZ'][:,2].max());target_cuff=float((heads['foot.R'][2]+heads['foot.L'][2])/2+.045)
    scale=(target_waist-target_cuff)/(source_waist-source_cuff)
    jm=np.eye(4);jm[:3,:3]=np.array([[0,0,1],[1,0,0],[0,1,0]])*scale
    source_waist_centre=np.array([0,source_waist,0]);target_waist_centre=np.array([heads['pelvis'][0],0,target_waist])
    jm[:3,3]=target_waist_centre-jm[:3,:3]@source_waist_centre
    result['jeans']={'semanticRegions':{'path':str(jp),'sha256':sha(jp),'ids':{'waistTorso':0,'negativeXLeg':1,'positiveXLeg':2,'waistBand':3,'cuffs':4}},
                     'sourceFront':'+Z (fly/pockets in original orbit)','sourceUp':'+Y','negativeXLegMapsTo':'canonicalL (-Y native); proper source basis determines sides',
                     'coarseSourceWaistY':source_waist,'coarseSourceCuffY':source_cuff,
                     'measuredCanonicalUnderwearWaistZ':target_waist,'canonicalCuffZFromAnklePlus045m':target_cuff,
                     'coarseAffineToCanonicalMeters':jm.tolist(),'uniformScale':float(scale),
                     'limits':['Proper uniform basis/scale only; canonical rest legspread differs from generated straightlegs.',
                               'Crotch/hip/knees/inner space/waist/ankle overlaps remain authorfit; calibrated bounds are not fitted ports.']}
    # Boot source up+Y, toe-X, lateralZ. Sole and ankle are separate fitting regions.
    boot=np.load(data/'boots/retopology-prototype.npz');bv=boot['vertices'];br=np.zeros(len(bv),np.int16)
    br[bv[:,1]<-.42]=1;br[(bv[:,0]>.45)&(bv[:,1]<-.3)]=2;br[bv[:,1]>.22]=3;br[bv[:,0]<-.45]=4
    bp=data/'boots/semantic-regions.npz';np.savez_compressed(bp,region=br)
    canonical_foot={}
    for side in ('R','L'):
        foot=heads['foot.'+side];ball=heads['ball.'+side];toe=endpoint('ball.'+side)
        scale=float(np.linalg.norm(toe-foot)/1.8)
        # Orient toe-X to canonical+X and upY to canonical+Z. Heel/ankle offset explicit.
        basis=np.array([[-1,0,0],[0,0,1],[0,1,0]],float)
        if side=='L':basis[1]*=-1
        source_ankle=np.array([.55,.18,0]);matrix=np.eye(4);matrix[:3,:3]=basis*scale
        matrix[:3,3]=foot-matrix[:3,:3]@source_ankle
        canonical_foot[side]={'coarseSourceToMeters':matrix.tolist(),'ankleTarget':foot.tolist(),
                              'ballTarget':ball.tolist(),'toeTarget':toe.tolist(),'scale':scale,
                              'mirrored':side=='L','reverseWinding':side=='L'}
    result['boots']={'sourceToe':'-X','sourceUp':'+Y','sourceLateral':'+/-Z; anatomicalinside/outside unverified',
                     'semanticRegions':{'path':str(bp),'sha256':sha(bp),'ids':{'upper':0,'sole':1,'heel':2,'ankle':3,'toe':4}},
                     'canonicalPairs':canonical_foot,
                     'limits':['Single source; mirror creates a derivedpair, not handedness certification.',
                               'Sourceankle is geometric coarse placement (.55,.18,0); inner opening, whole sole and jointaxis require wearer fit.',
                               'Footlength estimated using weightedbody toe; no peg/ground/contact acceptance.']}
    (evidence/'semantic-registration.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'SEMANTIC_INPUTS_READY_UNACCEPTED','gloveRegions':result['gloves']['semanticRegions']['counts']}))


if __name__=='__main__':main()
