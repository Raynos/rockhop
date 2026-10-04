"""Matched causal normal displays of frozen geometry; ambiguity retained."""
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
    for name in ('native','material','material-receipt','derived','derived-receipt','family','out'):
        parser.add_argument('--'+name,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID')
    pins={'trellis':('c9e0f72e6df3b2e2c8d2f8d81e989a644c8369b49e1bc845d9f1ebe41f5f8469','6ef98f41b43d1701d78245b3296065f9e6c3fe520868d995f361f89f14064779'),'pixal':('fa99516e7d19fb3de5f021d9c92bf5d80ad432891b7552c86d39bf6bd2b4d982','a0238f333ff628ddb2333853b93e33e96b703049548fa2413ceca5c041b6e089')}
    native_pin,material_pin=pins[args.family];assert sha(args.native)==native_pin
    receipt=json.loads(Path(args.material_receipt).read_text())
    assert receipt['maxCPUFloat64Error']<=1e-5 and receipt['originalArchiveStillIdentical']
    assert sha(args.material)==receipt['outputSHA256']==material_pin
    with np.load(args.native,allow_pickle=False) as raw:
        vertices,faces=raw['vertices'].copy(),raw['faces'].copy()
    with np.load(args.material,allow_pickle=False) as material:
        attrs=material['attrs'].copy()
    derived_receipt=json.loads(Path(args.derived_receipt).read_text())
    assert derived_receipt['nativeSHA256']==native_pin and sha(args.derived)==derived_receipt['outputArchiveSHA256']
    with np.load(args.derived,allow_pickle=False) as data:derived=data['faces'].copy()
    assert np.array_equal(np.sort(faces,axis=1),np.sort(derived,axis=1))
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
    # Same proven family display basis, positive determinant; raw arrays intact.
    axes=Matrix.Identity(4) if args.family=='trellis' else Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
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
    # Verify shader-side derivative values exactly; raw source attrs stay intact.
    check_color=np.empty(len(vertices)*4,np.float32)
    color.data.foreach_get('color',check_color)
    assert np.array_equal(check_color,np.column_stack((linear,np.ones(len(vertices),np.float32))).reshape(-1))
    for name,column in [('NativeMetallic',3),('NativeRoughness',4)]:
        check_attribute=np.empty(len(vertices),np.float32)
        mesh.attributes[name].data.foreach_get('value',check_attribute)
        assert np.array_equal(check_attribute,encoded[:,column])
    del check_color,check_attribute
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
    report={'accepted':False,'family':args.family,'recipeSHA256':sha(__file__),
            'nativeSHA256':native_pin,'materialSHA256':material_pin,
            'derivedSHA256':sha(args.derived),'derivedReceiptSHA256':sha(args.derived_receipt),
            'blender':bpy.app.version_string,'vertices':len(vertices),'triangles':len(faces),
            'positionsAndPerRowTriangleSetsExact':True,'materialReadbackExact':True,
            'displayScale':scale,'rawToBlenderMatrix':[list(r) for r in obj.matrix_world],
            'renderer':'CyclesCPU4threads8samples','resolution':[512,512],
            'camera':{'orthoScale':2.35,'target':list(target),'radius':4,'elevation':.25},
            'conditions':[],'rows':[], 'orientationLimits':derived_receipt['adapter'],
            'limits':['Gray comparison isolates shading with sampled material bytes retained.',
                      'No global orientation, intersection, topology repair or art acceptance.']}
    def save(): (out/'orbit.json').write_text(json.dumps(report,indent=2)+'\n')
    raw_normals=None
    for condition,smooth,selected in [('raw-replica',True,faces),('flat',False,faces),('derived',True,derived)]:
        mesh.loops.foreach_set('vertex_index',selected.reshape(-1))
        mesh.polygons.foreach_set('use_smooth',np.full(len(faces),smooth,dtype=bool))
        mesh.update();obj.update_tag();bpy.context.view_layer.update()
        check_v=np.empty(vertices.size,np.float32);check_f=np.empty(faces.size,np.int32)
        mesh.vertices.foreach_get('co',check_v);mesh.loops.foreach_get('vertex_index',check_f)
        assert np.array_equal(check_v,vertices.reshape(-1)) and np.array_equal(check_f,selected.reshape(-1))
        check_smooth=np.empty(len(faces),bool);mesh.polygons.foreach_get('use_smooth',check_smooth)
        assert (check_smooth==smooth).all()
        normals=np.empty((len(vertices),3),np.float32);mesh.vertices.foreach_get('normal',normals.reshape(-1))
        if raw_normals is None:raw_normals=normals.copy()
        report['conditions'].append({'name':condition,'smooth':smooth,
           'loadedFacesSHA256':hashlib.sha256(check_f.tobytes()).hexdigest(),
           'vertexNormalsSHA256':hashlib.sha256(normals.tobytes()).hexdigest(),
           'vertexNormalsChangedFromRaw':int(np.any(normals!=raw_normals,axis=1).sum())})
        np.savez_compressed(out/(condition+'-normals.npz'),vertexNormals=normals)
        del check_v,check_f,check_smooth,normals
        for frame in range(1 if condition=='raw-replica' else 24):
            yaw=frame*2*math.pi/24
            camera.location=target+Vector((4*math.sin(yaw),-4*math.cos(yaw),.25))
            camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
            path=frames/f'{frame:03d}-{condition}.png';scene.render.filepath=str(path)
            bpy.ops.render.render(write_still=True)
            report['rows'].append({'frame':frame,'yawDegrees':frame*15,'condition':condition,'path':str(path),'SHA256':sha(path)});save()
    assert sha(args.native)==native_pin and sha(args.material)==material_pin
    assert sha(args.derived)==derived_receipt['outputArchiveSHA256']
    report['frozenArchivesStillExact']=True;save()
    print(json.dumps({'frames':49,'conditions':report['conditions']}))


if __name__=='__main__':main()
