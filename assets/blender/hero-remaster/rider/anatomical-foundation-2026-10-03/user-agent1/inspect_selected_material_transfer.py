"""Read frozen source13 material channels before altering transfer or shape."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
source=Path(a.source).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pin=sha(source)
assert pin=='6ef79e38e3dc86b635977ba17a2f2f6100721715b002c4e831b8bcce90ed4e93'
bpy.ops.wm.open_mainfile(filepath=str(source))
high=bpy.data.objects['Exact selected Hunyuan high-poly PBR donor, display frame only']
garment=next(o for o in bpy.data.objects if o.type=='MESH' and len(o.data.vertices)==6046 and not o.hide_render)
report={'status':'UNACCEPTED read-only donor/baked material diagnosis','sourceSHA256':pin,'recipeSHA256':sha(__file__),'objects':{}}
for obj in [high,garment]:
    mats=[]
    for mat in obj.data.materials:
        nodes=[]
        for n in mat.node_tree.nodes:
            row={'name':n.name,'type':n.type,'inputs':{}}
            for socket in n.inputs:
                if hasattr(socket,'default_value'):
                    v=socket.default_value
                    row['inputs'][socket.name]={'value':list(v) if hasattr(v,'__len__') and not isinstance(v,str) else v,'links':[[l.from_node.name,l.from_socket.name] for l in socket.links]}
            if n.type=='TEX_IMAGE' and n.image:
                img=n.image;pix=np.empty(len(img.pixels),dtype=np.float32);img.pixels.foreach_get(pix);pix=pix.reshape(-1,4)
                row['image']={'name':img.name,'size':list(img.size),'colorSpace':img.colorspace_settings.name,'filepath':img.filepath,'packed':bool(img.packed_file),'channels':img.channels,'interpolation':n.interpolation,'extension':n.extension,
                              'imageBufferPixelPercentilesRGB':np.percentile(pix[:,:3],[0,5,50,95,100],axis=0).tolist()}
            nodes.append(row)
        mats.append({'name':mat.name,'nodes':nodes,'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in mat.node_tree.links]})
    report['objects'][obj.name]={'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons),'UVLayers':[(u.name,u.active_render) for u in obj.data.uv_layers],'materials':mats}
assert pin==sha(source)
(out/'material-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print('SELECTED_MATERIAL_INSPECTED',garment.name,flush=True)
