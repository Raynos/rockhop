"""Trace selected source topology from literal12 seams, without opening Blender.

inspect writes actual cached-source cut/anchor inventory. trace derives the
two seam-owned appearance domains only after parent source review/CPU2 grant.
They are geodesic source domains, not a blanket inner/outer normal label.
Measured73 opposite-wall links expose conflicting assignments explicitly.
"""
import json
from collections import defaultdict
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bake as B

ORIGINAL={'path':'harness/out/rider-rebuild/selected-proximal-fit-review54/original01/actual-hoodie-geometry.npz',
          'sha256':'370a8bc8569113e422b66d05a8677f6d206628eb362cf731fb6903ac641e06fd'}
PRIOR12={'path':'harness/out/rider-rebuild/selected-hoodie-joints77/receiver12/receiver.json',
         'sha256':'115aeff06087f24ca0fac029846e8f492aed699273fdc2d08f7b8cc13ba85139'}
COMPACT={'path':'harness/out/rider-rebuild/selected-hoodie-production76/receiver02/receiver.npz',
         'sha256':'190307f6f6956770b03c71e0f8458cfd985cd57e9eb6fee4dd3949474754ec60'}
LINKS={'path':'harness/out/rider-rebuild/selected-anatomical-hoodie-fit73/prepare02/prepared.json',
       'sha256':'6ea9a5aef3e8de0cc3084dd1eec3a930038d8779c7552f940868195850786c33'}


def seams(a,np):
    edges=defaultdict(list);seam=set(np.flatnonzero(a['vertexRoles']=='armhole_seam'))
    for start,count,role in zip(a['polygonStarts'],a['polygonCounts'],a['faceRoles']):
        if role!='selected_retained':continue
        face=a['cornerVertexIds'][start:start+count].tolist()
        for i,j in zip(face,face[1:]+face[:1]):
            if i in seam and j in seam:edges[tuple(sorted((i,j)))].append((i,j))
    adjacency=defaultdict(list)
    for (i,j),rows in edges.items():
        if len(rows)==1:adjacency[i].append(j);adjacency[j].append(i)
    assert set(adjacency)==seam and all(len(v)==2 for v in adjacency.values())
    loops=[];seen=set()
    for first in sorted(adjacency):
        if first in seen:continue
        loop=[];previous=None;current=first
        while current not in seen:
            loop.append(current);seen.add(current)
            previous,current=current,next(v for v in adjacency[current] if v!=previous)
        assert current==first;loops.append(np.asarray(loop,np.int32))
    result={}
    for side,sign in (('L',1),('R',-1)):
        ids=np.flatnonzero(np.char.endswith(a['vertexRoles'].astype(str),'_'+side))
        rows=ids[np.argsort(a['constructionVertexIds'][ids])].reshape(63,48)
        for layer,wall in ((0,'outer'),(30,'inner')):
            first=set(rows[layer].tolist());joined=set()
            for start,count,role in zip(a['polygonStarts'],a['polygonCounts'],a['faceRoles']):
                if role!='authored_armhole_'+side:continue
                face=a['cornerVertexIds'][start:start+count]
                if first.intersection(face):joined.update(int(v) for v in face if a['vertexRoles'][v]=='armhole_seam')
            loop=next(v for v in loops if set(v)==joined)
            assert np.all(a['positions'][loop,0]*sign>0)
            result[side+':'+wall]=loop
    return result


def topology(p,f,np):
    # No distance tolerance or mesh modification. Only byte-exact selected
    # positions bridge the source's split UV/normal indices.
    unique,first,inverse=np.unique(p,axis=0,return_index=True,return_inverse=True)
    welded=inverse[f];e=np.concatenate([welded[:,[0,1]],welded[:,[1,2]],welded[:,[2,0]]])
    face=np.tile(np.arange(len(f)),3);e.sort(axis=1)
    key=e[:,0].astype(np.int64)*len(unique)+e[:,1]
    order=np.argsort(key,kind='stable');keys,index,count=np.unique(key[order],return_index=True,return_counts=True)
    edges=e[order[index]];sorted_faces=face[order]
    pairs=np.column_stack((sorted_faces[index[count==2]],sorted_faces[index[count==2]+1]))
    ambiguous=first[edges[count>2]]
    report={'denseVertices':len(p),'denseTriangles':len(f),'exactPositionVertices':len(unique),
        'edgeIncidences':{str(int(a)):int(b) for a,b in zip(*np.unique(count,return_counts=True))},
        'actualBoundaryEdges':int(np.sum(count==1)),'nonmanifoldEdgeCuts':ambiguous.tolist(),
        'exactPositionBridging':'Only equal saved float32 position triples; source mesh untouched'}
    return pairs,edges[count==2],first,inverse,report


def inspect(output):
    import numpy as np
    output=Path(output).resolve();assert output.parent==HERE and not output.exists()
    prior=B.read(PRIOR12);assert prior['original47Geometry']==ORIGINAL and prior['sourceReceiver']==COMPACT
    a=np.load(B.checked(prior['receiver']));compact=np.load(B.checked(COMPACT));original=np.load(B.checked(ORIGINAL))
    p,f=original['points'],original['faces'];_,_,_,_,report=topology(p,f,np)
    anchors={}
    for key,loop in seams(a,np).items():
        parents=a['sourceReceiverVertexIds'][loop];coefficients=a['sourceReceiverCoefficients'][loop]
        assert np.all(parents>=0) and np.all(coefficients>=0) and np.max(abs(coefficients.sum(1)-1))<1e-12
        dense=compact['sourceTriangle'][parents];bary=compact['sourceBarycentric'][parents]
        point=np.einsum('ni,nij,nijk->nk',coefficients,bary,p[f[dense]])
        anchors[key]={'prior12SeamLoop':loop.tolist(),'compactParents':parents.tolist(),
            'compactCoefficients':coefficients.tolist(),'denseTriangles':dense.tolist(),
            'denseBarycentric':bary.tolist(),'seedFaces':np.unique(dense[coefficients>0]).tolist(),
            'maximumAncestralPointToLiteralReferenceM':float(np.linalg.norm(point-a['referencePositions'][loop],axis=1).max())}
    for akey,avalue in anchors.items():
        for bkey,bvalue in anchors.items():
            if akey<bkey:assert not set(avalue['seedFaces'])&set(bvalue['seedFaces']),('Opposite actual anchors overlap',akey,bkey)
    B.write(output,{'status':'ACTUAL47_SOURCE_TOPOLOGY_AND_LITERAL12_ANCHORS_ONLY','acceptedArt':False,
        'recipe':B.pin(__file__),'sourceIntake47':B.SOURCE47,'original47':ORIGINAL,
        'prior12':PRIOR12,'compact76':COMPACT,'prior12Arrays':prior['receiver'],
        'topology':report,'anchors':anchors,'sourceWallDomainsQualified':False,
        'sourceSurfaceRawCoordinatesUsed':False,'limits':'Closed selected source needs actual closure tracing; anchors/cuts alone do not qualify same-wall cages.'})


def trace(inventory_path,output):
    """Parent-reviewed one source-domain extraction; no candidate construction."""
    import numpy as np
    from scipy.sparse import coo_array
    from scipy.sparse.csgraph import dijkstra
    inventory=json.loads(Path(inventory_path).read_text());assert inventory['recipe']==B.pin(__file__)
    original=np.load(B.checked(ORIGINAL));p,f=original['points'],original['faces']
    pairs,edges,first,inverse,report=topology(p,f,np);assert report==inventory['topology']
    centers=p[f].astype(np.float64).mean(1);weights=np.linalg.norm(centers[pairs[:,0]]-centers[pairs[:,1]],axis=1)
    assert np.all(weights>0),'Coincident source face centers require explicit ambiguity handling'
    graph=coo_array((np.r_[weights,weights],(np.r_[pairs[:,0],pairs[:,1]],np.r_[pairs[:,1],pairs[:,0]])),shape=(len(f),len(f))).tocsr()
    graph.indices=graph.indices.astype(np.int32);graph.indptr=graph.indptr.astype(np.int32)
    seeds={wall:sorted({face for key,row in inventory['anchors'].items() if key.endswith(':'+wall) for face in row['seedFaces']}) for wall in ('outer','inner')}
    outer=dijkstra(graph,indices=seeds['outer'],min_only=True,directed=False)
    inner=dijkstra(graph,indices=seeds['inner'],min_only=True,directed=False)
    label=np.full(len(f),-1,np.int8);finite=np.isfinite(outer)&np.isfinite(inner)
    label[finite&(outer<inner)]=0;label[finite&(inner<outer)]=1
    # These are literal seam-geodesic transport domains. Opposing-wall rays
    # are independent observations; conflicts remain explicit, never relabeled.
    links=B.read(LINKS);saved=np.load(B.checked(links['arrays']))
    assert np.array_equal(saved['points'],p) and np.array_equal(saved['faces'],f)
    vertex_labels=np.zeros((len(p),2),bool)
    for wall in (0,1):vertex_labels[np.unique(f[label==wall]),wall]=True
    sample=vertex_labels[saved['pairIds']];opposite=label[saved['pairFaces']]
    conflict=(opposite>=0)&sample[np.arange(len(sample)),np.maximum(opposite,0)]
    ambiguous_ids=saved['pairIds'][conflict]
    cut=pairs[:,0];other=pairs[:,1];changed=label[cut]!=label[other]
    actual_cuts=first[edges[changed]]
    adjacent=defaultdict(list)
    for a,b in actual_cuts:adjacent[int(a)].append(int(b));adjacent[int(b)].append(int(a))
    paths=[];seen=set()
    for start in sorted(adjacent):
        if start in seen:continue
        stack=[start];vertices=[]
        while stack:
            v=stack.pop()
            if v in seen:continue
            seen.add(v);vertices.append(v);stack.extend(adjacent[v])
        literal=np.asarray(vertices,np.int32)
        paths.append({'actualDenseVertices':vertices,'bounds':[p[literal].min(0).tolist(),p[literal].max(0).tolist()],
            'closedDegreeTwoLoop':all(len(adjacent[v])==2 for v in vertices),
            'ambiguousBranchVertices':[v for v in vertices if len(adjacent[v])!=2]})
    output=Path(output).resolve();assert output.is_relative_to(B.OUT) and not output.exists();output.mkdir(parents=True)
    np.savez(output/'source-domain-cuts.npz',faceDomains=label,actualCutEdges=actual_cuts,
        opposingWallConflictingVertices=ambiguous_ids,unassignedFaces=np.flatnonzero(label<0))
    B.write(output/'source-domain-report.json',{'status':'ACTUAL47_SEAM_GEODESIC_APPEARANCE_DOMAINS_UNACCEPTED',
        'recipe':B.pin(__file__),'inventory':B.pin(inventory_path),'links73':LINKS,'arrays':B.pin(output/'source-domain-cuts.npz'),
        'seedFaces':seeds,'faceCounts':{str(i):int(np.sum(label==i)) for i in (-1,0,1)},
        'actualClosureCutEdges':int(changed.sum()),'actualClosurePaths':paths,'opposingWallConflicts':int(conflict.sum()),
        'unclassified73RayVertices':links['unclassifiedWallRays'],'sourceWallDomainsQualified':False,
        'limits':'Shortest actual connected source distances from literal seam anchors; conflicting/opposite/tied cases remain unaccepted. This report is not an admission authority.'})


if __name__=='__main__':
    if sys.argv[1]=='inspect':inspect(*sys.argv[2:])
    elif sys.argv[1]=='trace':trace(*sys.argv[2:])
    else:raise AssertionError(sys.argv[1])
