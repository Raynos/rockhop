"""Original selected boot source/cavity diagnostic; never an outfit/art pass.

Dense source has its exact original corner atlas and normal detail. Compact
geometry contributes explicit section curves only, never an invented atlas.
"""
import hashlib
import json
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[4]
PREP = ROOT / 'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data/prep02/boots'
PINS = {'cleaned-donor.npz':'9849de6444632c2dcd1e1d76fda42ac27a7cbe8c7d2c0263ab2082e24b94777f',
        'retopology-prototype.npz':'d420da6bc7db4fa02ea095266dc174ff07cd3fb657cb0b01b91a319aa6b17853',
        'baseColorTexture.png':'5bda21b0d584f91aad83d310b868be6a575d28eddb1170e01e65c0b2071f4044',
        'metallicRoughnessTexture.png':'4017261b5f233cba5780578691a1508382295db4b157c4d175ad905bc98e5c30'}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
arguments=sys.argv[sys.argv.index('--')+1:];assert len(arguments)==1
out=Path(arguments[0]).resolve();assert out.is_relative_to(ROOT/'harness/out/rider-rebuild');out.mkdir(parents=True,exist_ok=False)
report={'accepted':False,'status':'RUNNING_SOURCE_DIAGNOSTIC','recipeSHA256':sha(__file__),
        'inputs':[{'path':str(PREP/name),'sha256':digest} for name,digest in PINS.items()],
        'sections':[],'renders':[], 'limits':['Read-only original donor diagnostic. No fit, cut acceptance, rig, whole outfit or art acceptance.',
            'Zero mesh boundary edges cannot determine whether a thick material has wearable ports.',
            'Compact section curves are geometric correspondence evidence; compact inherited atlas is not used.']}
def save(): (out/'source-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')

def section_loops(vertices,faces,axis,coordinate):
    distance=vertices[:,axis]-coordinate;selected=faces[(distance[faces].min(1)<0)&(distance[faces].max(1)>0)]
    nodes={};points=[];segments=[]
    for face in selected:
        cuts=[]
        for a,b in zip(face,np.roll(face,-1)):
            if distance[a]*distance[b]<0:
                key=tuple(sorted((int(a),int(b))))
                if key not in nodes:
                    t=-distance[a]/(distance[b]-distance[a]);nodes[key]=len(points);points.append(vertices[a]+t*(vertices[b]-vertices[a]))
                cuts.append(nodes[key])
        assert len(cuts)==2,'Unsupported triangle/section degeneracy';segments.append(cuts)
    points=np.asarray(points);segments=np.asarray(segments,dtype=np.int32);neighbors={}
    for a,b in segments:
        neighbors.setdefault(int(a),[]).append(int(b));neighbors.setdefault(int(b),[]).append(int(a))
    assert all(len(rows)==2 for rows in neighbors.values()),'Section is not a set of simple loops'
    remaining=set(neighbors);loops=[]
    while remaining:
        seed=remaining.pop();loop=[seed];previous=None;cursor=seed
        while True:
            choices=neighbors[cursor];following=choices[0] if choices[0]!=previous else choices[1]
            if following==seed:break
            assert following in remaining,'Repeated section point';remaining.remove(following);loop.append(following);previous,cursor=cursor,following
        loops.append(np.asarray(loop,dtype=np.int32))
    return points,segments,loops

def camera_at(camera,location,focus,scale):
    camera.location=location;direction=(Vector(focus)-camera.location).normalized();source_up=Vector((0,1,0))
    if abs(direction.dot(source_up))>.97:source_up=Vector((-1,0,0))
    right=direction.cross(source_up).normalized();up=right.cross(direction)
    camera.rotation_euler=Matrix((right,up,-direction)).transposed().to_euler();camera.data.ortho_scale=scale

def curve(name,points,loops,color):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=.003;data.bevel_resolution=0
    for loop in loops:
        spline=data.splines.new('POLY');spline.points.add(len(loop)-1);spline.points.foreach_set('co',np.column_stack([points[loop],np.ones(len(loop))]).ravel());spline.use_cyclic_u=True
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    material=bpy.data.materials.new(name+' geometric section ink');material.diffuse_color=(*color,1);material.use_nodes=True
    principal=material.node_tree.nodes.get('Principled BSDF');principal.inputs['Base Color'].default_value=(*color,1);principal.inputs['Roughness'].default_value=.65
    data.materials.append(material);return obj

try:
    assert all(sha(PREP/name)==digest for name,digest in PINS.items())
    dense=dict(np.load(PREP/'cleaned-donor.npz'));compact=dict(np.load(PREP/'retopology-prototype.npz'))
    bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.render.film_transparent=False
    world=bpy.data.worlds.new('Source diagnostic world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.25,.27,.31,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6;scene.world=world
    for index,location in enumerate(((-2,3,3),(2,2,-3),(-2,.8,-1))):
        data=bpy.data.lights.new('Source diagnostic light'+str(index),'AREA');data.energy=450 if index==0 else 250;data.shape='DISK';data.size=4
        light=bpy.data.objects.new(data.name,data);bpy.context.collection.objects.link(light);light.location=location;light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
    material=bpy.data.materials.new('Original dense boot exact corner atlas');material.use_nodes=True;nodes=material.node_tree.nodes;links=material.node_tree.links;principal=nodes.get('Principled BSDF')
    base=bpy.data.images.load(str(PREP/'baseColorTexture.png'));base.colorspace_settings.name='sRGB'
    mr=bpy.data.images.load(str(PREP/'metallicRoughnessTexture.png'));mr.colorspace_settings.name='Non-Color'
    tex=nodes.new('ShaderNodeTexImage');tex.image=base;links.new(tex.outputs['Color'],principal.inputs['Base Color'])
    tex=nodes.new('ShaderNodeTexImage');tex.image=mr;split=nodes.new('ShaderNodeSeparateColor');split.mode='RGB';links.new(tex.outputs['Color'],split.inputs['Color']);links.new(split.outputs['Green'],principal.inputs['Roughness']);links.new(split.outputs['Blue'],principal.inputs['Metallic'])
    mesh=bpy.data.meshes.new('Original dense source topology');mesh.from_pydata(dense['vertices'].tolist(),[],dense['faces'].tolist());mesh.update();mesh.materials.append(material)
    uv=mesh.uv_layers.new(name='Exact original dense corner UV');uv.data.foreach_set('uv',dense['originalCornerUV'].astype(np.float32).ravel())
    for face in mesh.polygons:face.use_smooth=True
    mesh.normals_split_custom_set([tuple(row) for row in dense['donorCornerNormals'].reshape(-1,3)])
    obj=bpy.data.objects.new('Original actual selected dense boot',mesh);bpy.context.collection.objects.link(obj)
    assert np.array_equal(np.asarray([tuple(v.co) for v in mesh.vertices]),dense['vertices'])
    assert np.array_equal(np.asarray([tuple(p.vertices) for p in mesh.polygons]),dense['faces'])
    transported=np.empty(len(uv.data)*2,dtype=np.float32);uv.data.foreach_get('uv',transported);assert np.array_equal(transported,dense['originalCornerUV'].astype(np.float32).ravel())
    report['denseExactBuffers']={'vertices':len(mesh.vertices),'triangles':len(mesh.polygons),'cornerUVFloat32Exact':True,'originalNormalsApplied':True};save()
    camera_data=bpy.data.cameras.new('Source diagnostic camera');camera_data.type='ORTHO';camera=bpy.data.objects.new(camera_data.name,camera_data);bpy.context.collection.objects.link(camera);scene.camera=camera
    views=[('original-toe-threequarter',(-3,1.4,2.7),(0,0,0),2.7),('original-lateral-profile',(0,.2,3.5),(0,0,0),2.5),('original-shaft-interior',(.55,3.0,0),(.55,-.15,0),1.45)]
    for name,location,focus,scale in views:
        camera_at(camera,location,focus,scale);scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True);report['renders'].append({'role':name,'path':scene.render.filepath,'sha256':sha(scene.render.filepath)});save()
    # Derived cutaway reveals the genuine source cavity. Never add source caps.
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,.18001,0),plane_no=(0,1,0),clear_outer=True,dist=1e-8);bm.to_mesh(mesh);bm.free();mesh.update()
    data_for_sections={};section_objects=[]
    for axis,coordinate in ((1,.18001),(1,.28001),(1,.35001),(0,.55001),(0,-.70001)):
        points,segments,loops=section_loops(compact['vertices'],compact['faces'],axis,coordinate);key='axis'+str(axis)+'-'+str(coordinate)
        data_for_sections[key+'-points']=points;data_for_sections[key+'-segments']=segments
        report['sections'].append({'axis':axis,'sourceCoordinate':coordinate,'loops':[{ 'vertices':len(loop),'bounds':[points[loop].min(0).tolist(),points[loop].max(0).tolist()],'center':points[loop].mean(0).tolist()} for loop in loops]})
        if axis==1 and coordinate==.18001:section_objects.append(curve('Actual compact section contour',points,loops,(1,.25,.05)))
    np.savez_compressed(out/'compact-section-loops.npz',**data_for_sections);save()
    camera_at(camera,(.35,2.5,.15),(.35,-.15,0),2.4);scene.render.filepath=str(out/'original-cavity-cutaway-compact-section.png');bpy.ops.render.render(write_still=True);report['renders'].append({'role':'original-cavity-cutaway-compact-section','path':scene.render.filepath,'sha256':sha(scene.render.filepath)})
    assert all(sha(PREP/name)==digest for name,digest in PINS.items());report['status']='ORIGINAL_SOURCE_DIAGNOSTIC_UNACCEPTED';report['originalSourceFilesBytePreserved']=True
except Exception as error:
    report['status']='REJECTED_SOURCE_DIAGNOSTIC';report['error']=type(error).__name__+': '+str(error);raise
finally:
    save();print(json.dumps({key:report[key] for key in ('status','error') if key in report}))
