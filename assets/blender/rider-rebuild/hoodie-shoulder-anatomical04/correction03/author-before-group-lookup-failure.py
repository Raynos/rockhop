"""ONE expanded sewn shoulder join. Parent checkpoint/serial CPU2 job only.
Save actual geometry before genuine continuous donor-identity PBR transfer.
"""
import hashlib,json,runpy,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[5]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def pin(row):
 p=ROOT/row['path'];assert sha(p)==row['sha256'],row['path'];return p
def main():
 args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
 cp,out=(Path(x).resolve()for x in args);c=json.loads(cp.read_text())
 assert not out.exists()and out.is_relative_to(ROOT/'harness/out/rider-rebuild/hoodie-shoulder-anatomical04')
 pins=[v for v in c.values()if isinstance(v,dict)and'path'in v and'sha256'in v]
 for row in pins:pin(row)
 d=np.load(pin(c['savedArrays']));fields=np.load(pin(c['incomingFields']));cut=json.loads(pin(c['expandedCut']).read_text());original=json.loads(pin(c['incomingReceipt']).read_text())
 source_controls=json.loads(pin(c['originalControls']).read_text());pattern=runpy.run_path(str(pin(c['patternSource'])))
 helpers=runpy.run_path(str(pin(c['originalHelpers'])));chart=runpy.run_path(str(pin(c['sourceChartHelpers'])));atlas=runpy.run_path(str(pin(c['atlasHelpers'])))
 bpy.ops.wm.open_mainfile(filepath=str(pin(c['incomingNative'])))
 obj=bpy.data.objects['Hoodie__RiderHoodie'];body=bpy.data.objects['RiderBody'];rig=bpy.data.objects['RiderSkeleton'];mesh=obj.data
 before_body=helpers['signature'](body,rig);assert before_body==original['bodyAnd75RigSignature']
 positions=np.asarray([v.co[:]for v in mesh.vertices]);assert np.array_equal(positions,d['vertices'])and np.array_equal(positions,fields['vertices'])
 before_maps=atlas['packed_images'](obj);dense=bpy.data.objects['Hoodie__ActualOriginalDensePBR_FrozenFitContext'];assert set(before_maps)==set(atlas['packed_images'](dense))
 assert len(before_maps)==2 and all(list(image.size)==[4096,4096]for image in before_maps.values())
 assert all(n.extension=='REPEAT'and n.interpolation=='Linear'for mat in mesh.materials for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
 old_rows={v.index:tuple(sorted((g.group,g.weight)for g in v.groups))for v in mesh.vertices}
 old_uv={(p.index,mesh.loops[lid].vertex_index):tuple(mesh.uv_layers.active.data[lid].uv)for p in mesh.polygons for lid in p.loop_indices}
 old_material=[p.material_index for p in mesh.polygons]
 results=[];raw=d['actual_donor_display_xyz']
 for spec in c['panels']:
  sidecut=next(s for s in cut['sides']if s['side']==spec['side']);boundary=sidecut['orientedBoundaryCycles'][spec['boundaryCycle']]
  outer=next(p for p in c['panels']if p['side']==spec['side']and not p['interior'])
  result=pattern['patch'](boundary,spec['anchors'],positions,raw,fields['fields'],spec['side'],spec['interior'],positions[outer['anchors']],c['cloth'])
  results.append((spec,result))
 bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
 input_vertex=bm.verts.layers.int.new('_tailor03_input_vertex_id');input_face=bm.faces.layers.int.new('_tailor03_input_face_id')
 role=bm.faces.layers.int.new('_tailor03_role');params=bm.verts.layers.float_vector.new('_tailor03_uv_parameter')
 rawlayer=bm.verts.layers.float_vector['actual_donor_display_xyz'];deform=bm.verts.layers.deform.active;assert deform is not None
 original_vertex=bm.verts.layers.int['_panel04_original_vertex_id'];original_face=bm.faces.layers.int['_panel04_original_face_id']
 uv=bm.loops.layers.uv.active;assert uv is not None
 for v in bm.verts:v[input_vertex]=v.index
 for f in bm.faces:f[input_face]=f.index
 by_input={v.index:v for v in bm.verts};removed={fi for s in cut['sides']for fi in s['actualExpandedFaceIds']};assert len(removed)==2743
 bmesh.ops.delete(bm,geom=[bm.faces[fi]for fi in sorted(removed)],context='FACES')
 group_indices=[obj.vertex_groups[str(name)].index for name in fields['jointNames']];assert len(group_indices)==75
 records=[]
 for spec,result in results:
  generated=[]
  for p,identity,row,st in zip(result['positions'],result['raw'],result['weights'],result['UV']):
   v=bm.verts.new(Vector(p));v[input_vertex]=-1;v[original_vertex]=-1;v[rawlayer]=Vector(identity);v[params]=Vector((st[0],st[1],0))
   for gi,w in zip(group_indices,row):
    if w>1e-8:v[deform][gi]=float(w)
   generated.append(v)
  for vi,st in result['outerUV'].items():by_input[vi][params]=Vector((st[0],st[1],0))
  newfaces=[]
  for indices in result['faces']:
   vs=[by_input[-i-1]if i<0 else generated[i]for i in indices];f=bm.faces.new(vs);f[role]=spec['role'];f[input_face]=-1;f[original_face]=-1;f.material_index=0;f.smooth=True
   for name in ('source22_polygon_id','simplified_donor_polygon'):
    layer=bm.faces.layers.int.get(name)
    if layer is not None:f[layer]=-1
   for loop in f.loops:
    for name in ('_panel04_selected_face_id','_panel04_selected_corner_0','_panel04_selected_corner_1','_panel04_selected_corner_2'):
     layer=bm.loops.layers.int.get(name)
     if layer is not None:loop[layer]=-1
    layer=bm.loops.layers.float_vector.get('_panel04_selected_barycentric')
    if layer is not None:loop[layer]=Vector((0,0,0))
   newfaces.append(f)
  records.append({'role':spec['role'],'side':spec['side'],'interior':spec['interior'],'sourceComponent':spec['sourceComponent'],'vertices':len(generated),'regularQuads':result['regularQuads'],'transitionTriangles':result['transitionTriangles'],'anatomicalAnchorInputVertices':spec['anchors']})
 bm.normal_update()
 new_edges={e for f in bm.faces if f[role]>0 for e in f.edges};assert all(len(e.link_faces)==2 for e in new_edges)
 bm.to_mesh(mesh);bm.free();mesh.update()
 def verify_retained():
  iv=mesh.attributes['_tailor03_input_vertex_id'];ifa=mesh.attributes['_tailor03_input_face_id']
  for v in mesh.vertices:
   old=iv.data[v.index].value
   if old>=0:
    assert np.array_equal(v.co[:],positions[old]);assert tuple(sorted((g.group,g.weight)for g in v.groups))==old_rows[old]
  for f in mesh.polygons:
   old=ifa.data[f.index].value
   if old>=0:
    assert f.material_index==old_material[old]
    for lid in f.loop_indices:
     oldv=iv.data[mesh.loops[lid].vertex_index].value;assert tuple(mesh.uv_layers.active.data[lid].uv)==old_uv[old,oldv]
  assert helpers['signature'](body,rig)==before_body
 verify_retained();out.mkdir(parents=True)
 shape_native=out/'tailored-geometry-before-transfer.blend';bpy.ops.wm.save_as_mainfile(filepath=str(shape_native),compress=True)
 # Existing UVs on new geometry are not reviewable until this genuine local
 # selected-source transfer finishes. Recoverable actual geometry is saved first.
 panels=[];role_data=mesh.attributes['_tailor03_role'];param_data=mesh.attributes['_tailor03_uv_parameter']
 for spec in c['panels']:
  faces=[p.index for p in mesh.polygons if role_data.data[p.index].value==spec['role']]
  ids={v for fi in faces for v in mesh.polygons[fi].vertices}
  panels.append({'label':spec['sourceComponent'],'faces':faces,'params':{vi:np.asarray(param_data.data[vi].vector[:2])for vi in ids},'sourceComponent':next(p for p in source_controls['components']if p['label']==spec['sourceComponent'])})
 mapreports=atlas['transfer_atlas'](mesh,panels,None,c,out,before_maps,chart['source_chart'])
 verify_retained();assert set(before_maps)<set(atlas['packed_images'](obj))
 visible=sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH'and not o.hide_render);assert visible==original['visibleMeshes']and len(visible)==7
 assert not body.hide_get()and not obj.hide_get()
 obj['contextStatus']='EXPANDED_ANATOMICAL_FRONT_REAR_SEWN_JOIN_ORIGINAL_PBR_TRANSFER_UNREVIEWED';obj['acceptedArt']=False;obj['tailor03RecipeSHA256']=sha(__file__);obj['tailor03ControlsSHA256']=sha(cp)
 native=out/'selected-tailored-outfit.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
 native_fields=np.zeros((len(mesh.vertices),75));index={gi:i for i,gi in enumerate(group_indices)}
 for v in mesh.vertices:
  for g in v.groups:
   if g.group in index:native_fields[v.index,index[g.group]]=g.weight
 np.savez_compressed(out/'tailored-native-fields.npz',vertices=np.asarray([v.co[:]for v in mesh.vertices]),fields=native_fields,jointNames=fields['jointNames'])
 receipt={'accepted':False,'stage':'EXPANDED_ANATOMICAL_SEWN_JOIN_AND_ORIGINAL_PBR_TRANSFER_SAVED','native':{'path':str(native.relative_to(ROOT)),'sha256':sha(native)},'geometryBeforeTransfer':{'path':str(shape_native.relative_to(ROOT)),'sha256':sha(shape_native)},'recipeSHA256':sha(__file__),'controlsSHA256':sha(cp),'incomingNative':c['incomingNative'],'targetObject':obj.name,'bodyAnd75RigSignature':before_body,'bodyAnd75RigUnchanged':True,'visibleMeshes':visible,'removedJoinAndSupportFaces':len(removed),'vertices':len(mesh.vertices),'polygons':len(mesh.polygons),'panels':records,'properCutRetainedPositionsUVMaterialsFieldsExact':True,'coupledTrueExteriorInterior':True,'originalPBRTransferMaps':mapreports,'limits':c['limits']}
 (out/'author.json').write_text(json.dumps(receipt,indent=2)+'\n')
 for row in pins:pin(row)
 print('ACTUAL_EXPANDED_SEWN_HOODIE_AND_SOURCE_PBR_SAVED',flush=True)
if __name__=='__main__':main()
