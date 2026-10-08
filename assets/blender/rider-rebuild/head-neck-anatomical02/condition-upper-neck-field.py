"""One endpoint-continuous field derivative of reviewed body902; parent lease.

No geometry/UV/PBR/rest edit. Actual middle-neck joint plane sets onset in the
actual authored UV surface. C2 smootherstep reaches genuine head1 at the last
existing row, leaving the final edge interval constant and its tangent zero.
No inferred layer deletion, height/gain fit, solver, animation, render or export.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[4]
SOURCE_SHA='9023618821cfb4e0c2725f0dfb970ac898d7e38d94a4c30be9863515c938307c'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def pin(row):
    p=(ROOT/row['path']).resolve();assert sha(p)==row['sha256'],('Changed input',str(p));return p

def rest(rig):
    return [{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),
      'matrix':[list(r) for r in b.matrix_local],'connect':b.use_connect,'deform':b.use_deform} for b in rig.data.bones]

def weights(body):
    names={g.index:g.name for g in body.vertex_groups}
    return [{names[g.group]:g.weight for g in v.groups if g.weight>0} for v in body.data.vertices]

def geometry(body):
    h=hashlib.sha256()
    for v in body.data.vertices:h.update(struct.pack('<3f',*v.co))
    for p in body.data.polygons:
        h.update(struct.pack('<II',p.material_index,len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    for layer in body.data.uv_layers:
        h.update(layer.name.encode())
        for corner in layer.data:h.update(struct.pack('<2f',*corner.uv))
    for normal in body.data.corner_normals:h.update(struct.pack('<3f',*normal.vector))
    for a in body.data.attributes:
        if a.name in ('_SOURCE_VERTEX_ID','SelectedSourceFace','AuthoredNeckDomain'):
            h.update(a.name.encode())
            for row in a.data:h.update(struct.pack('<i',row.value))
    for mat in body.data.materials:
        if not mat:continue
        h.update(mat.name.encode())
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image:
                    assert node.image.packed_file;h.update(hashlib.sha256(node.image.packed_file.data).digest())
    return h.hexdigest()

def chart(body):
    uv=body.data.uv_layers.active.data;domain=body.data.attributes['AuthoredNeckDomain'].data
    corners={};faces=[]
    for p in body.data.polygons:
        if domain[p.index].value!=1:continue
        assert len(p.vertices)==3
        row=[]
        for li in p.loop_indices:
            vi=body.data.loops[li].vertex_index;tex=Vector(uv[li].uv);row.append((vi,tex))
            corners.setdefault(vi,[]).append(tex)
        faces.append(row)
    values={}
    for vi,tex in corners.items():
        ts=[q.y for q in tex];us=[q.x for q in tex]
        assert max(ts)-min(ts)<=2e-6,('Vertex crosses authored row parameter',vi)
        # The UV seam has exact coincident u0/u1 ancestry. Wrap to u0 only.
        u=0. if max(us)-min(us)>.5 else sum(us)/len(us)
        values[vi]=(u,sum(ts)/len(ts))
    levels=sorted({round(t,7) for _,t in values.values()});assert levels[0]==0. and levels[-1]==1.
    stop=max(t for t in levels if t<1.-1e-6)
    assert len(levels)==21 and abs(stop-.95)<2e-6,('Unexpected actual authored rows',levels)
    return values,faces,stop

def onset_segments(body,rig,faces):
    start=rig.data.bones['DEF-spine.004'];middle=rig.data.bones['DEF-spine.005'];head=rig.data.bones['DEF-spine.006']
    assert (start.tail_local-middle.head_local).length<1e-7 and (middle.tail_local-head.head_local).length<1e-7
    origin=middle.head_local.copy();axis=(head.head_local-start.head_local).normalized();segments=[]
    for row in faces:
        cuts=[]
        for (a,ua),(b,ub) in zip(row,row[1:]+row[:1]):
            pa=body.data.vertices[a].co;pb=body.data.vertices[b].co;da=(pa-origin).dot(axis);db=(pb-origin).dot(axis)
            if da*db<0:
                f=da/(da-db);cuts.append(ua.lerp(ub,f))
            elif abs(da)<1e-9:cuts.append(ua.copy())
        unique=[]
        for p in cuts:
            if not any((p-q).length<1e-8 for q in unique):unique.append(p)
        if unique:
            assert len(unique)==2,('Invalid anatomical plane intersection',unique)
            a,b=sorted(unique,key=lambda p:p.x)
            if b.x-a.x>1e-8:segments.append((a,b))
    assert segments,'Actual neck joint plane did not intersect authored surface'
    return origin,axis,segments

def onset(u,segments,stop):
    values=[]
    for a,b in segments:
        if a.x-1e-7<=u<=b.x+1e-7:
            f=max(0,min(1,(u-a.x)/(b.x-a.x)));values.append(a.y*(1-f)+b.y*f)
    assert values,('No anatomical plane crossing for actual UV strip',u)
    assert max(values)-min(values)<2e-5,('Multiple incompatible plane crossings',u,values)
    value=sum(values)/len(values);assert 0<value<stop,('Onset outside valid actual rows',u,value,stop)
    return value

def endpoint_metrics(body,fields,chart_values,stop,head_y):
    buckets={'all':[],'anterior':[],'posterior':[]}
    for e in body.data.edges:
        a,b=map(int,e.vertices)
        if a not in chart_values or b not in chart_values:continue
        ta,tb=chart_values[a][1],chart_values[b][1]
        if not ((abs(ta-stop)<2e-6 and abs(tb-1)<2e-6) or (abs(tb-stop)<2e-6 and abs(ta-1)<2e-6)):continue
        names=set(fields[a])|set(fields[b]);d=[abs(fields[a].get(n,0)-fields[b].get(n,0)) for n in names]
        row=(sum(d),max(d));buckets['all'].append(row)
        key='anterior' if (body.data.vertices[a].co.y+body.data.vertices[b].co.y)/2<head_y else 'posterior';buckets[key].append(row)
    assert all(buckets.values()),'Actual final-row edges must span both anterior and posterior'
    return {k:{'edges':len(v),'maxL1':max(x[0] for x in v),'maxLInfinity':max(x[1] for x in v)} for k,v in buckets.items()}

def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    config_path,out=(Path(p).resolve() for p in args);config=json.loads(config_path.read_text());assert config['accepted'] is False
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/head-neck-anatomical02') and not out.exists()
    native=pin(config['sourceNative']);readback=json.loads(pin(config['sourceReadback']).read_text())
    assert config['sourceNative']['sha256']==SOURCE_SHA and readback['candidate']==config['sourceNative']
    assert readback['all75RestRecordsExactlyUnchanged'] and readback['repairedHandRowsExactlyUnchanged']==1446
    bpy.ops.wm.open_mainfile(filepath=str(native));body=bpy.data.objects['RiderBody'];rig=bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones)==75 and rig.animation_data is None and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    before_rest=rest(rig);before_geometry=geometry(body);before=weights(body);values,faces,stop=chart(body)
    origin,axis,segments=onset_segments(body,rig,faces);onsets={vi:onset(u,segments,stop) for vi,(u,t) in values.items()}
    head='DEF-spine.006';head_group=body.vertex_groups[head]
    anchor=[vi for vi,(u,t) in values.items() if abs(t-1)<2e-6]
    assert len(anchor)==347 and all(before[i]=={head:1.} for i in anchor),'Actual genuine upper-rim head1 anchors required'
    before_metrics=endpoint_metrics(body,before,values,stop,origin.y)
    changed=[];blend_records=[]
    for vi,(u,t) in values.items():
        start=onsets[vi]
        if t<=start:continue
        if t>=stop-2e-6:a=1.
        else:
            x=(t-start)/(stop-start);a=x*x*x*(10+x*(-15+6*x))
        old=before[vi];new={n:w*(1-a) for n,w in old.items()};new[head]=new.get(head,0)+a
        new={n:w for n,w in new.items() if w>0};total=sum(new.values());new={n:w/total for n,w in new.items()}
        if new==old:continue
        for g in body.vertex_groups:g.remove([vi])
        for n,w in new.items():body.vertex_groups[n].add([vi],w,'REPLACE')
        changed.append(vi);blend_records.append({'vertex':vi,'u':u,'t':t,'anatomicalOnsetT':start,'headBlend':a})
    after=weights(body);after_metrics=endpoint_metrics(body,after,values,stop,origin.y)
    assert after_metrics['all']['maxL1']==0 and after_metrics['all']['maxLInfinity']==0
    ids=body.data.attributes['_SOURCE_VERTEX_ID'].data
    assert all(ids[i].value==-1 for i in changed),'Endpoint conditioning touched original canonical/donor row'
    changed_set=set(changed)
    assert all(before[i]==after[i] for i in range(len(before)) if i not in changed_set)
    canonical=[v.index for v in body.data.vertices if 0<=ids[v.index].value<1000000]
    assert len(canonical)==6753 and all(before[i]==after[i] for i in canonical)
    assert geometry(body)==before_geometry and rest(rig)==before_rest
    lower=[i for i,(u,t) in values.items() if t<=onsets[i]];assert all(before[i]==after[i] for i in lower)
    field_sum_error=max(abs(sum(w.values())-1) for w in after);assert field_sum_error<2e-6
    out.mkdir(parents=True);candidate=out/'selected-head-neck-conditioned.blend';bpy.ops.wm.save_as_mainfile(filepath=str(candidate),compress=True)
    (out/'changed-fields.json').write_text(json.dumps({'changedVertexIndices':changed,'records':blend_records,
        'before':{str(i):before[i] for i in changed},'after':{str(i):after[i] for i in changed}},indent=2)+'\n')
    (out/'weights-native-named.json').write_text(json.dumps(after)+'\n')
    report={'accepted':False,'status':'UNACCEPTED_ENDPOINT_CONDITIONED_FIELD_DERIVATIVE_SAVED',
      'candidate':{'path':str(candidate.relative_to(ROOT)),'sha256':sha(candidate)},'sourceNative':config['sourceNative'],
      'sourceReadback':config['sourceReadback'],'recipeSHA256':sha(__file__),'configSHA256':sha(config_path),
      'geometryUVActualCornerNormalsPackedPBRSignatureUnchanged':before_geometry,'all75RestRecordsUnchanged':True,
      'canonicalRetainedNamedFieldRowsUnchanged':len(canonical),'originalSourceRowsEdited':0,'changedNewNeckVertices':len(changed),
      'actualUpperHead1Anchors':len(anchor),'actualFinalRowPlateauT':stop,'lowerAuthoredRowsUnchanged':len(lower),
      'anatomicalPlane':{'originJoint':'DEF-spine.005 head (=DEF-spine.004 tail)','origin':list(origin),'axis':list(axis),
       'axisLandmarks':['DEF-spine.004 head','DEF-spine.006 head'],'UVIntersectionSegments':len(segments)},
      'actualAnatomicalOnsetTRange':[min(onsets.values()),max(onsets.values())],
      'blend':'quintic smootherstep10x³−15x⁴+6x⁵ from actual plane t0(u) to actual last row; final row→upper head1 anchor is constant; C2 endpoint derivatives zero',
      'beforeEndpointFieldJump':before_metrics,'afterEndpointFieldJump':after_metrics,'maximumFieldSumError':field_sum_error,
      'maximumNativeInfluences':max(map(len,after)),
      'limits':['No geometry/material/rest correction or new art acceptance.','Independent saved readback and clothed actual stress remain required.',
        'Known C7 bulge, right-neck albedo/shading/hair seam and historical saved normal residual remain open.',
        'New named field inventory is derivative; original canonical FULL/FOUR files remain immutable and are not redefined.']}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');assert sha(native)==SOURCE_SHA
    print(json.dumps({'candidate':report['candidate'],'changedNewVertices':len(changed),'onsetTRange':report['actualAnatomicalOnsetTRange'],'before':before_metrics,'after':after_metrics}))
if __name__=='__main__':main()
