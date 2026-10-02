import bpy,json,numpy as np,hashlib
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/drafted-raglan');E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/drafted-raglan')
S=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(S));bpy.context.view_layer.update()
rep={'source':str(S),'sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'coordinate':'Blender world Z up; glTF Y up import adapter','objects':[],'bones':[]}
for ob in bpy.context.scene.objects:
 if ob.type=='ARMATURE':
  rep['bones']=[{'name':b.name,'head':list(ob.matrix_world@b.head_local),'tail':list(ob.matrix_world@b.tail_local)} for b in ob.data.bones]
 if ob.type!='MESH':continue
 p=np.array([list(ob.matrix_world@v.co) for v in ob.data.vertices]);f=np.array([list(q.vertices) for q in ob.data.polygons]);m=np.array([q.material_index for q in ob.data.polygons]);np.savez(R/(ob.name+'.npz'),p=p,f=f,material=m)
 adj=[[] for v in p]
 for i,t in enumerate(f):
  for a in t:
   for b in t:
    if a!=b:adj[a].append(int(b))
 seen=set();comps=[]
 for a in range(len(p)):
  if a in seen:continue
  todo=[a];c=[];seen.add(a)
  while todo:
   v=todo.pop();c.append(v)
   for w in adj[v]:
    if w not in seen:seen.add(w);todo.append(w)
  ids=np.array(c);comps.append({'vertices':len(c),'min':p[ids].min(0).tolist(),'max':p[ids].max(0).tolist(),'vertexIDs':c})
 rep['objects'].append({'name':ob.name,'vertices':len(p),'faces':len(f),'min':p.min(0).tolist(),'max':p.max(0).tolist(),'materials':[{'name':m.name,'nodes':[{'name':n.name,'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes]} for m in ob.data.materials], 'materialBounds':[{'index':int(i),'faces':int((m==i).sum()),'min':p[f[m==i]].reshape(-1,3).min(0).tolist(),'max':p[f[m==i]].reshape(-1,3).max(0).tolist()} for i in np.unique(m)],'components':comps})
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source-inventory.blend'));(E/'inventory.json').write_text(json.dumps(rep,indent=2));print(json.dumps({**rep,'objects':[{k:v for k,v in o.items() if k!='components'} for o in rep['objects']]}))
