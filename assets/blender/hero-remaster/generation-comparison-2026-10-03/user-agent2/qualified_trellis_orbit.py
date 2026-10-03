"""Matched played gray/PBR orbits of all raw triangles, Blender CPU only."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    for name in ('native','material','material-receipt','out'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID')
    assert sha(args.native)=='c9e0f72e6df3b2e2c8d2f8d81e989a644c8369b49e1bc845d9f1ebe41f5f8469'
    receipt=json.loads(Path(args.material_receipt).read_text())
    assert receipt['maxCPUFloat64Error']<=1e-5 and receipt['originalArchiveStillIdentical']
    assert sha(args.material)==receipt['outputSHA256']=='6ef98f41b43d1701d78245b3296065f9e6c3fe520868d995f361f89f14064779'
    with np.load(args.native,allow_pickle=False) as raw:
        vertices,faces=raw['vertices'].copy(),raw['faces'].copy()
    with np.load(args.material,allow_pickle=False) as material:
        attrs=material['attrs'].copy()
    assert attrs.shape==(len(vertices),6) and np.isfinite(attrs).all()
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    mesh=bpy.data.meshes.new('All native TRELLIS triangles; no cleanup')
    # Avoid millions of transient Python lists; preserve native order exactly.
    mesh.vertices.add(len(vertices));mesh.loops.add(faces.size);mesh.polygons.add(len(faces))
    mesh.vertices.foreach_set('co',vertices.reshape(-1))
    mesh.loops.foreach_set('vertex_index',faces.reshape(-1))
    mesh.polygons.foreach_set('loop_start',np.arange(len(faces),dtype=np.int32)*3)
    mesh.polygons.foreach_set('loop_total',np.full(len(faces),3,np.int32))
    mesh.polygons.foreach_set('use_smooth',np.ones(len(faces),dtype=bool))
    mesh.update()
    check_v=np.empty(vertices.size,np.float32);check_f=np.empty(faces.size,np.int32)
    mesh.vertices.foreach_get('co',check_v);mesh.loops.foreach_get('vertex_index',check_f)
    assert np.array_equal(check_v,vertices.reshape(-1)) and np.array_equal(check_f,faces.reshape(-1))
    del check_v,check_f
    obj=bpy.data.objects.new('Unchanged raw geometry',mesh);bpy.context.collection.objects.link(obj)
    axes=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
    scale=2/float(np.ptp(vertices,axis=0).max())
    obj.matrix_world=axes@Matrix.Scale(scale,4)
    centre=(vertices.min(axis=0)+vertices.max(axis=0))/2
    target=obj.matrix_world@Vector(centre.tolist())
    # Match official texture writer's clipped8-bit PBR values for display.
    encoded=np.floor(np.clip(attrs,0,1)*255).astype(np.uint8).astype(np.float32)/255
    rgb=encoded[:,:3]
    linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4).astype(np.float32)
    color=mesh.color_attributes.new(name='NativeBaseColor',type='FLOAT_COLOR',domain='POINT')
    color.data.foreach_set('color',np.column_stack((linear,np.ones(len(vertices),np.float32))).reshape(-1))
    for name,column in [('NativeMetallic',3),('NativeRoughness',4)]:
        attr=mesh.attributes.new(name=name,type='FLOAT',domain='POINT')
        attr.data.foreach_set('value',encoded[:,column])
    neutral=bpy.data.materials.new('Constant neutral grey');neutral.use_nodes=True
    shader=neutral.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.5,.5,.5,1);shader.inputs['Roughness'].default_value=.65
    pbr=bpy.data.materials.new('Actual native sampled PBR vertex display');pbr.use_nodes=True
    shader=pbr.node_tree.nodes.get('Principled BSDF')
    for name,socket in [('NativeBaseColor','Base Color'),('NativeMetallic','Metallic'),('NativeRoughness','Roughness')]:
        node=pbr.node_tree.nodes.new('ShaderNodeAttribute');node.attribute_name=name
        pbr.node_tree.links.new(node.outputs['Color' if socket=='Base Color' else 'Fac'],shader.inputs[socket])
    obj.data.materials.append(neutral)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
    scene.render.resolution_x=scene.render.resolution_y=512;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.use_persistent_data=True;scene.world.color=(.16,.16,.16);scene.view_settings.view_transform='Standard'
    for name,location,watts in [('Key',(3,-3,4),450),('Fill',(2,4,3),350),('Rim',(-3,0,4),400)]:
        light=bpy.data.lights.new(name,'AREA');light.energy=watts;light.size=4
        lamp=bpy.data.objects.new(name,light);bpy.context.collection.objects.link(lamp);lamp.location=location
        lamp.rotation_euler=(target-lamp.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('Same matched full-shape orbit');data.type='ORTHO';data.ortho_scale=2.35
    camera=bpy.data.objects.new('Matched camera',data);bpy.context.collection.objects.link(camera);scene.camera=camera
    frames=out/'frames';frames.mkdir()
    report={'accepted':False,'recipeSHA256':sha(__file__),'nativeSHA256':sha(args.native),'materialSHA256':sha(args.material),
            'blender':bpy.app.version_string,'vertices':len(vertices),'triangles':len(faces),'loadedArraysByteIdentical':True,
            'geometryEdits':False,'winding':'Unchanged original faces','displayOnlyUniformScale':scale,'rawToBlenderMatrix':[list(r) for r in obj.matrix_world],
            'shading':'Derived averaged vertex normals; no vertex/topology smoothing',
            'material':'Native trilinear attrs at raw vertices, clipped8-bit baseColorSRGB/metallic/roughness; official opaque alpha convention',
            'renderer':'CyclesCPU4threads8samples','camera':{'orthoScale':2.35,'target':list(target),'radius':4,'elevation':.25},
            'fps':8,'frames':48,'resolution':[512,512],'rows':[],
            'limits':['Pervertex display derivative, not UV bake/map-level PBR or final-art acceptance.','Native6.32million triangles retained; no fit/rig/mobile/CUDA proof.']}
    def save():
        (out/'orbit.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    for frame in range(48):
        yaw=frame*2*math.pi/48
        camera.location=target+Vector((4*math.sin(yaw),-4*math.cos(yaw),.25))
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        row={'frame':frame,'yawDegrees':frame*7.5}
        for name,mat in [('gray',neutral),('pbr',pbr)]:
            obj.data.materials[0]=mat;path=frames/f'{frame:03d}-{name}.png'
            scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
            row[name]={'path':str(path),'SHA256':sha(path)}
        report['rows'].append(row);save()
    print(json.dumps({'frames':48,'triangles':len(faces),'loadedArraysByteIdentical':True}))


if __name__=='__main__':
    main()
