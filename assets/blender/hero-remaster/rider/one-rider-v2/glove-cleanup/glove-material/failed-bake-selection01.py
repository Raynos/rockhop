"""One native-UV black leather micrograin CPU bake, no geometry/weight edits."""
import hashlib,json,math,time
from pathlib import Path
import bpy,numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop');BASE='one-rider-v2/glove-cleanup/glove-material'
OUT=ROOT/'docs/evidence/hero-remaster'/BASE;OUT.mkdir(exist_ok=True)
RUN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')/BASE;RUN.mkdir(exist_ok=True)
ASSEMBLY=ROOT/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/neutral-assembly'
CLEAN=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/neutral-assembly/body-neutral-hands.blend')
NATIVE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2/neutral-anatomy/neutral-anatomical-hands.blend')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if (OUT/'report.json').exists():raise RuntimeError('Frozen material trial exists')
start=time.perf_counter();sources={str(p):sha(p) for p in [CLEAN,NATIVE]};proof=json.loads((ASSEMBLY/'native-weight-proof.json').read_text());build=json.loads((ASSEMBLY/'report.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(NATIVE));native={}
for side in ['L','R']:
    obj=bpy.data.objects[f'NEW neutral anatomical hand {side}'];uv=obj.data.uv_layers.active
    native[side]={tuple(sorted(p.vertices)):{int(obj.data.loops[i].vertex_index):list(uv.data[i].uv) for i in p.loop_indices} for p in obj.data.polygons}
    assert len(native[side])==1656
bpy.ops.wm.open_mainfile(filepath=str(CLEAN));body=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh=body.data
def meshproof():
    return hashlib.sha256(json.dumps({'vertices':[list(v.co) for v in mesh.vertices],'faces':[list(p.vertices) for p in mesh.polygons],'originalUV':[list(v.uv) for v in mesh.uv_layers[0].data],'groups':[[[g.group,g.weight] for g in v.groups] for v in mesh.vertices]},separators=(',',':')).encode()).hexdigest()
geometry_before=meshproof();uv0=mesh.uv_layers[0];gloveuv=mesh.uv_layers.new(name='NativeGloveAtlas')
for a,b in zip(gloveuv.data,uv0.data):a.uv=b.uv
assignments=[]
for hand in proof['hands']:
    side=hand['side'];first=hand['firstNativeVertexIndex'];last=first+hand['nativeVertices'];count=0
    for polygon in mesh.polygons:
        if all(first<=i<last for i in polygon.vertices):
            face=native[side][tuple(sorted(int(i)-first for i in polygon.vertices))]
            for li in polygon.loop_indices:gloveuv.data[li].uv=face[int(mesh.loops[li].vertex_index)-first]
            count+=1
    assert count==1656;assignments.append({'side':side,'nativeFaces':count,'nativeUVSource':str(NATIVE)})
    groups={g.index:g.name for g in body.vertex_groups};wrist={v.index for v in mesh.vertices[:build['sourceVertexPrefixCount']] if any(groups[g.group]=='wrist.'+side and g.weight>.999 for g in v.groups)}
    mid=set(range(last,last+22));native_loop=set()
    # Actual native boundary is recovered from complete source indices.
    cage=np.load(Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2/neutral-anatomy/display-complete')/f'neutral-complete-{side}.npz');native_loop={first+int(i) for i in cage['wristLoop']}
    levels={**{i:0 for i in wrist},**{i:.5 for i in mid},**{i:1 for i in native_loop}};centre=next(p['centre'] for p in build['patches'] if p['nativeSide']==side)
    seam_count=0
    for p in mesh.polygons:
        if p.material_index==1 and all(i in levels for i in p.vertices) and any(i in wrist or i in mid for i in p.vertices):
            angles=[math.atan2(mesh.vertices[i].co.y-centre[1],mesh.vertices[i].co.x-centre[0])%(2*math.pi) for i in p.vertices]
            if max(angles)-min(angles)>math.pi:angles=[a+2*math.pi if a<math.pi else a for a in angles]
            for li,angle in zip(p.loop_indices,angles):
                i=mesh.loops[li].vertex_index;gloveuv.data[li].uv=((.04 if side=='L' else .54)+.4*angle/(2*math.pi),.88+.09*levels[i])
            seam_count+=1
    assignments[-1]['seamFaces']=seam_count
mesh.uv_layers.active_index=mesh.uv_layers.find(gloveuv.name);gloveuv.active_render=True
mesh.calc_loop_triangles();uv_triangles=[]
for t in mesh.loop_triangles:
    if t.material_index==1:uv_triangles.append([list(gloveuv.data[i].uv) for i in t.loops])
# Strict pixel-centre interior raster avoids counting adjacent shared edges.
resolution=1024;coverage=np.zeros((resolution,resolution),dtype=np.uint16);degenerate=0
for tri in uv_triangles:
    p=np.array(tri);lo=np.maximum(0,np.floor(p.min(0)*resolution-.5).astype(int));hi=np.minimum(resolution-1,np.ceil(p.max(0)*resolution-.5).astype(int));a,b,c=p
    denominator=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(denominator)<1e-12:degenerate+=1;continue
    xs=(np.arange(lo[0],hi[0]+1)+.5)/resolution;ys=(np.arange(lo[1],hi[1]+1)+.5)/resolution;x,y=np.meshgrid(xs,ys)
    u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/denominator;v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/denominator;inside=(u>1e-5)&(v>1e-5)&(u+v<1-1e-5)
    coverage[lo[1]:hi[1]+1,lo[0]:hi[0]+1]+=inside
overlap=int((coverage>1).sum());assert overlap==0,'Native/transition UV overlap: stop before bake'
(OUT/'uv-layout.json').write_text(json.dumps({'source':str(NATIVE),'sourceSHA256':sources[str(NATIVE)],'nativeFaces':3312,'seamAssignments':assignments,'triangles':uv_triangles,'rasterResolution':resolution,'strictInteriorOverlapPixels':overlap,'degenerateUVTriangles':degenerate,'sourceOriginalUVPreserved':True,'layout':'native sourceUV plus isolated topband seamcharts; no geometry unwrap/remesh'},indent=2)+'\n')
material=bpy.data.materials.new('Baked black leather micrograin');material.use_nodes=True;nodes=material.node_tree.nodes;links=material.node_tree.links;nodes.clear();output=nodes.new('ShaderNodeOutputMaterial');shader=nodes.new('ShaderNodeBsdfPrincipled');links.new(shader.outputs['BSDF'],output.inputs['Surface']);shader.inputs['Metallic'].default_value=0
coords=nodes.new('ShaderNodeTexCoord');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1200;noise.inputs['Detail'].default_value=2;noise.inputs['Roughness'].default_value=.55;links.new(coords.outputs['Object'],noise.inputs['Vector'])
color=nodes.new('ShaderNodeValToRGB');color.color_ramp.elements[0].color=(.009,.010,.012,1);color.color_ramp.elements[1].color=(.019,.020,.022,1);links.new(noise.outputs['Fac'],color.inputs[0]);links.new(color.outputs['Color'],shader.inputs['Base Color'])
rough=nodes.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=0;rough.inputs['From Max'].default_value=1;rough.inputs['To Min'].default_value=.58;rough.inputs['To Max'].default_value=.72;links.new(noise.outputs['Fac'],rough.inputs[0]);links.new(rough.outputs[0],shader.inputs['Roughness'])
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.00012;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])
mesh.materials[1]=material;bpy.context.view_layer.objects.active=body;body.select_set(True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.bake.use_selected_to_active=False;scene.render.bake.margin=8;scene.render.bake.use_clear=True
maps=[]
for label,bake in [('basecolor','DIFFUSE'),('roughness','ROUGHNESS'),('normal','NORMAL')]:
    image=bpy.data.images.new('Glove-'+label,width=2048,height=2048,alpha=False);image.colorspace_settings.name='sRGB' if label=='basecolor' else 'Non-Color'
    targets=[]
    for mat in mesh.materials:
        node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;mat.node_tree.nodes.active=node;targets.append((mat,node))
    if bake=='DIFFUSE':scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True
    bpy.ops.object.bake(type=bake)
    image.filepath_raw=str(RUN/(label+'.png'));image.file_format='PNG';image.save()
    for mat,node in targets:mat.node_tree.nodes.remove(node)
    maps.append({'label':label,'image':image,'file':image.filepath_raw,'sha256':sha(Path(image.filepath_raw))})
# Replace every procedural input with the actual baked maps.
for node in [coords,noise,color,rough,bump]:nodes.remove(node)
uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map=gloveuv.name
for row in maps:
    node=nodes.new('ShaderNodeTexImage');node.image=row['image'];links.new(uvnode.outputs[0],node.inputs['Vector'])
    if row['label']=='normal':normal=nodes.new('ShaderNodeNormalMap');normal.uv_map=gloveuv.name;links.new(node.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs[0],shader.inputs['Normal'])
    else:links.new(node.outputs['Color'],shader.inputs['Base Color' if row['label']=='basecolor' else 'Roughness'])
geometry_after=meshproof();assert geometry_before==geometry_after,'Geometry/originalUV/nativeweights altered by material bake'
for row in maps:row['image'].pack()
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'bodyPBR.blend'));bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.export_scene.gltf(filepath=str(RUN/'bodyPBR.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False)
assert sources=={p:sha(Path(p)) for p in sources}
(OUT/'report.json').write_text(json.dumps({'status':'One actual UV material bake; parent PBR review pending','sourceHashesBefore':sources,'sourceHashesAfter':{p:sha(Path(p)) for p in sources},'geometryOriginalUVNativeWeightsSHA256Before':geometry_before,'geometryOriginalUVNativeWeightsSHA256After':geometry_after,'uvProof':'uv-layout.json','maps':[{k:v for k,v in row.items() if k!='image'} for row in maps],'bakeResolution':2048,'samples':16,'backend':'CyclesCPU','threads':4,'rayScope':'Same-mesh procedural shader evaluation into nativeUV; selected-to-active false, no highpoly raycast/detail transfer claim','normalSource':'Actual authored3D micrograin bump shader baked tangentNORMAL; must verify output variation/reimport before claiming normalmap','materialNodesAfterBake':[n.bl_idname for n in nodes],'masterSHA256':sha(RUN/'bodyPBR.blend'),'glbSHA256':sha(RUN/'bodyPBR.glb'),'wallSeconds':time.perf_counter()-start,'recipeSHA256':sha(Path(__file__))},indent=2)+'\n');print('GLOVE_CPU_MATERIAL_BAKE_FROZEN',flush=True)
