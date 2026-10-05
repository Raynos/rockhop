"""Played numeric stream: R and reflected-back L comparison, no native pose claim."""
import sys
import argparse
from pathlib import Path
import hashlib
import json
import numpy as np
import bpy
from mathutils import Vector


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--semantics',required=True)
    p.add_argument('--out',required=True);args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    out=Path(args.out);assert not out.exists();out.mkdir(parents=True)
    data=Path(args.data);sem=json.loads(Path(args.semantics).read_text())['gloves']
    coarse=np.array(sem['coarsePalmRegistration']['R']['matrix']);inv=np.linalg.inv(coarse)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    sources=[];objects=[]
    for side,offset in [('R',-1.05),('L',1.05)]:
        posefile=data/('flex-'+side+'.npz');g=np.load(data/('glove-'+side+'.npz'));motion=np.load(posefile)
        positions=motion['positions'].astype(float)
        if side=='L':positions[:,:,1]*=-1  # Comparison only, not candidate L geometry edit.
        positions=positions@inv[:3,:3].T+inv[:3,3]
        # Source upY/frontZ -> Blender upZ/front-Y for this fixed review camera.
        positions=positions[:,:,[0,2,1]];positions[:,:,1]*=-1;positions[:,:,0]+=offset
        faces=g['faces'][:,::-1] if side=='L' else g['faces']
        mesh=bpy.data.meshes.new(side+' Numeric LBS stream');mesh.from_pydata(positions[0].tolist(),[],faces.tolist());mesh.update()
        obj=bpy.data.objects.new(side,mesh);bpy.context.collection.objects.link(obj)
        mat=bpy.data.materials.new(side+' Gray diagnostic');mat.diffuse_color=(.58,.58,.58,1);mat.use_nodes=True
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.58,.58,.58,1)
        mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.65;obj.data.materials.append(mat)
        for polygon in mesh.polygons:polygon.use_smooth=True
        objects.append((obj,positions));sources.append({'side':side,'pose':str(posefile),'sha256':sha(posefile)})
        curve=bpy.data.curves.new(side+' label','FONT');curve.body=side+(' fitted prototype' if side=='R' else ' reflected-back comparison');curve.size=.12
        text=bpy.data.objects.new(side+' label',curve);bpy.context.collection.objects.link(text);text.location=(offset-.65,0,1.08)
        text.rotation_euler=(np.pi/2,0,0)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
    scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=960;scene.render.resolution_y=640
    scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard'
    scene.world.color=(.15,.15,.15);scene.render.use_persistent_data=True
    for loc,power in [((2,-4,4),500),((-3,-2,2),300),((1,3,4),400)]:
        light=bpy.data.lights.new('Silentarea','AREA');light.energy=power;light.size=4
        lamp=bpy.data.objects.new('Silentarea',light);bpy.context.collection.objects.link(lamp);lamp.location=loc
        lamp.rotation_euler=(Vector((0,0,.1))-lamp.location).to_track_quat('-Z','Y').to_euler()
    cam=bpy.data.cameras.new('Pairedsamecamera');cam.type='ORTHO';cam.ortho_scale=3.95
    camera=bpy.data.objects.new('Pairedsamecamera',cam);bpy.context.collection.objects.link(camera)
    camera.location=(.15,-5,1);camera.rotation_euler=(Vector((0,0,.02))-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
    frames=out/'frames';frames.mkdir();pins=[]
    for frame in range(49):
        for obj,positions in objects:obj.data.vertices.foreach_set('co',positions[frame].astype(np.float32).ravel());obj.data.update()
        target=frames/f'{frame:03}.png';scene.render.filepath=str(target);bpy.ops.render.render(write_still=True)
        pins.append({'index':frame,'sha256':sha(target)})
    (out/'render.json').write_text(json.dumps({'accepted':False,'recipeSHA256':sha(__file__),'sources':sources,'frames':pins,
        'fps':12,'displayNormalization':'InverseRcoarsepalm matrix; L reflected-back nativeY for geometricpair comparison; commonproper raw+Yup/raw+Zfront -> Blender Z/-Y.',
        'limits':'ManualFK/LBS graystream only. No native/engine/contact/grip/PBR/handedpair/art pass; currentLradialroll discrepancy is visible and frozen.'},indent=2)+'\n')


if __name__=='__main__':main()
