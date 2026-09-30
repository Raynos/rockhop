"""Independently verify applied MPFB body mask and measured native eye openings."""
import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'fresh-base.blend'))
base=bpy.data.objects['Fresh_adult_MakeHuman_base'];arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
ids=base.data.attributes.new('FreshSourceId','INT','POINT')
for v in base.data.vertices:ids.data[v.index].value=v.index
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
me=bpy.data.meshes.new_from_object(base.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
sourceids=[d.value for d in me.attributes['FreshSourceId'].data]
assert len(sourceids)==13380 and min(sourceids)==0 and max(sourceids)==13379
assert len(set(sourceids))==13380
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
eyes={}
for side in ('L','R'):
 c=arm.data.bones['eye.'+side].head_local
 boundary=set(v for e in bm.edges if len(e.link_faces)==1 for v in e.verts if (v.co-c).length<.065)
 pts=[v.co for v in boundary];eyes[side]={'nativeEyeBoneCenter':list(c),'openingBoundaryVertices':len(pts),'openingCenter':list(sum(pts,Vector((0,0,0)))/len(pts)) if pts else None,'openingBounds':[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)] if pts else None,'openingPoints':[list(p) for p in pts]}
report={'status':'fresh source topology probe, no art acceptance','rawVertices':len(base.data.vertices),'evaluatedBodyVertices':len(me.vertices),'sourceIndexRange':[min(sourceids),max(sourceids)],'sourceIndicesExactlyBodyRange':sourceids==list(range(13380)),'helperGeometryRetained':False,'jointCubesRetained':False,'appliedModifiers':[{'name':m.name,'type':m.type,'group':getattr(m,'vertex_group',None)} for m in base.modifiers],'triangles':sum(len(p.vertices)-2 for p in me.polygons),'eyeOpenings':eyes,'sourceRecipeSha256':hashlib.sha256((P/'probe_fresh_base.py').read_bytes()).hexdigest()}
Path('docs/evidence/hero-remaster/restart/whole-rider-v1-fresh-mask.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='eyeOpenings'}))
