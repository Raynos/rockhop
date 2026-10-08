"""Independent saved endpoint-conditioning readback; parent CPU2 lease only."""
import hashlib
import json
import runpy
import sys
from pathlib import Path
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    out=Path(sys.argv[sys.argv.index('--')+1]).resolve();report=json.loads((out/'report.json').read_text())
    recipe=Path(__file__).with_name('condition-upper-neck-field.py');assert sha(recipe)==report['recipeSHA256']
    helper=runpy.run_path(str(recipe));pin=helper['pin'];geometry=helper['geometry'];weights=helper['weights'];rest=helper['rest'];chart=helper['chart'];metrics=helper['endpoint_metrics']
    source=pin(report['sourceNative']);candidate=pin(report['candidate']);bpy.ops.wm.open_mainfile(filepath=str(source))
    before_body=bpy.data.objects['RiderBody'];before_rig=bpy.data.objects['RiderSkeleton'];before_geometry=geometry(before_body);before_rest=rest(before_rig);before_fields=weights(before_body)
    source_rows={int(before_body.data.attributes['_SOURCE_VERTEX_ID'].data[v.index].value):(tuple(v.co),before_fields[v.index]) for v in before_body.data.vertices if 0<=before_body.data.attributes['_SOURCE_VERTEX_ID'].data[v.index].value<1000000}
    bpy.ops.wm.open_mainfile(filepath=str(candidate));body=bpy.data.objects['RiderBody'];rig=bpy.data.objects['RiderSkeleton'];after_fields=weights(body)
    assert geometry(body)==before_geometry==report['geometryUVActualCornerNormalsPackedPBRSignatureUnchanged'] and rest(rig)==before_rest
    changes=json.loads((out/'changed-fields.json').read_text());changed=set(changes['changedVertexIndices'])
    actual_changed={i for i,(a,b) in enumerate(zip(before_fields,after_fields)) if a!=b};assert actual_changed==changed
    ids=body.data.attributes['_SOURCE_VERTEX_ID'].data;assert all(ids[i].value==-1 for i in changed)
    for i in changed:assert after_fields[i]==changes['after'][str(i)] and before_fields[i]==changes['before'][str(i)]
    after_rows={int(ids[v.index].value):(tuple(v.co),after_fields[v.index]) for v in body.data.vertices if 0<=ids[v.index].value<1000000}
    assert after_rows==source_rows and len(after_rows)==6753
    arrays=np.load(ROOT/'harness/out/rider-rebuild/native-hand-repair01/native02/native-body.npz')
    hands=set(map(int,arrays['nativeSourceVertexIds'][arrays['newFieldBlendAlpha']>0]));assert len(hands)==1446 and hands<=after_rows.keys()
    values,faces,stop=chart(body);origin,axis,segments=helper['onset_segments'](body,rig,faces)
    after_metrics=metrics(body,after_fields,values,stop,origin.y);before_metrics=metrics(body,before_fields,values,stop,origin.y)
    assert after_metrics==report['afterEndpointFieldJump'] and before_metrics==report['beforeEndpointFieldJump']
    assert after_metrics['all']['maxL1']==0.
    # Carry forward the actually measured saved normal residual only after the
    # complete actual corner-normal signature has passed exact saved comparison.
    original_readback=json.loads(pin(report['sourceReadback']).read_text())
    assert rig.animation_data is None and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    import bmesh
    bm=bmesh.new();bm.from_mesh(body.data);topology={'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges),'looseVertices':sum(not v.link_faces for v in bm.verts)};bm.free()
    result={'accepted':False,'status':'INDEPENDENT_SAVED_CONDITIONED_FIELD_READBACK',
      'candidate':report['candidate'],'sourceNative':report['sourceNative'],'recipeSHA256':sha(__file__),
      'all75RestRecordsExactlyUnchanged':True,'canonicalPositionNamedFieldRowsExactlyUnchanged':6753,
      'repairedHandRowsExactlyUnchanged':1446,'geometryUVActualCornerNormalsPackedPBRExactlyUnchanged':True,
      'changedNewNeckVertices':len(changed),'savedChangedFieldsExactlyMatchDeclaredRows':True,
      'beforeEndpointFieldJump':before_metrics,'afterEndpointFieldJump':after_metrics,
      'maximumFieldSumError':max(abs(sum(f.values())-1) for f in after_fields),
      'selectedUpperSavedCornerNormalMaxVectorError':original_readback['selectedUpperSavedCornerNormalMaxVectorError'],
      'savedUpperNormalComparisonPass':False,'savedUpperNormalComparisonTolerance':2e-6,
      'actualCornerNormalsExactlySameAsPreviouslyMeasuredSource':True,
      'nativeUnchanged':sha(candidate)==report['candidate']['sha256'],**topology,
      'limits':['Saved field endpoint continuity only; no played art acceptance.','Historical saved corner-normal residual remains failed and unchanged; no waiver.','C7/PBR residuals and actual clothed head movement remain pending.']}
    (out/'independent-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
