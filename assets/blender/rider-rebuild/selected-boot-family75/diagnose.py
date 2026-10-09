"""Retain all actual right failures and classify foot evidence anatomically."""
import json
from pathlib import Path
import numpy as np
import prepare as p


def main():
    evidence=p.ROOT/'docs/evidence/rider-rebuild/selected-boot-family75'
    preflight=evidence/'preflight.json';report=json.loads(preflight.read_text())
    assert report['status']=='RIGHT_TOPOLOGY_REUSE_REJECTED_NO_NATIVE_OR_OPTIMIZER'
    p.intake.pin(p.ROOT/report['source']['path'],report['source']['sha256'])
    source=json.loads((p.ROOT/report['source']['path']).read_text());a=p.intake.arrays(source['arrays'])
    p.intake.pin(p.intake.RECEIPT,p.intake.RECEIPT_SHA)
    constructor=json.loads(p.intake.RECEIPT.read_text());prior=p.intake.arrays(constructor['finalFanProtection'])
    right=report['sides']['R'];requested={row['originalVertexId'] for row in right['vertex']['failures']}
    for row in right['face']['failures']:
        assert not row['exactInheritedSourceFace'];requested.update(row['originalVertexIds']);requested.update(row['sourceBearingOriginalVertexIds'])
    assert len(right['vertex']['failures'])==4 and len(right['face']['failures'])==28
    old=set(prior['centerOriginalVertexIds'].tolist());centers=np.array(sorted(old|requested),'<u4')
    f=a['RTriangles'].reshape(-1,3);positions=a['RPositions'].reshape(-1,3)
    edge_rows=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]).astype(np.int64)
    edge_keys=np.minimum(edge_rows[:,0],edge_rows[:,1])*len(positions)+np.maximum(edge_rows[:,0],edge_rows[:,1])
    _,edge_counts=np.unique(edge_keys,return_counts=True)
    topology={'uniqueEdges':len(edge_counts),'boundaryEdges':int((edge_counts==1).sum()),'nonmanifoldEdges':int((edge_counts>2).sum())}
    assert topology['boundaryEdges']==topology['nonmanifoldEdges']==0
    face_ids=np.flatnonzero(np.isin(f,centers).any(1)).astype('<u4');patch=f[face_ids]
    vertices=np.unique(patch).astype('<u4');edges=np.unique(np.sort(np.concatenate([patch[:,[0,1]],patch[:,[1,2]],patch[:,[2,0]]]),axis=1),axis=0).astype('<u4')
    assert np.isin(prior['requiredSourceFaceIds'],face_ids).all()
    proof=p.package(p.ROOT/'harness/out/rider-rebuild/selected-boot-family75/cpu01/right-protection.bin',
        {'centerOriginalVertexIds':centers,'lockedOriginalVertexIds':vertices,'requiredSourceFaceIds':face_ids,'requiredEdgesOriginal':edges})
    failures=right['face']['failures'];failed_ids=np.array([r['targetFaceId'] for r in failures],'<i4')
    target=a['RCandidateOriginalTriangles'].reshape(-1,3)[failed_ids]
    bearing_ids=np.array(sorted({i for row in failures for i in row['bearingSourceFaceIds']}),'<i4')
    geometry=p.package(p.ROOT/'harness/out/rider-rebuild/selected-boot-family75/cpu01/right-failure-geometry.bin',
        {'targetFaceIds':failed_ids,'targetOriginalVertexIds':target.astype('<u4'),'targetCoordinates':positions[target],
         'bearingSourceFaceIds':bearing_ids,'bearingOriginalVertexIds':f[bearing_ids].astype('<u4'),'bearingCoordinates':positions[f[bearing_ids]]})
    p.intake.pin(p.BODY,p.BODY_SHA);body=dict(np.load(p.BODY));names=body['jointNames'].tolist();classes={}
    for side in ('L','R'):
        outside=np.array(report['sides'][side]['actualNative02FootEnclosure']['outsideOriginalBodyVertexIds'])
        q=body['vertices'][outside];top=float(a[side+'Positions'].reshape(-1,3)[:,2].max())
        ankle=body['jointHeads'][names.index('DEF-foot.'+side)];toe=body['jointHeads'][names.index('DEF-toe.'+side)]
        forward=toe[:2]-ankle[:2];forward/=np.linalg.norm(forward)
        heel=(q[:,:2]-ankle[:2])@forward<=0
        toe_domain=body['nativeCoefficients'][outside,names.index('DEF-toe.'+side)]>body['nativeCoefficients'][outside,names.index('DEF-foot.'+side)]
        def subset(mask):return outside[mask].tolist()
        classes[side]={'allOutsideCount':len(outside),'sourceMaximumZM':top,
            'aboveEntireSourceTopOriginalIds':subset(q[:,2]>top),
            'atOrBelowOriginal107mmCoverageOriginalIds':subset(q[:,2]<=.107),
            'aboveOriginal107mmCoverageOriginalIds':subset(q[:,2]>.107),
            'heelwardOfNativeAnkleOriginalIds':subset(heel),
            'toeWeightDominantOriginalIds':subset(toe_domain),
            'atOrBelowOriginal6mmSoleProtectionOriginalIds':subset(q[:,2]<=.006),
            'outsideBoundsM':[q.min(0).tolist(),q.max(0).tolist()],
            'limits':'Domain lists overlap. Source maximum Z proves only the above-entire-source subset.107mm coverage and6mm sole band reuse existing boot-last-anatomical04 policy; neither is a new clearance gate. Outside ray parity is not automatically failed enclosure or material penetration.'}
    finding={'status':'COMPLETE_RIGHT_LOCAL_REPAIR_SEED_NATIVE_SOURCE_CENSUS_REQUIRED','acceptedArt':False,
        'preflight':p.intake.pin(preflight,p.intake.sha(preflight)),'recipe':p.intake.pin(Path(__file__),p.intake.sha(__file__)),
        'native70':source['native70'],'canonicalNative02':source['canonicalNative02'],
        'priorQualifiedLeftConstructor':p.intake.pin(p.intake.RECEIPT,p.intake.RECEIPT_SHA),
        'priorQualifiedProtection':constructor['finalFanProtection'],'rightOriginalTopology':topology,
        'actualVertexFailures':right['vertex']['failures'],'actualFaceFailures':failures,'actualFailureGeometry':geometry,
        'priorQualifiedCenters':len(old),'allFailureDerivedCenters':sorted(requested),'addedCenters':sorted(requested-old),
        'totalCenters':len(centers),'exactRequiredFaces':len(face_ids),'protection':proof,'outsideFootDomainClassification':classes,
        'construction':'Reuse unchanged37 fields/topology/compaction,59 exact-fan retention,62 vertex census and67 full-source tree/face census/monotone failure union on actual RIGHT native arrays. Keep original ErrorAbsolute,1mm,.25,skin/FOUR bounds and soft8k target. No mirrored fitting or dense-right bake fallback.',
        'limits':'The67 entry point itself pins left ancestry; a right-specific intake is required. Right native normals, corner UVs and full named fields must be read and witnessed before that existing construction can run. No optimizer/native/bake executed; no pair, enclosure, scene-budget or art acceptance.'}
    (evidence/'right-repair.json').write_text(json.dumps(finding,indent=2)+'\n')
    print(json.dumps({'centers':len(centers),'addedCenters':len(requested-old),'requiredFaces':len(face_ids),
        'outsideDomains':{side:{key:len(value) for key,value in row.items() if key.endswith('OriginalIds')} for side,row in classes.items()}}))


if __name__=='__main__':main()
