"""Export untouched native head/UV/semantic data for CPU texture transfer."""
import argparse,sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=a.input)
head=max((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices))
m=head.data;m.calc_loop_triangles();uv=m.uv_layers.active.data
v=np.array([[p.co.x,p.co.z,-p.co.y] for p in m.vertices],dtype=np.float32)
faces=np.array([t.vertices[:] for t in m.loop_triangles],dtype=np.int32)
triuv=np.array([[uv[l].uv[:] for l in t.loops] for t in m.loop_triangles],dtype=np.float32)
weights={}
for name in ['scalp','ears','lips']:
    gi=head.vertex_groups[name].index
    weights[name]=np.array([next((g.weight for g in p.groups if g.group==gi),0) for p in m.vertices],dtype=np.float32)
np.savez(out/'uv-transfer-data.npz',vertices=v,faces=faces,triangleUV=triuv,**weights)
report={'source':a.input,'sourceSHA256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),
    'groups':{k:{'count':int(np.sum(w>.5)),'meanNative':v[w>.5].mean(0).tolist()} for k,w in weights.items()},
    'verticesSHA256':hashlib.sha256(v.tobytes()).hexdigest(),'facesSHA256':hashlib.sha256(faces.tobytes()).hexdigest()}
(out/'uv-transfer-data.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
