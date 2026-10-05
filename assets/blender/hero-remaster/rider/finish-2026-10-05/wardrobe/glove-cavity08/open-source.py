"""One exactly admitted array-only cuff opening; no fit, skin or source overwrite."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for key in ['preflight','parent-scope','scope-sha256','dense','base-color','metallic-roughness','out','evidence']:
        parser.add_argument('--'+key,required=True)
    args=parser.parse_args();assert sha(args.parent_scope)==args.scope_sha256
    scope=json.loads(Path(args.parent_scope).read_text());assert scope['status']=='PARENT_EDGE_GRAPH_READBACK_PASS_DIAGNOSTIC_CUT_SCOPE_ADMITTED' and not scope['acceptedWearable'];assert scope['isolatedSourceTriangle']==5167 and scope['boundedNextScope']['keepFaces']==14543
    p=json.loads(Path(args.preflight).read_text());assert sha(p['source']['path'])==p['source']['sha256'];assert sha(p['output']['path'])==p['output']['sha256'];source=np.load(p['source']['path']);mask=np.load(p['output']['path']);faces,vertices=source['faces'],source['vertices'];assert np.array_equal(mask['sourceFaces'],faces) and np.array_equal(mask['sourceXYZ'],vertices)
    remove=mask['faceRemoveCandidate'].copy();assert int(remove.sum())==1456 and not remove[5167];assert not (remove&mask['protectedDistalFaces']).any();remove[5167]=True
    assert int(remove.sum())==1457 and not (remove&mask['protectedDistalFaces']).any()
    retained_rows=np.flatnonzero(~remove);retained=faces[retained_rows];assert len(retained)==14543
    # Preserve every original vertex row and attribute, including unused rows.
    arrays={key:source[key]for key in source.files};arrays['faces']=retained
    arrays['sourcePrototypeFaceRows']=retained_rows;arrays['sourceVertexRows']=np.arange(len(vertices));arrays['removedSourceFaceRows']=np.flatnonzero(remove);arrays['sourceOriginalFaces']=faces;arrays['cornerUVPrototype']=source['uv'][retained]
    dense=np.load(args.dense);lookup={int(row):index for index,row in enumerate(dense['originalTriangleRows'])};dense_rows=np.array([lookup[int(row)]for row in source['originalTriangleRows']]);bary=source['barycentric'];mapped_xyz=(dense['vertices'][dense['faces'][dense_rows]]*bary[:,:,None]).sum(1);mapped_uv=(dense['originalCornerUV'][dense_rows]*bary[:,:,None]).sum(1)
    xyz_error=float(np.linalg.norm(mapped_xyz-vertices,axis=1).max());uv_error=float(abs(mapped_uv-source['uv']).max());assert xyz_error<1e-12 and uv_error<1e-12
    # Combinatorial topology of retained faces; unused original vertices ignored.
    edges={};neighbors=[[]for _ in retained]
    for row,face in enumerate(retained):
        for a,b in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]:edges.setdefault(tuple(sorted([int(a),int(b)])),[]).append(row)
    boundary=np.array([edge for edge,rows in edges.items()if len(rows)==1],int);assert len(boundary)==71 and all(len(rows)<=2 for rows in edges.values())
    directedBalance={edge:0 for edge in edges}
    for face in retained:
        for a,b in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]:directedBalance[tuple(sorted([int(a),int(b)]))]+=1 if a<b else -1
    assert all(directedBalance[edge]==0 if len(rows)==2 else abs(directedBalance[edge])==1 for edge,rows in edges.items())
    euler=int(len(np.unique(retained))-len(edges)+len(retained));assert euler==-1
    for edge,rows in edges.items():
        if len(rows)==2:a,b=rows;neighbors[a].append(b);neighbors[b].append(a)
    remaining=set(range(len(retained)));components=[]
    while remaining:
        stack=[min(remaining)];region=[]
        while stack:
            row=stack.pop()
            if row not in remaining:continue
            remaining.remove(row);region.append(row);stack.extend(n for n in neighbors[row]if n in remaining)
        components.append(region)
    assert len(components)==1 and len(components[0])==14543
    degree=np.bincount(boundary.ravel(),minlength=len(vertices));assert (degree[degree>0]==2).all()
    bn={int(i):[]for i in np.flatnonzero(degree)}
    for a,b in boundary:bn[int(a)].append(int(b));bn[int(b)].append(int(a))
    first=min(bn);ordered=[first];previous=-1;current=first
    while True:
        nxt=next(i for i in bn[current]if i!=previous)
        if nxt==first:break
        ordered.append(nxt);previous,current=current,nxt
    assert len(ordered)==71 and set(ordered)==set(bn)
    # No output before all scope, geometry, provenance and topology assertions pass.
    out=Path(args.out);assert not out.exists();out.mkdir(parents=True);ev=Path(args.evidence);ev.mkdir(parents=True,exist_ok=True);candidate=out/'open-glove-source.npz';np.savez_compressed(candidate,**arrays)
    read=np.load(candidate);assert np.array_equal(read['vertices'],vertices) and np.array_equal(read['faces'],retained) and np.array_equal(read['cornerUVPrototype'],source['uv'][faces][retained_rows])
    preserved={key:bool(np.array_equal(read[key],source[key]))for key in source.files if key!='faces'};assert all(preserved.values())
    assert sha(p['source']['path'])==p['source']['sha256'] and sha(p['output']['path'])==p['output']['sha256'];assert sha(args.parent_scope)==args.scope_sha256
    report={'accepted':False,'status':'EXACT_SCOPE_DIAGNOSTIC_OPEN_SOURCE_DERIVATIVE_CREATED_UNACCEPTED','recipeSHA256':sha(__file__),'parentScope':{'path':args.parent_scope,'sha256':args.scope_sha256},'preflight':{'path':args.preflight,'sha256':sha(args.preflight)},'source':p['source'],'mask':p['output'],'denseSource':{'path':args.dense,'sha256':sha(args.dense)},'maps':{name:{'path':path,'sha256':sha(path)}for name,path in [('baseColor',args.base_color),('metallicRoughness',args.metallic_roughness)]},'candidate':{'path':str(candidate),'sha256':sha(candidate)},'removedFaceRows':np.flatnonzero(remove).tolist(),'retainedFaces':len(retained),'allOriginalXYZRows':len(vertices),'referencedVertices':len(np.unique(retained)),'unusedRetainedOriginalVertexRows':len(vertices)-len(np.unique(retained)),'originalAttributesExact':preserved,'retainedTrianglesExact':True,'retainedPrototypeCornerUVExact':True,'denseXYZBarycentricReconstructionMaxError':xyz_error,'denseCornerUVBarycentricProjectionMaxError':uv_error,'protectedDistalFacesRemoved':0,'topology':{'faceComponents':len(components),'componentFaces':[len(region)for region in components],'boundaryEdges':len(boundary),'boundaryLoops':1,'orderedSourceBoundaryVertexIds':ordered,'boundaryDegreeNotTwo':0,'nonmanifoldEdges':0,'eulerCharacteristicReferencedMesh':euler,'consistentInteriorEdgeOrientation':True,'genusConnectedOrientableOneBoundary':1},'limits':['Diagnostic source topology derivative only; no registration, fit, skin, body/native/model/render or wearable qualification.','All8000source vertex/attribute rows retained; unused rows disclosed and not counted as isolated face components.','Per-vertex dense corner-UV ancestry is exact; UV seam/corner bake qualification remains open. Original maps remain immutable.','Referenced connected orientable shell has Euler-1 and one boundary, implying genus1. The remaining handle/other passage must be located before fit; single cuff boundary does not certify normal finger/palm enclosure, mouth passage or wearable appearance.']}
    (ev/'opening.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'candidate':report['candidate'],'faces':len(retained),'boundary':71,'components':1,'unusedVertices':report['unusedRetainedOriginalVertexRows']}))


if __name__=='__main__':main()
