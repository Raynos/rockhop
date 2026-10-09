"""One whole-garment bind from the actual complete wearer's own full fields.

Derivative weights are replaced throughout; selected source fields remain
ancestry. Geometry and preview UV are untouched. No bone alias or top-four drop.
"""
import json
from pathlib import Path
import runpy
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
A=runpy.run_path(str(HERE/'author.py'));ROOT=A['ROOT'];pin=A['pin'];checked=A['checked']
INPUT={'path':'harness/out/rider-rebuild/selected-hoodie-joints77/receiver10/receiver.json',
       'sha256':'24972524311e809b3166ba263065f8757aabe2786077a746d8d58c2854723d5b'}
BODY={'path':'harness/out/rider-rebuild/selected-hoodie-joints77/body-guide01/actual-body-fields.json',
      'sha256':'8fb18ac1722439375e3fa30a3b72b9696fb8d2459d4747892d3a454e6f2be6e3'}
PRIOR={'path':'assets/blender/rider-rebuild/selected-hoodie-joints77/anatomical_fields.py',
       'sha256':'67bce423a81362f517c88f7c1a2b927df18b1d7967911b0186120bc2d04a80c4'}


def inputs():
    previous=runpy.run_path(str(checked(PRIOR)))['verify'](checked(INPUT))
    body=json.loads(checked(BODY).read_text())
    assert body['status']=='ACTUAL47_COMPLETE_REFERENCE_FULL_FIELDS_READ_ONLY'and body['nativeMutation']is False
    assert body['sourceReceipt']==previous['source47Receipt']and body['originalBodyCache']==previous['fullBody']
    rest=json.loads(checked(previous['source47Receipt']).read_text())['expectedRest'];assert body['rest']==rest
    for key in ('recipe','native','component','originalBodyCache','arrays'):checked(body[key])
    return previous,body


def verify(receipt_path):
    row=json.loads(Path(receipt_path).read_text());bind=row['wearerFieldBinding']
    assert bind['recipe']==pin(__file__)and bind['input']==INPUT and bind['bodyGuide']==BODY
    assert bind['status']=='ACTUAL_COMPLETE_WEARER_FULL_FIELD_TRANSFER_UNACCEPTED'
    previous,body=inputs();before=np.load(checked(previous['receiver']));after=np.load(checked(row['receiver']))
    for key in before.files:
        if key not in ('namedFields','priorNamedFields'):assert np.array_equal(before[key],after[key]),key
    assert np.array_equal(after['priorNamedFields'],before['namedFields'])
    assert np.array_equal(after['anatomical10PriorNamedFields'],before['priorNamedFields'])
    source=np.load(checked(body['arrays']));tri=source['triangles'][after['wearerTriangleIds']]
    bary=after['wearerBarycentric'];assert np.isfinite(bary).all()and bary.min()>=-1e-12
    assert np.max(abs(bary.sum(1)-1))<1e-12
    names=after['groupNames'].tolist();body_names=source['groupNames'].tolist()
    sampled=np.sum(source['normalizedNamedFields'][tri]*bary[:,:,None],axis=1)
    expected=np.zeros(after['namedFields'].shape,np.float64)
    for j,n in enumerate(body_names):
        if n in names:expected[:,names.index(n)]=sampled[:,j]
        else:assert np.max(abs(sampled[:,j]))==0,('Unrepresented actual body field',n)
    assert np.array_equal(after['namedFields'],expected.astype(np.float32))
    assert np.isfinite(after['namedFields']).all()and after['namedFields'].min()>=0
    assert np.max(abs(after['namedFields'].sum(1)-1))<3e-7
    checked(bind['diagnostic']);return row


def main(output):
    # Existing installed CPU dependency; exact geometry queries, no optimizer.
    sys.path.insert(0,str(ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit73/python'))
    from scipy.spatial import cKDTree
    output=Path(output).resolve()
    assert output.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77')and not output.exists()
    previous,body=inputs();a=dict(np.load(checked(previous['receiver'])));b=np.load(checked(body['arrays']))
    p=a['positions'];bp=b['positions'].astype(np.float64);bf=b['triangles'];t=bp[bf]
    centers=t.mean(1);radius=np.linalg.norm(t-centers[:,None],axis=2).max(1);max_radius=float(radius.max())
    vertex_tree=cKDTree(bp);face_tree=cKDTree(centers);bound=vertex_tree.query(p)[0]
    # Floating-point query roundoff only, not a geometry acceptance margin.
    bound+=32*np.finfo(np.float64).eps*np.maximum(1.,bound)
    ids=np.zeros(len(p),np.int32);bary=np.zeros((len(p),3));samples=np.zeros_like(p);distance=np.zeros(len(p))
    candidates=[];body_names=b['groupNames'].tolist();names=a['groupNames'].tolist();fields=np.zeros_like(a['namedFields'])
    for vi,point in enumerate(p):
        # A triangle closer than the nearest body vertex has its center at
        # most bound + its enclosing radius. This includes every possible
        # nearest triangle; the following bbox test only removes impossibles.
        ci=np.asarray(face_tree.query_ball_point(point,np.nextafter(bound[vi]+max_radius,np.inf)),np.int32)
        low=t[ci].min(1);high=t[ci].max(1);gap=np.maximum(low-point,0)+np.minimum(high-point,0)
        ci=ci[np.sum(gap*gap,axis=1)<=np.nextafter(bound[vi]*bound[vi],np.inf)]
        assert len(ci)>0
        surface=A['Surface'](bp,bf[ci]);surface.points=surface.tri.reshape(-1,3)
        face,weights,q,_,signed=surface.nearest(point);ids[vi]=ci[face];bary[vi]=weights;samples[vi]=q;distance[vi]=abs(signed)
        sampled=np.sum(b['normalizedNamedFields'][bf[ids[vi]]]*weights[:,None],axis=0)
        for j,n in enumerate(body_names):
            if n in names:fields[vi,names.index(n)]=sampled[j]
            else:assert sampled[j]==0,('Unrepresented actual body field',n)
        candidates.append(len(ci))
    before=a['namedFields'].copy();prior=a['priorNamedFields'].copy()
    a.update(namedFields=fields,priorNamedFields=before,anatomical10PriorNamedFields=prior,
             wearerTriangleIds=ids,wearerBarycentric=bary,wearerSamplePoints=samples,wearerDistanceM=distance)
    output.mkdir(parents=True);np.savez(output/'receiver.npz',**a)
    counts,frequency=np.unique((fields>0).sum(1),return_counts=True)
    report={'acceptedArt':False,'input':INPUT,'bodyGuide':BODY,'recipe':pin(__file__),
        'allReceiverVerticesBound':len(p),'geometryUVAncestryUnchanged':True,
        'supportCountHistogram':{str(k):int(v)for k,v in zip(counts,frequency)},
        'distancePercentilesM':np.percentile(distance,[0,50,95,99,100]).tolist(),
        'exactNearestCandidateCountPercentiles':np.percentile(candidates,[0,50,95,100]).tolist(),
        'method':'One whole-object nearest-face-interpolated transfer of actual complete wearer normalized full fields. Exact triangle+barycentric witnesses. No original donor weight anchors.',
        'controlInventory':len(names),'productionFourConditioned':False,
        'limits':'Standard bind candidate only. Axillary/hood nearest-surface branch selection and all actual motion remain measurable; no contact, GPU, production-four or art pass.'}
    (output/'wearer-fields.json').write_text(json.dumps(report,indent=2)+'\n')
    row=dict(previous);row['receiver']=pin(output/'receiver.npz');row['priorAnatomicalFieldRepair']=row.pop('anatomicalFieldRepair')
    row['wearerFieldBinding']={'status':'ACTUAL_COMPLETE_WEARER_FULL_FIELD_TRANSFER_UNACCEPTED',
        'input':INPUT,'bodyGuide':BODY,'recipe':pin(__file__),'diagnostic':pin(output/'wearer-fields.json')}
    row['correspondenceAndSkin']=dict(previous['correspondenceAndSkin'],skinStatus=report['method'],
        healthyFieldsExactBeforeFloat32=False,sourceFarFieldAnchorsExact=False,
        wholeWearerTransferredVertices=len(p),
        originalSelectedFieldRowsExactAfterTransfer=int(np.all(fields==a['sourceOnlyNamedFields'],axis=1).sum()))
    for key in ('newAnatomicalFieldVertices','unchangedFieldVertices','fieldRepairActiveVertices'):
        row['correspondenceAndSkin'].pop(key,None)
    row['previousFieldLimitations']=previous['limitations']
    row['limitations']=['All derivative fields replaced from actual wearer; original selected fields retained as ancestry only.',
        'Nearest-body branch ownership, generic/heldout and actual game deformation remain unqualified.',
        'No native/GPU parity, finite garment contact, genuine atlas/detail bake, production-four or played art pass.']
    (output/'receiver.json').write_text(json.dumps(row,indent=2)+'\n');verify(output/'receiver.json')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main(sys.argv[1])
