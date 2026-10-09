"""One connected skin-brush band for the measured77 armhole discontinuity.

CPU-only source. Does not alter geometry, UV, rig or source donor fields. The
parent must checkpoint the rejected08 result before authorizing this run.
"""
import heapq
import json
from pathlib import Path
import runpy
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
A=runpy.run_path(str(HERE/'author.py'));ROOT=A['ROOT'];pin=A['pin'];checked=A['checked']
SOURCE_RECEIPT={'path':'harness/out/rider-rebuild/selected-hoodie-joints77/receiver08/receiver.json',
                'sha256':'9775c8c459b2780d8a6b8f1cf6765bacf15efc239f87d7a58ec15371f6e17ce4'}


def graph(a):
    edges=set()
    for start,count in zip(a['polygonStarts'],a['polygonCounts']):
        f=a['cornerVertexIds'][start:start+count]
        for i,j in zip(f,np.roll(f,-1)):edges.add(tuple(sorted((int(i),int(j)))))
    edges=np.asarray(sorted(edges),np.int32)
    length=np.linalg.norm(a['positions'][edges[:,1]]-a['positions'][edges[:,0]],axis=1)
    assert np.all(length>0)
    neighbors=[[]for _ in a['positions']]
    for (i,j),d in zip(edges,length):neighbors[i].append((int(j),float(d)));neighbors[j].append((int(i),float(d)))
    return edges,length,neighbors


def distances(neighbors,seeds):
    value=np.full(len(neighbors),np.inf);value[seeds]=0.;queue=[(0.,int(i))for i in seeds];heapq.heapify(queue)
    while queue:
        distance,i=heapq.heappop(queue)
        if distance!=value[i]:continue
        for j,length in neighbors[i]:
            candidate=distance+length
            if candidate<value[j]:value[j]=candidate;heapq.heappush(queue,(candidate,j))
    return value


def verify(receipt_path):
    path=Path(receipt_path).resolve();row=json.loads(path.read_text())
    repair=row['fieldRepair'];assert repair['recipe']==pin(__file__) and repair['status']=='CONNECTED_ARMHOLE_FIELD_REPAIR_UNACCEPTED'
    assert repair['input']==SOURCE_RECEIPT
    source=json.loads(checked(repair['input']).read_text())
    assert source['recipe']==pin(HERE/'author.py')
    before=np.load(checked(source['receiver']));after=np.load(checked(row['receiver']))
    for key in before.files:
        if key=='namedFields':continue
        assert np.array_equal(before[key],after[key]),('Geometry/source drift',key)
    assert np.array_equal(after['priorNamedFields'],before['namedFields'])
    active=after['fieldRepairActive']
    assert active.dtype==np.bool_ and active.shape==(len(before['positions']),)
    assert after['namedFields'].shape==before['namedFields'].shape
    assert after['namedFields'].dtype==before['namedFields'].dtype
    assert np.array_equal(after['namedFields'][~active],before['namedFields'][~active])
    assert np.isfinite(after['namedFields']).all() and after['namedFields'].min()>=0
    assert np.max(abs(after['namedFields'].sum(1)-1))<3e-7
    checked(repair['diagnostic']);return row


def main(output):
    # This Python3.13 SciPy is already installed by the parent's existing73
    # lane. It is imported only for this explicit CPU solve, never by verify.
    sys.path.insert(0,str(ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit73/python'))
    from scipy.sparse import coo_matrix
    from scipy.sparse.linalg import spsolve
    output=Path(output).resolve()
    assert output.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77')and not output.exists()
    source=json.loads(checked(SOURCE_RECEIPT).read_text())
    assert source['recipe']==pin(HERE/'author.py')
    a=dict(np.load(checked(source['receiver'])))
    rest=json.loads(checked(source['source47Receipt']).read_text())['expectedRest']
    edges,length,neighbors=graph(a)
    seam=np.flatnonzero(a['vertexRoles']=='armhole_seam');distance=distances(neighbors,seam)
    p=a['positions'];roles=a['vertexRoles']
    # Explicit skin-paint domain: source torso collar within85mm geodesic of
    # the cut, below the healthy hood, plus authored cap/proximal upper sleeve.
    # Distal elbow/twist fields and untouched torso remain exact anchors.
    torso=(roles=='selected_original')&(distance<.085)&(p[:,2]>1.15)&(p[:,2]<1.49)&(abs(p[:,0])>.055)
    active=torso|(roles=='armhole_seam')
    for side in ('L','R'):
        frame,bone_lengths=A['bone_frame'](rest,side);origin,axis,_,_=frame(0)
        side_rows=np.asarray([str(r).endswith('_'+side)for r in roles])
        active|=side_rows&(((p-origin)@axis)<bone_lengths[0]-.045)
    unknown=np.flatnonzero(active);index=np.full(len(p),-1,np.int32);index[unknown]=np.arange(len(unknown))
    rows=[];columns=[];values=[];rhs=np.zeros((len(unknown),len(a['groupNames'])))
    for i in unknown:
        total=0.
        for j,d in neighbors[i]:
            weight=1/d;total+=weight
            if active[j]:rows.append(index[i]);columns.append(index[j]);values.append(-weight)
            else:rhs[index[i]]+=weight*a['namedFields'][j]
        rows.append(index[i]);columns.append(index[i]);values.append(total)
    matrix=coo_matrix((values,(rows,columns)),shape=(len(unknown),len(unknown))).tocsr()
    solved=spsolve(matrix,rhs)
    residual=matrix@solved-rhs
    assert np.isfinite(solved).all()and solved.min()>-1e-12 and np.max(abs(solved.sum(1)-1))<2e-6
    # Roundoff only; positive harmonic interpolation obeys the maximum rule.
    solved=np.maximum(solved,0);solved/=solved.sum(1)[:,None]
    fields=a['namedFields'].copy();fields[unknown]=solved.astype(np.float32)
    before=a['namedFields'].copy();a.update(namedFields=fields,priorNamedFields=before,
        fieldRepairActive=active,fieldRepairGeodesicDistanceM=np.where(np.isfinite(distance),distance,-1.))
    output.mkdir(parents=True);np.savez(output/'receiver.npz',**a)
    diagnostic={'input':SOURCE_RECEIPT,'recipe':pin(__file__),'acceptedArt':False,
        'activeVertices':len(unknown),'sourceTorsoCollarVertices':int(torso.sum()),'geodesicBrushWidthM':.085,
        'geodesicDistanceMissingValue':-1.,'verticesDisconnectedFromSeam':int((~np.isfinite(distance)).sum()),
        'maximumAbsoluteLinearResidual':float(abs(residual).max()),
        'maximumNamedFieldChange':float(abs(fields-before).max()),
        'allOutsideRowsExact':bool(np.array_equal(fields[~active],before[~active])),
        'fieldMinimum':float(fields.min()),'maximumStoredRowSumError':float(abs(fields.sum(1)-1).max()),
        'method':'Positive inverse-edge-length harmonic interpolation on one sewn garment topology. Original far-torso and distal native75 limb fields are exact Dirichlet anchors.',
        'limits':'Skin brush design only. All482 actual geometry and finite body/glove checks remain required; no bone/rest, selected geometry or UV edits.'}
    (output/'field-repair.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
    row=dict(source);row['receiver']=pin(output/'receiver.npz')
    row['fieldRepair']={'status':'CONNECTED_ARMHOLE_FIELD_REPAIR_UNACCEPTED','recipe':pin(__file__),
                        'input':SOURCE_RECEIPT,'diagnostic':pin(output/'field-repair.json')}
    row['correspondenceAndSkin']=dict(source['correspondenceAndSkin'],skinStatus=diagnostic['method'],
        fieldRepairActiveVertices=len(unknown),sourceFarFieldAnchorsExact=True,
        healthyFieldsExactBeforeFloat32=False)
    row['limitations']=[*source['limitations'],'The connected armhole skin-brush band changes local source torso-collar fields; far anchors and all original source files stay exact.']
    (output/'receiver.json').write_text(json.dumps(row,indent=2)+'\n');verify(output/'receiver.json')
    print(json.dumps(diagnostic),flush=True)


if __name__=='__main__':main(sys.argv[1])
