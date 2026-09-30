"""Headless CPU Blender raw-body diagnostic orbit; never alters source exports."""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--input',required=True);ap.add_argument('--out',required=True)
ap.add_argument('--gray',action='store_true');ap.add_argument('--frames',type=int,default=36)
ap.add_argument('--yaw-offset',type=float,default=0)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
source=Path(a.input).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
if (out/'manifest.json').exists():raise RuntimeError('Frozen render exists; use a separate output directory')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
scene=bpy.context.scene
meshes=[o for o in scene.objects if o.type=='MESH']
if not meshes:raise RuntimeError('Input has no mesh')
bpy.context.view_layer.update()
points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
lo=Vector([min(p[i] for p in points) for i in range(3)])
hi=Vector([max(p[i] for p in points) for i in range(3)])
height=hi.z-lo.z
if height<=0:raise RuntimeError('Invalid body height')
centre=(lo+hi)/2;normalizer=bpy.data.objects.new('Recorded uniform display normalization',None)
scene.collection.objects.link(normalizer)
for o in list(scene.objects):
    if o==normalizer or o.parent:continue
    mat=o.matrix_world.copy();o.parent=normalizer;o.matrix_world=mat
scale=1.8/height;normalizer.scale=(scale,)*3
normalizer.location=(-centre.x*scale,-centre.y*scale,-lo.z*scale)
bpy.context.view_layer.update()
material_changes=[]
if a.gray:
    gray=bpy.data.materials.new('Geometry diagnostic neutral gray');gray.diffuse_color=(.42,.42,.42,1)
    gray.use_nodes=True;bsdf=gray.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value=(.42,.42,.42,1)
    bsdf.inputs['Roughness'].default_value=.65
    for o in meshes:o.data.materials.clear();o.data.materials.append(gray)
else:
    for mat in bpy.data.materials:
        if not mat.use_nodes:continue
        for n in mat.node_tree.nodes:
            if n.type!='BSDF_PRINCIPLED':continue
            links=list(n.inputs['Metallic'].links)
            material_changes.append({'material':mat.name,'originalMetallic':float(n.inputs['Metallic'].default_value),'metallicLinksRemoved':len(links)})
            for link in links:mat.node_tree.links.remove(link)
            n.inputs['Metallic'].default_value=0
world=bpy.data.worlds.new('Common gray studio');world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world
target=Vector((0,0,.9))
for name,position,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=position
    o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('Exact yaw orthographic');camera=bpy.data.objects.new('Exact yaw orthographic',camera_data)
scene.collection.objects.link(camera);scene.camera=camera;camera_data.type='ORTHO';camera_data.ortho_scale=2.15
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.threads_mode='FIXED';scene.render.threads=6
scene.render.resolution_x=512;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
scene.render.fps=12
views=[]
for i in range(a.frames):
    yaw=i*360/a.frames+a.yaw_offset;angle=math.radians(yaw)
    camera.location=target+Vector((4*math.sin(angle),-4*math.cos(angle),0))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    path=out/f'{i:04d}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    views.append({'frame':i,'yaw':yaw,'file':path.name,'cameraMatrix':[list(row) for row in camera.matrix_world]})
report={'status':'RAW BODY DIAGNOSTIC; no rig or gameplay acceptance','input':str(source),'inputSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'rendererSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'blender':bpy.app.version_string,
        'triangles':sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons),
        'sourceBounds':[list(lo),list(hi)],'uniformScale':scale,'displayHeight':1.8,'orthoScale':2.15,
        'lightRig':'fixed studio600/350/450W area4/4/3m','resolution':[512,768],'samples':12,
        'grayDiagnostic':a.gray,'materialChanges':material_changes,'views':views,
        'limits':['Display normalization only, unchanged source GLB','Texture diagnostic forces metallic0 for all engines; native PBR remains preserved','Concept angles are approximate; rendered camera yaws are exact','Static unrigged orbit; later gates require actual animation/gameplay']}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
