"""Independent saved-native readback, parent CPU2 lease only; no render/save."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def rest(rig):
    return [{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':[list(r) for r in b.matrix_local],'connect':b.use_connect,'deform':b.use_deform} for b in rig.data.bones]

def rows(body):
    ids=body.data.attributes['_SOURCE_VERTEX_ID'].data;groups={g.index:g.name for g in body.vertex_groups}
    result={}
    for v in body.data.vertices:
        identity=int(ids[v.index].value)
        if 0<=identity<1000000:
            assert identity not in result
            result[identity]=(tuple(v.co),sorted((groups[g.group],g.weight) for g in v.groups))
    return result

def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==1
    out=Path(args[0]).resolve();report=json.loads((out/'report.json').read_text())
    candidate=ROOT/report['candidate']['path'];assert sha(candidate)==report['candidate']['sha256']
    source=ROOT/'harness/out/rider-rebuild/native-hand-repair01/native02/anatomical-hand-rig.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source));before_rest=rest(bpy.data.objects['RiderSkeleton']);before_rows=rows(bpy.data.objects['RiderBody'])
    arrays=np.load(source.with_name('native-body.npz'));hands=set(map(int,arrays['nativeSourceVertexIds'][arrays['newFieldBlendAlpha']>0]))
    bpy.ops.wm.open_mainfile(filepath=str(candidate));body=bpy.data.objects['RiderBody'];rig=bpy.data.objects['RiderSkeleton'];after_rows=rows(body)
    assert rest(rig)==before_rest
    assert all(before_rows[k]==row for k,row in after_rows.items())
    assert hands<=after_rows.keys() and all(before_rows[k]==after_rows[k] for k in hands)
    assert rig.animation_data is None and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    bm=bmesh.new();bm.from_mesh(body.data)
    boundary=sum(e.is_boundary for e in bm.edges);nonmanifold=sum(not e.is_manifold for e in bm.edges)
    loose=sum(not v.link_faces for v in bm.verts)
    components=0;remaining=set(bm.verts)
    while remaining:
        components+=1;pending=[remaining.pop()]
        while pending:
            for e in pending.pop().link_edges:
                for v in e.verts:
                    if v in remaining:remaining.remove(v);pending.append(v)
    bm.free()
    domain=body.data.attributes['AuthoredNeckDomain'];newfaces=[p for p in body.data.polygons if domain.data[p.index].value==1]
    areas=[p.area for p in newfaces];assert areas and min(areas)>0
    normals=np.array([list(n.vector) for n in body.data.corner_normals]);assert np.isfinite(normals).all()
    rn=body.data.attributes['GenuineSelectedCornerNormal'];sf=body.data.attributes['SelectedSourceFace'];error=0.;checked=0
    for p in body.data.polygons:
        if sf.data[p.index].value>=0:
            for li in p.loop_indices:
                co=body.data.vertices[body.data.loops[li].vertex_index].co
                if co.z-(1.555+.36*(co.y+.07)+.5*co.x*co.x)>=.025:
                    raw=np.array(rn.data[li].vector);raw/=np.linalg.norm(raw)
                    error=max(error,float(np.linalg.norm(normals[li]-raw)));checked+=1
    # Transport's actual residual is retained, not silently waived.
    result={'accepted':False,'status':'INDEPENDENT_SAVED_NATIVE_READBACK',
       'candidate':report['candidate'],'sourceNativeSHA256':sha(source),'all75RestRecordsExactlyUnchanged':True,
       'canonicalPositionNamedFieldRowsExactlyUnchanged':len(after_rows),'repairedHandRowsExactlyUnchanged':len(hands),
       'boundaryEdges':boundary,'nonmanifoldEdges':nonmanifold,'looseVertices':loose,'connectedComponents':components,
       'authoredNeckFaces':len(newfaces),'minimumAuthoredTriangleArea':min(areas),
       'selectedUpperRawCornerNormalsChecked':checked,'selectedUpperSavedCornerNormalMaxVectorError':error,
       'savedUpperNormalComparisonTolerance':2e-6,'savedUpperNormalComparisonPass':error<=2e-6,
       'nativeUnchanged':sha(candidate)==report['candidate']['sha256'],
       'limits':['Mesh closure and numerical readback do not accept anatomy, art, UV appearance or moving deformation.','No wardrobe, exported/GPU, engine, mobile or release acceptance.']}
    (out/'independent-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
