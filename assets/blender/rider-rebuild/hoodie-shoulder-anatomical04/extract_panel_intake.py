"""ONE minimal readonly compact/source topology+UV intake for cloth tailoring.

SOURCE ONLY until parent checkpoint/global serial CPU2 lease.
blender -b -t 2 --python-exit-code 1 --python extract_panel_intake.py -- inputs.json FRESH_OUT
No modifier, geometry edit, fit, native save, dense import, bake or render.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

ROOT=Path(__file__).resolve().parents[4]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(row):
    p=ROOT/row['path'];assert sha(p)==row['sha256'],('Changed input',row['path'])
    return p


def mesh_arrays(obj,path,basis=None):
    mesh=obj.data
    matrix=obj.matrix_world if basis is None else basis@obj.matrix_world
    arrays={'vertices':np.asarray([matrix@v.co for v in mesh.vertices],dtype=np.float64),
            'polygonStarts':np.asarray([p.loop_start for p in mesh.polygons],dtype=np.int32),
            'polygonCounts':np.asarray([p.loop_total for p in mesh.polygons],dtype=np.int32),
            'cornerVertexIds':np.asarray([loop.vertex_index for loop in mesh.loops],dtype=np.int32),
            'polygonMaterialIds':np.asarray([p.material_index for p in mesh.polygons],dtype=np.int32),
            'edges':np.asarray([e.vertices[:] for e in mesh.edges],dtype=np.int32)}
    uv_names=[]
    for i,layer in enumerate(mesh.uv_layers):
        arrays['cornerUV_'+str(i)]=np.asarray([d.uv[:] for d in layer.data],dtype=np.float32)
        uv_names.append(layer.name)
    attribute_records=[]
    for attribute in mesh.attributes:
        record={'name':attribute.name,'domain':attribute.domain,'type':attribute.data_type}
        # Preserve existing explicit geometry/chart lineage when present. Do not
        # synthesize source IDs for generated patch vertices or missing UVs.
        if not attribute.name.startswith('.') and attribute.data_type in ('INT','FLOAT','BOOLEAN','FLOAT_VECTOR','FLOAT_COLOR'):
            field='vector' if attribute.data_type=='FLOAT_VECTOR' else 'color' if attribute.data_type=='FLOAT_COLOR' else 'value'
            data=[list(getattr(v,field)) if field!='value' else getattr(v,field) for v in attribute.data]
            key='attribute_'+str(len(attribute_records));arrays[key]=np.asarray(data)
            record['arrayKey']=key
        attribute_records.append(record)
    np.savez_compressed(path,**arrays)
    return {'object':obj.name,'vertices':len(mesh.vertices),'polygons':len(mesh.polygons),
            'corners':len(mesh.loops),'uvLayers':uv_names,'attributes':attribute_records,
            'materials':[m.name if m else None for m in mesh.materials],
            'originalObjectMatrix':[list(r) for r in obj.matrix_world],
            'arrayFrame':'Current wearer frame; selected source rotated -90deg Z only' if basis is not None else 'Current wearer native rest',
            'npz':{'path':str(path.relative_to(ROOT)),'sha256':sha(path)}}


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    config_path,out=(Path(x).resolve() for x in args)
    c=json.loads(config_path.read_text())
    assert out.is_relative_to(ROOT/c['outputRoot']) and not out.exists()
    rows=[v for v in c.values() if isinstance(v,dict) and 'path' in v and 'sha256' in v]
    for row in rows:pin(row)
    bpy.ops.wm.open_mainfile(filepath=str(pin(c['targetNative'])))
    body,rig,target=(bpy.data.objects[n] for n in ('RiderBody','RiderSkeleton','RiderHoodie'))
    assert len(body.data.vertices)==10582 and len(rig.data.bones)==75
    helpers=runpy.run_path(str(pin(c['frozenAuthorHelpers'])))
    before=helpers['signature'](body,rig)
    receipt=json.loads(pin(c['targetReceipt']).read_text())
    assert helpers['hoodie_geometry'](target)==receipt['targetGeometrySHA256']
    assert before==receipt['bodyAnd75RigSignature']
    out.mkdir(parents=True)
    target_record=mesh_arrays(target,out/'compact-target.npz')
    # Only selected geometry/UV attributes are consumed. No old source rig or
    # source skin arrays are requested or inspected as deformation authority.
    with bpy.data.libraries.load(str(pin(c['selectedNative'])),link=False) as (available,selected):
        assert c['selectedObject'] in available.objects
        selected.objects=[c['selectedObject']]
    source=selected.objects[0]
    assert len(source.data.vertices)==12430 and len(source.data.polygons)==19878
    source_record=mesh_arrays(source,out/'selected25-source.npz',Matrix(c['selectedToWearerRows']).to_4x4())
    assert helpers['signature'](body,rig)==before
    assert helpers['hoodie_geometry'](target)==receipt['targetGeometrySHA256']
    for row in rows:pin(row)
    result={'accepted':False,'stage':'MINIMAL_COMPACT_AND_SELECTED_PANEL_TOPOLOGY_UV_INTAKE_ONLY',
            'recipeSHA256':sha(__file__),'inputsSHA256':sha(config_path),'inputs':c,
            'target':target_record,'selectedSource':source_record,
            'bodyAnd75RestUnchanged':True,'targetUnchanged':True,'nativeSaved':False,
            'next':'Choose explicit chest/back/upperarm seam boundaries and selected chart landmarks; author ONE bilateral axillary panel baseline before any PBR transfer.',
            'limits':c['limits']}
    (out/'intake.json').write_text(json.dumps(result,indent=2)+'\n')
    print('MINIMAL_PANEL_INTAKE_SAVED',str(out),flush=True)


if __name__=='__main__':main()
