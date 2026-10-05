"""Camera-only source-face classification film; no cut, fit, hide or skin."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review(points):
    result=np.asarray(points)[...,[0,2,1]].copy()
    result[...,1]*=-1
    return result


def main():
    parser=argparse.ArgumentParser()
    for key in ['preflight','boundary-context','out']:
        parser.add_argument('--'+key,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(args.out);assert not out.exists();out.mkdir(parents=True)
    p=json.loads(Path(args.preflight).read_text());assert sha(p['source']['path'])==p['source']['sha256'];assert sha(p['output']['path'])==p['output']['sha256']
    source=np.load(p['source']['path']);mask=np.load(p['output']['path']);vertices,faces=source['vertices'],source['faces']
    assert np.array_equal(mask['sourceXYZ'],vertices) and np.array_equal(mask['sourceFaces'],faces)
    assert len(faces)==16000 and int(mask['faceRemoveCandidate'].sum())==1456 and int(mask['faceAmbiguousConflict'].sum())==209
    assert not (mask['faceRemoveCandidate']&mask['protectedDistalFaces']).any()
    boundary=json.loads(Path(args.boundary_context).read_text());small=next(row for row in boundary['loops']if row['count']==3);small_ids=set(small['sourceVertexIds'])
    white=[i for i,face in enumerate(faces)if set(face.tolist())==small_ids];assert len(white)==1 and not mask['faceRemoveCandidate'][white[0]]
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    display=review(vertices);mesh=bpy.data.meshes.new('All original prototype faces');mesh.from_pydata(display.tolist(),[],faces.tolist());mesh.update()
    obj=bpy.data.objects.new('Uncut original prototype',mesh);bpy.context.collection.objects.link(obj);obj.hide_render=False;obj.hide_viewport=False
    colors=[('Retained source',(.42,.42,.42)),('Protected distal',(.06,.67,.62)),('Cavity candidate',(1.,.40,.03)),('Ambiguous exterior view',(.88,.06,.66)),('Secondary retained triangle',(.98,.98,.98))]
    for name,color in colors:
        material=bpy.data.materials.new(name);material.use_nodes=True
        node=material.node_tree.nodes['Principled BSDF'];node.inputs['Base Color'].default_value=(*color,1);node.inputs['Alpha'].default_value=1;node.inputs['Transmission Weight'].default_value=0;node.inputs['Roughness'].default_value=.72;mesh.materials.append(material)
    classes=np.zeros(len(faces),np.int32);classes[mask['protectedDistalFaces']]=1;classes[mask['faceRemoveCandidate']]=2;classes[mask['faceAmbiguousConflict']]=3;classes[white]=4
    for poly,index in zip(mesh.polygons,classes):poly.material_index=int(index);poly.use_smooth=False
    original_geometry_readback=np.empty(len(vertices)*3,np.float32);mesh.vertices.foreach_get('co',original_geometry_readback);restored=original_geometry_readback.reshape(-1,3)[:,[0,2,1]].astype(float);restored[:,2]*=-1
    # Inverse of display [X,-Z,Y] is [X,Y,Z]=[dX,dZ,-dY].
    assert np.array_equal(restored,vertices)
    triangles_readback=np.array([poly.vertices[:]for poly in mesh.polygons]);assert np.array_equal(triangles_readback,faces)
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=6;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=768;scene.render.resolution_y=768;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.use_persistent_data=True;scene.view_settings.view_transform='Standard';scene.world.color=(.16,.16,.16)
    for loc,power in [((2,-3,4),500),((-3,-2,2),350),((1,3,3),500),((0,1,-3),220)]:
        light=bpy.data.lights.new('Silent area','AREA');light.energy=power;light.size=4;lamp=bpy.data.objects.new('Silent area',light);bpy.context.collection.objects.link(lamp);lamp.location=loc;lamp.rotation_euler=(Vector((0,0,0))-lamp.location).to_track_quat('-Z','Y').to_euler()
    camera_data=bpy.data.cameras.new('Scope review moving camera');camera_data.type='ORTHO';camera=bpy.data.objects.new('Scope review moving camera',camera_data);bpy.context.collection.objects.link(camera);scene.camera=camera
    paths=[]
    # First24frames: complete-source moving rotation.
    for index in range(24):
        angle=2*np.pi*index/24
        paths.append({'stage':'outer source rotation','sourceLocation':[3*np.sin(angle),.5,3*np.cos(angle)],'sourceTarget':[0,-.02,-.15],'orthoScale':2.7})
    # Next18frames: move from lateral oblique into the existing wrist mouth.
    wrist=np.array([-.19893085956573486,-.655137,-.06397416442632675])
    for index in range(18):
        t=index/17;angle=np.deg2rad(65-65*t);radius=1.1
        loc=wrist+np.array([radius*np.sin(angle),-radius*np.cos(angle),.10*np.sin(np.pi*t)])
        paths.append({'stage':'wrist mouth moving path','sourceLocation':loc.tolist(),'sourceTarget':wrist.tolist(),'orthoScale':1.25})
    # Last6frames: uninterrupted small source-air camera arc, not a held pose.
    secondary=np.array(small['mean'])
    for index in range(6):
        angle=np.deg2rad(-15+30*index/5);loc=wrist+np.array([.75*np.sin(angle),-.75*np.cos(angle),.06])
        paths.append({'stage':'secondary boundary continuous arc','sourceLocation':loc.tolist(),'sourceTarget':secondary.tolist(),'orthoScale':.85})
    assert len(paths)==48 and all(paths[i]['sourceLocation']!=paths[i-1]['sourceLocation']for i in range(1,48))
    frames=out/'frames';frames.mkdir();pins=[]
    for index,pose in enumerate(paths):
        camera.location=review(np.array(pose['sourceLocation']));target=review(np.array(pose['sourceTarget']));camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.ortho_scale=pose['orthoScale'];target_file=frames/f'{index:03}.png';scene.render.filepath=str(target_file);bpy.ops.render.render(write_still=True);pins.append({'index':index,'sha256':sha(target_file)})
    readback=np.empty(len(vertices)*3,np.float32);mesh.vertices.foreach_get('co',readback);assert np.array_equal(readback,original_geometry_readback);assert np.array_equal(np.array([poly.vertices[:]for poly in mesh.polygons]),faces)
    report={'accepted':False,'status':'SOURCE_CLASSIFICATION_FILM_RENDERED_PARENT_REVIEW_PENDING','recipeSHA256':sha(__file__),'preflight':{'path':args.preflight,'sha256':sha(args.preflight)},'boundaryContext':{'path':args.boundary_context,'sha256':sha(args.boundary_context)},'source':p['source'],'mask':p['output'],'frames':pins,'fps':12,'cameraPaths':paths,'cameraPathsSHA256':hashlib.sha256(json.dumps(paths,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'reviewBasis':'Proper source+Yup/+Zfront to Blender+Zup/-Yfront: [X,-Z,Y]','sourceXYZAndFaceReadbackExact':True,'sourceTrianglesPresent':len(faces),'sourceHiddenTriangles':0,'allSourceMaterialsOpaque':True,'classFaceCounts':{colors[i][0]:int((classes==i).sum())for i in range(5)},'secondaryRetainedTriangleRow':white[0],'limits':'Camera-only original-source scope classification, not native animation, wearable/cavity occupancy, PBR, engine, art or device qualification. No cut, hide, fit, opacity or skin.'}
    (out/'render.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
