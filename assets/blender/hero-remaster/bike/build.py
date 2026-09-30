"""Candidate-only whole-bike remaster. Mechanical node TRS/extras are immutable.

Imports current production (Meshopt-decoded); authors manufactured panel shells,
cast engine, header and silencer, then bakes bounded PBR atlas for 23 draws.
"""
import argparse,json,math,sys,hashlib
from pathlib import Path
import bpy,bmesh
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'assets/blender'))
import common as C
import build_bike as B
from common import V,MeshBuilder
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--variant',choices=['rookie','pro'],required=True);p.add_argument('--lod',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
OUT=Path(a.output).resolve();OUT.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(a.input).resolve()))
original={o.name:{'matrix':[list(r) for r in o.matrix_local],'parent':o.parent.name if o.parent else None,'extras':{k:str(v) for k,v in o.items()}} for o in bpy.context.scene.objects}
low=a.lod
paintcol=(.006,.037,.48,1) if a.variant=='rookie' else (.017,.020,.026,1)
stripe=(.82,.87,.91,1) if a.variant=='rookie' else (1,.58,.005,1)
def mat(name,col,rough,metal,bump=0):
 m=C.new_mat('remaster_'+name,col,rough=rough,metal=metal)
 if bump:C.bump(m,C.noise_fac(m,scale=420,detail=2),strength=.1,distance=bump)
 return m
M={'paint':mat('satin_cobalt' if a.variant=='rookie' else 'satin_graphite',paintcol,.30,.16,.00015),
 'stripe':mat('porcelain' if a.variant=='rookie' else 'race_gold',stripe,.35,.08),
 'alloy':mat('brushed_alloy',(.42,.46,.49,1),.31,.92,.00018),
 'black':mat('black_polymer',(.008,.01,.012,1),.64,0,.0003),
 'cast':mat('cast_magnesium',(.028,.035,.042,1),.47,.65,.00025),
 'fin':mat('dark_fin_edges',(.12,.14,.155,1),.38,.80),
 'gasket':mat('gasket',(.004,.005,.006,1),.80,.05),
 'gold':mat('gold_stanchions',(.66,.32,.075,1),.23,.92),
 'header':mat('heat_titanium',(.26,.19,.125,1),.34,.90,.00012),
 'seat':mat('saddle',(.01,.011,.014,1),.83,0,.00045),
 'red':mat('spring_red',(.43,.012,.009,1),.37,.18)}
def panel(b,pts,s,y,t,m):
 bm=bmesh.new();aa=[bm.verts.new((x,s*y,z)) for x,z in pts];bb=[bm.verts.new((x,s*(y+t),z)) for x,z in pts]
 bm.faces.new(aa);bm.faces.new(list(reversed(bb)))
 for i in range(len(pts)):j=(i+1)%len(pts);bm.faces.new((aa[i],bb[i],bb[j],aa[j]))
 bmesh.ops.recalc_face_normals(bm,faces=bm.faces);b.add(bm,Matrix.Identity(4),m,smooth=False,sharp_angle=32);bm.free()
def shell(b,stations,m,power=3.2):
 rings=[B.superellipse_ring(V(x,0,z),w,h,n=12 if not low else 8,power=power) for x,z,w,h in stations]
 bm=B.loft(rings);b.add(bm,Matrix.Identity(4),m,sharp_angle=35);bm.free()
def cyl(b,x,y,r,m,seg=12,r2=None):B.add_cyl(b,x,y,r,r2,mat=m,seg=seg if not low else max(6,seg//2),sharp=35)
def box(b,pos,size,m,bevel=.002):B.add_box(b,pos,size,m,bevel=bevel,seg=1)
def tube(b,pts,r,m,sides=10):B.add_tube(b,pts,r,m,sides=sides if not low else 6,samples=3 if not low else 2)
def replace(name,b):
 old=bpy.context.scene.objects[name];new=b.build();new.data.transform(old.matrix_world.inverted());old.data=new.data;bpy.data.objects.remove(new,do_unlink=True);return old
# Continuous swept plastics, independent side panels and properly layered graphics.
b=MeshBuilder('candidate_bodywork')
shell(b,[(.995,.675,.038,.009),(.932,.709,.066,.031),(.823,.675,.083,.046),(.703,.612,.079,.039),(.605,.565,.063,.014)],M['paint'])
shell(b,[(.91,.747,.025,.003),(.82,.728,.035,.004),(.703,.657,.027,.003),(.62,.611,.015,.002)],M['black'])
shell(b,[(.59,.617,.044,.006),(.49,.588,.066,.012),(.34,.564,.072,.014),(.19,.552,.066,.012),(.07,.547,.047,.006)],M['seat'])
shell(b,[(.28,.525,.065,.010),(.08,.522,.079,.009),(-.14,.500,.078,.009),(-.31,.477,.060,.006),(-.415,.465,.019,.003)],M['paint'])
shell(b,[(.18,.536,.034,.0015),(-.05,.525,.043,.0015),(-.28,.493,.029,.0015),(-.40,.472,.01,.001)],M['stripe'])
for s in (-1,1):
 panel(b,[(.974,.674),(.906,.712),(.793,.673),(.67,.60),(.617,.548),(.748,.547),(.902,.586)],s,.105,.007,M['paint'])
 panel(b,[(.947,.667),(.899,.69),(.79,.65),(.691,.592),(.649,.563),(.751,.575),(.881,.625)],s,.113,.0014,M['stripe'])
 panel(b,[(.924,.548),(.852,.555),(.73,.506),(.65,.434),(.752,.458),(.885,.504)],s,.12,.005,M['paint'])
 panel(b,[(.864,.54),(.806,.522),(.714,.472),(.746,.475),(.85,.52)],s,.126,.0014,M['stripe'])
 # Open rear side cover surrounds the upper silencer and shock window.
 panel(b,[(.272,.521),(.099,.521),(-.09,.485),(-.14,.432),(.03,.417),(.208,.46)],s,.096,.005,M['black'])
 panel(b,[(.257,.51),(.083,.511),(-.094,.477),(-.119,.45),(.061,.456),(.211,.477)],s,.102,.001,M['stripe'])
 for x,z,y in ((.9,.654,.117),(.729,.478,.13),(.161,.479,.108)):
  cyl(b,V(x,s*y,z),V(x,s*(y+.003),z),.005,M['black'],6)
cyl(b,V(.853,0,.737),V(.853,0,.746),.024,M['alloy'],16);box(b,V(.853,0,.749),(.03,.008,.004),M['black'])
replace('bodywork',b)
# Engine: dark cast cases, machined rim, fine alternating black cooling gaps.
b=MeshBuilder('candidate_engine')
outline=[(.49,.169),(.483,.262),(.537,.328),(.635,.35),(.741,.332),(.802,.288),(.799,.202),(.743,.15),(.585,.136)]
panel(b,outline,1,-.105,.21,M['cast'])
for s in (-1,1):
 panel(b,[(.501,.176),(.5,.261),(.55,.313),(.641,.333),(.73,.316),(.783,.28),(.779,.211),(.731,.164),(.592,.149)],s,.107,.008,M['gasket'])
 panel(b,[(.514,.182),(.512,.256),(.557,.302),(.639,.32),(.721,.306),(.771,.273),(.767,.217),(.726,.176),(.601,.162)],s,.116,.005,M['cast'])
 x,z,r=(.674,.244,.078)
 cyl(b,V(x,s*.12,z),V(x,s*.129,z),r+.005,M['alloy'],24)
 cyl(b,V(x,s*.129,z),V(x,s*.137,z),r,M['cast'],24)
 cyl(b,V(x,s*.137,z),V(x,s*.139,z),r-.014,M['cast'],24)
 for i in range(6):
  t=math.tau*i/6;cyl(b,V(x+(r-.005)*math.cos(t),s*.14,z+(r-.005)*math.sin(t)),V(x+(r-.005)*math.cos(t),s*.143,z+(r-.005)*math.sin(t)),.004,M['alloy'],6)
 for i in range(3):box(b,V(.548+i*.016,s*.127,.237),(.005,.007,.073-i*.009),M['cast'])
 for bx,bz in ((.542,.183),(.546,.282),(.727,.292),(.746,.198)):
  cyl(b,V(bx,s*.122,bz),V(bx,s*.128,bz),.0045,M['alloy'],6)
base=V(.724,0,.35);lean=Matrix.Rotation(math.radians(-10),4,'Y');up=lean@V(0,0,1)
B.add_box(b,base+up*.075,(.11,.13,.16),M['cast'],bevel=.006,rot=lean,seg=1)
for i in range(8 if not low else 5):
 z=.017+i*(.019 if not low else .032)
 B.add_box(b,base+up*z,(.145,.161,.006),M['fin'],bevel=.004,rot=lean,seg=1)
head=base+up*.171
B.add_box(b,head,(.148,.159,.038),M['cast'],bevel=.007,rot=lean,seg=1)
B.add_box(b,head+up*.024,(.12,.139,.008),M['alloy'],bevel=.005,rot=lean,seg=1)
cyl(b,head+up*.033,head+up*.074,.012,M['black'],8)
tube(b,[head+up*.072,V(.644,-.047,.605),V(.603,-.06,.59)],.004,M['black'],6)
cyl(b,V(.59,0,.435),V(.642,0,.435),.024,M['alloy'],12)
tube(b,[V(.591,0,.435),V(.533,0,.449),V(.493,0,.475)],.025,M['black'],8)
box(b,V(.611,0,.399),(.042,.044,.038),M['cast'])
tube(b,[V(.59,-.135,.177),V(.683,-.154,.126),V(.759,-.154,.13)],.005,M['alloy'],6)
cyl(b,V(.759,-.154,.13),V(.759,-.19,.13),.008,M['black'],8)
replace('engine',b)
# Header has a realistic slim constant section; separate flattened alloy silencer.
b=MeshBuilder('candidate_exhaust')
pts=[V(.801,0,.485),V(.856,-.025,.462),V(.901,-.074,.4),V(.899,-.147,.314),V(.845,-.161,.22),V(.747,-.165,.163),V(.61,-.166,.154),V(.473,-.163,.20),V(.371,-.163,.346)]
tube(b,pts,.020,M['header'],12)
rings=[]
for x,z,w,h in ((.372,.347,.015,.02),(.32,.382,.037,.047),(.12,.425,.037,.046),(-.018,.446,.026,.032),(-.043,.448,.012,.017)):
 rings.append(B.superellipse_ring(V(x,-.165,z),w,h,n=12 if not low else 8,power=3.0))
bm=B.loft(rings);b.add(bm,Matrix.Identity(4),M['alloy'],sharp_angle=35);bm.free()
for x,z in ((.293,.387),(.064,.438)):box(b,V(x,-.204,z),(.015,.003,.056),M['cast'],.003)
panel(b,[(.284,.382),(.255,.397),(.104,.425),(.035,.43),(.051,.405),(.231,.365)],-1,.204,.001,M['black'])
cyl(b,V(-.021,-.165,.445),V(-.046,-.165,.448),.014,M['cast'],12,r2=.011)
cyl(b,V(-.046,-.165,.448),V(-.047,-.165,.448),.007,M['black'],12)
replace('exhaust',b)
# Preserve moving mechanical geometry while assigning coherent manufactured finishes.
for name,m in [('frame',M['alloy']),('swingarm',M['alloy']),('pegs',M['alloy']),('sprocket_front',M['alloy']),('sprocket_rear',M['alloy']),('shock_spring',M['red']),('shock_body',M['cast']),('shock_shaft',M['alloy']),('shock_clevis',M['alloy'])]:
 ob=bpy.context.scene.objects[name];ob.data.materials.clear();ob.data.materials.append(m)
 for f in ob.data.polygons:f.material_index=0
# Keep the radiator dark between its machined fins; cast frame remains light.
ob=bpy.context.scene.objects['frame'];dark=len(ob.data.materials);ob.data.materials.append(M['cast']);edge=len(ob.data.materials);ob.data.materials.append(M['fin'])
for f in ob.data.polygons:
 c=ob.matrix_world@f.center
 if .868<c.x<.952 and .39<c.z<.624:f.material_index=edge if c.x>.916 else dark
# The complete stanchion surface keeps the same vertices and exact fork travel.
ob=bpy.context.scene.objects['fork_upper'];idx=len(ob.data.materials);ob.data.materials.append(M['gold']);n=B.FORK_DIR
for f in ob.data.polygons:
 c=ob.matrix_world@f.center;along=(c-B.P['front']).dot(n);radial=c-B.P['front']-n*along
 if .32<along<.86 and abs(abs(radial.y)-.10)<.026 and abs(radial.x)<.03 and abs(radial.z)<.03:f.material_index=idx
# Reserve chain/hose/spoke/blur exact topology. LOD follows production reducer.
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];protected={'chain','brake_hose','wheel_front_blur','wheel_rear_blur','wheel_front_spokes','wheel_rear_spokes'}
if low:
 # Start from production LOD; never further simplify manufactured moving interfaces.
 fixed=protected|{'fork_upper','fork_lower','swingarm','shock_body','shock_shaft','shock_clevis','shock_spring'}
 reserve=sum(C.tri_count(o) for o in meshes if o.name in fixed)
 flexible=[o for o in meshes if o.name not in fixed]
 total=sum(C.tri_count(o) for o in flexible)
 ratio=min(1,(5860-reserve)/total)
 for ob in flexible:C.decimate_to(ob,max(24,int(C.tri_count(ob)*ratio)))
 assert sum(C.tri_count(o) for o in meshes)<=6000
else:
 total=sum(C.tri_count(o) for o in meshes)
 if total>33300:
  ob=bpy.context.scene.objects['handlebar'];C.decimate_to(ob,max(800,C.tri_count(ob)-(total-33300)-40))
# UV binding before packing preserves sampled authored wheel/fork texture regions.
parts=[o for o in meshes if o.name not in {'chain','brake_hose','wheel_front_blur','wheel_rear_blur'}]
for ob in parts:
 if not ob.data.uv_layers:ob.data.uv_layers.new(name='SourceUV')
 source=ob.data.uv_layers.active;source.name='SourceUV'
 for material in ob.data.materials:
  if not material or not material.use_nodes:continue
  nt=material.node_tree
  for node in nt.nodes:
   if node.type=='BSDF_PRINCIPLED':node.name='BSDF'
   if node.type=='OUTPUT_MATERIAL' and node.is_active_output:node.name='OUT'
  for node in list(nt.nodes):
   if node.type=='TEX_IMAGE' and node.image:
    uv=nt.nodes.new('ShaderNodeUVMap');uv.uv_map='SourceUV';nt.links.new(uv.outputs['UV'],node.inputs['Vector'])
 ob.data.uv_layers.new(name='RemasterUV');ob.data.uv_layers.active=ob.data.uv_layers['RemasterUV'];ob.data.uv_layers['RemasterUV'].active_render=True
# Exact node contract is saved in an editable packed master before PBR flattening.
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(OUT.with_suffix('.blend')),compress=True)
# Separate large colour fields from the hundreds of tiny monochrome wheel islands.
# Native phone dimensions avoid the loader's canvas shrink; a single dense 19-part
# atlas allowed foreign red/white/black islands into downsampled surface texels.
groups={
 'plastics':{'bodywork','fork_upper','fork_lower'},
 'powertrain':{'engine','exhaust'},
 'chassis':{'frame','handlebar','pegs','swingarm','shock_body','shock_clevis','shock_shaft','shock_spring','sprocket_front','sprocket_rear'},
 'wheels':{'wheel_front','wheel_rear','wheel_front_spokes','wheel_rear_spokes'},
}
paths={};uv_report={}
for group,names in groups.items():
 members=[o for o in parts if o.name in names]
 C.unwrap_all(members,angle=66,margin=.006)
 # Blender may return a wider sheet when requested gutters cannot fit: fail or
 # normalise explicitly, never silently export UVs beyond the baked image.
 coords=[u.uv for o in members for u in o.data.uv_layers.active.data]
 high=max(max(u) for u in coords);scale=.99/high if high>1 else 1.0
 if high>1:
  for u in coords:u*=scale
 assert min(min(u) for u in coords)>=-1e-6 and max(max(u) for u in coords)<=1.000001
 uv_report[group]={'maxBeforeNormalising':high,'scale':scale,'uvsInUnitSquare':True}
 tex=C.bake_atlas(members,512 if not low else 256,str(OUT.parent/'textures'),OUT.stem+'_'+group,jpeg_quality=88,normal_size=256,orm_size=256,margin=6,ao_distance=.018,ao_samples=16,ao_strength=.55)
 C.assign_atlas(members,C.atlas_material('bike_remaster_'+group,tex));paths[group]=tex
# Remove source UV layer; one UV and material per object gives 23 runtime draws.
for ob in parts:
 uv=ob.data.uv_layers.get('SourceUV')
 if uv:ob.data.uv_layers.remove(uv)
# Include only original nodes: production assembly remains independently driven.
for o in bpy.context.scene.objects:
 if o.name in original:
  now={'matrix':[list(r) for r in o.matrix_local],'parent':o.parent.name if o.parent else None,'extras':{k:str(v) for k,v in o.items()}}
  assert now==original[o.name],f'Node contract changed: {o.name}'
C.export_glb(str(OUT),list(bpy.context.scene.objects),animations=False,meshopt=False)
report={'variant':a.variant,'lod':low,'source':a.input,'sourceSha256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),'parts':{o.name:C.tri_count(o) for o in meshes},'triangles':sum(C.tri_count(o) for o in meshes),'nodeContractExact':True,'texturePaths':paths,'uvPacking':uv_report,'authorship':'New Blender-authored panel/engine/exhaust geometry and PBR surfaces; production wheels/fork/interfaces retained; no neural geometry included.'}
OUT.with_suffix('.blender.json').write_text(json.dumps(report,indent=2)+'\n')
