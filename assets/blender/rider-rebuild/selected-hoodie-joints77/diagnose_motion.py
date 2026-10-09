"""Exact two-point decomposition of observed77 actual-game field failures."""
import json
from pathlib import Path
import runpy
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
A=runpy.run_path(str(HERE/'author.py'));ROOT=A['ROOT'];pin=A['pin'];checked=A['checked']
GAME={'path':'harness/out/rider-rebuild/selected-authoring-motion11/gameplay-converted02/measured-gameplay-native-world.json',
      'sha256':'f3e0444768655bf72500a9245745a559586a7717b3f6cb6b600b6e9d1d05c153'}


def main(receipt_path,output):
    receipt_path=Path(receipt_path).resolve();output=Path(output).resolve()
    assert output.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77')and not output.exists()
    receipt=json.loads(receipt_path.read_text());a=np.load(checked(receipt['receiver']));game=json.loads(checked(GAME).read_text())
    names=game['boneNames'];rest={b['name']:b for b in game['nativeRest']['bones']}
    inv=np.linalg.inv(np.asarray([rest[n]['matrix']for n in names]));canonical=json.loads(checked(receipt['source47Receipt']).read_text())['expectedRest']
    cases=[('rookie',129,[13550,13551]),('pro',128,[13550,13551]),('pro',209,[8451,11821])]
    result=[]
    for bike,key,ids in cases:
        action=next(x for x in game['actions']if x['bike']==bike)
        world=np.asarray(action['nativeWorldMatrices'][key-1]);matrices=world@inv
        p=a['positions'][ids];weights=np.zeros((2,len(names)))
        for gi,name in enumerate(a['groupNames']):weights[:,names.index(str(name))]=a['namedFields'][ids,gi]
        active=np.flatnonzero(weights.max(0)>0);posed=np.zeros_like(p);contributions={}
        midpoint=p.mean(0);edge=p[1]-p[0];mean_weight=weights.mean(0);delta_weight=weights[1]-weights[0]
        shape=np.zeros(3);field=np.zeros(3)
        for j in active:
            m=matrices[j];q=p@m[:3,:3].T+m[:3,3];posed+=q*weights[:,j,None]
            rigid_edge=mean_weight[j]*(m[:3,:3]@edge)
            field_edge=delta_weight[j]*(m[:3,:3]@midpoint+m[:3,3])
            shape+=rigid_edge;field+=field_edge
            contributions[names[j]]={'weights':weights[:,j].tolist(),'weightDifference':float(delta_weight[j]),
                'skinMatrix':m.tolist(),'nativeWorldMatrix':world[j].tolist(),'nativeRestMatrix':rest[names[j]]['matrix'],
                'transformedRestEndpoints':q.tolist(),'meanWeightRigidEdgeContributionM':rigid_edge.tolist(),
                'weightGradientEdgeContributionM':field_edge.tolist(),
                'directWeightedEdgeContributionM':(weights[1,j]*q[1]-weights[0,j]*q[0]).tolist()}
        assert np.allclose(shape+field,posed[1]-posed[0],rtol=0,atol=2e-15)
        vertices=[]
        for local,vi in enumerate(ids):
            side='L'if p[local,0]>0 else'R';frame,lengths=A['bone_frame'](canonical,side)
            origin,axis,_,_=frame(0);elbow=frame(lengths[0])[0];_,fore_axis,_,_=frame(lengths[0]+.08)
            vertices.append({'receiverId':vi,'role':str(a['vertexRoles'][vi]),'restPosition':p[local].tolist(),
                'posedPosition':posed[local].tolist(),'upperAxisStationM':float((p[local]-origin)@axis),
                'forearmAxisStationM':float(lengths[0]+(p[local]-elbow)@fore_axis),
                'skinBlend':float(a['authoredSkinBlend'][vi]),'seamParentIds':a['authoredCapSeamParents'][vi].tolist(),
                'seamFraction':float(a['authoredCapSeamFraction'][vi]),
                'fullNamedFields':{str(n):float(w)for n,w in zip(a['groupNames'],a['namedFields'][vi])},
                'sourceOnlyFullNamedFields':{str(n):float(w)for n,w in zip(a['groupNames'],a['sourceOnlyNamedFields'][vi])}})
        twist={}
        for side in ('L','R'):
            for part in ('upper_arm','forearm'):
                n='DEF-'+part+'.'+side;i,j=names.index(n),names.index(n+'.001')
                delta=matrices[j]-matrices[i]
                twist[n]={'maximumAbsoluteSkinMatrixDifference':float(abs(delta).max()),
                          'transformedMidpointDifferenceM':float(np.linalg.norm(delta[:3,:3]@midpoint+delta[:3,3]))}
        result.append({'bike':bike,'actualKey':key,'vertices':vertices,'restEdgeLengthM':float(np.linalg.norm(edge)),
            'posedEdgeLengthM':float(np.linalg.norm(posed[1]-posed[0])),
            'edgeLengthRatio':float(np.linalg.norm(posed[1]-posed[0])/np.linalg.norm(edge)),
            'meanWeightsRigidEdgeVectorM':shape.tolist(),'meanWeightsRigidEdgeLengthM':float(np.linalg.norm(shape)),
            'weightGradientVectorM':field.tolist(),'weightGradientLengthM':float(np.linalg.norm(field)),
            'weightDifferenceL1':float(abs(delta_weight).sum()),'twistPairMeasurements':twist,'boneContributions':contributions})
    report={'status':'AUTHORED77_EXACT_ACTUAL_EDGE_DECOMPOSITION','acceptedArt':False,'recipe':pin(__file__),
            'receiverReceipt':pin(receipt_path),'gameplayMatrices':GAME,'cases':result,
            'identity':'posed edge = mean-weight rigid edge + weight-gradient edge; residual <=2e-15m in each case',
            'limits':'CPU linear skinning on exact recorded game matrices. No garment/contact/native/art acceptance.'}
    output.mkdir(parents=True);(output/'edge-decomposition.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([{k:r[k]for k in ['bike','actualKey','restEdgeLengthM','posedEdgeLengthM','edgeLengthRatio',
                    'meanWeightsRigidEdgeLengthM','weightGradientLengthM','weightDifferenceL1','twistPairMeasurements']}for r in result],indent=2))


if __name__=='__main__':main(*sys.argv[1:])
