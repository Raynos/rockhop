"""Extract the already reviewed weighted gloves/shoes and bake compact colour.
Meshes and skin weights remain unchanged; only unused faces/atlas space removed.
"""
import bpy,bmesh,json
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P/'work/baseline.glb'))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
arm.animation_data.action=None
for tr in arm.animation_data.nla_tracks:tr.mute=True
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
body=bpy.data.objects.get('rider_body');assert body
contacts=body.copy();contacts.data=body.data.copy();s.collection.objects.link(contacts);contacts.name='Authored_grips_and_soles';contacts.modifiers.clear();contacts.parent=None
wanted={'hand.L','hand.R','foot.L','foot.R'}
vkeep=[]
for v in contacts.data.vertices:
 amount=sum(g.weight for g in v.groups if contacts.vertex_groups[g.group].name in wanted)
 vkeep.append(amount>.55)
bm=bmesh.new();bm.from_mesh(contacts.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
drop=[f for f in bm.faces if sum(vkeep[v.index] for v in f.verts)<len(f.verts)*.66]
bmesh.ops.delete(bm,geom=drop,context='FACES');loose=[v for v in bm.verts if not v.link_faces];bmesh.ops.delete(bm,geom=loose,context='VERTS');bm.to_mesh(contacts.data);bm.free()
source=contacts.copy();source.data=contacts.data.copy();s.collection.objects.link(source);source.name='Contact_bake_source'
bpy.ops.object.select_all(action='DESELECT');contacts.select_set(True);bpy.context.view_layer.objects.active=contacts
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
mat=bpy.data.materials.new('Authored charcoal gloves and soles');mat.use_nodes=True;bsdf=mat.node_tree.nodes['Principled BSDF'];bsdf.inputs['Metallic'].default_value=0;bsdf.inputs['Roughness'].default_value=.75
img=bpy.data.images.new('Authored_contact_albedo_1024',width=1024,height=1024);img.colorspace_settings.name='sRGB'
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;mat.node_tree.nodes.active=tex;mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
contacts.data.materials.clear();contacts.data.materials.append(mat)
for f in contacts.data.polygons:f.material_index=0
for ma in source.data.materials:
 if ma and ma.use_nodes:
  for node in ma.node_tree.nodes:
   if node.type=='BSDF_PRINCIPLED':node.inputs['Metallic'].default_value=0
s.render.engine='CYCLES';s.cycles.samples=1;s.render.bake.use_pass_direct=False;s.render.bake.use_pass_indirect=False;s.render.bake.use_pass_color=True;s.render.bake.use_selected_to_active=True;s.render.bake.cage_extrusion=.001;s.render.bake.max_ray_distance=.004;s.render.bake.margin=8
# Every other mesh is excluded from the bake, including hidden source probes.
for o in s.objects:
 if o.type=='MESH' and o not in (contacts,source):o.hide_render=True
bpy.ops.object.select_all(action='DESELECT');source.select_set(True);contacts.select_set(True);bpy.context.view_layer.objects.active=contacts
bpy.ops.object.bake(type='DIFFUSE')
img.filepath_raw=str(P/'work/authored-contact-albedo.png');img.file_format='PNG';img.save();img.pack()
for o in list(bpy.data.objects):
 if o!=contacts:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/authored-contacts.blend'),compress=True)
report={'vertices':len(contacts.data.vertices),'triangles':sum(len(f.vertices)-2 for f in contacts.data.polygons),'baseAtlas':1024,'source':'ec04192d61e39dcc8bdb80fd97842e8019ef4e55:public/models/rider-street-mustard.glb','retainedDominantBones':sorted(wanted),'weightsAndCoordinatesUnchanged':True,'limitation':'Boundary joins require matching generated sleeve/ankle geometry; parent actual Garage motion judges.'}
(P/'authored-contacts.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
