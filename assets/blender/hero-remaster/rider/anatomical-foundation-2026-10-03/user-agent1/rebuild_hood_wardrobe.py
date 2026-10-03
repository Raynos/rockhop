"""Rebuild hood ownership/seam and coherent native wardrobe texture, not identity."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'reference', 'out', 'evidence']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, reference, out, evidence = [Path(getattr(a, n)).resolve() for n in ['source', 'reference', 'out', 'evidence']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest(); pins = {str(p): sha(p) for p in [source, reference]}
assert pins[str(reference)] == 'd48e3913d368275488a135da1779b22a6ebb42ae5e719b3ebbcfbce58932ae9a'
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
if (out/'rider.blend').exists():
    raise RuntimeError('Frozen hood construction exists')
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']; root = bpy.data.objects['Foundation file frame, game x0.65']
original = bpy.data.objects['Separate fitted sweatshirt control, hood not constructed']; old_hood = bpy.data.objects['Protected mustard hood on own rig']
vertices = [list(v.co) for v in original.data.vertices]; original_count = len(vertices); faces = [list(p.vertices) for p in original.data.polygons]
weights = [{original.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>0 and original.vertex_groups[g.group].name in rig.data.bones} for v in original.data.vertices]
uv_faces = [[list(original.data.uv_layers.active.data[l].uv) for l in p.loop_indices] for p in original.data.polygons]
materials = [0]*len(faces); source_fields = [(i,1.) for i in range(original_count)]
edge_count = {}
for face in faces:
    for i,j in zip(face,face[1:]+face[:1]):
        edge=tuple(sorted((i,j))); edge_count[edge]=edge_count.get(edge,0)+1
neck_edges=[e for e,c in edge_count.items() if c==1 and min(vertices[i][2] for i in e)>1.5]
neck_ids=sorted({i for e in neck_edges for i in e});assert len(neck_ids)==20
center=np.array([vertices[i] for i in neck_ids]).mean(0)
angle=lambda i:math.atan2(vertices[i][1]-center[1],vertices[i][0]-center[0])%(2*math.pi)
arc=sorted([i for i in neck_ids if .65<=angle(i)<=2*math.pi-.65],key=angle);assert len(arc)>=12
start_angle,end_angle=angle(arc[0]),angle(arc[-1]); rings=[arc]
# An open folded hood pattern shares actual neckline vertices. It owns upper
# torso deformation; donor shoulder/arm triangles and nearest-body weights stop.
for row in range(1,7):
    t=row/6; ring=[]
    for col,old in enumerate(arc):
        if col in [0,len(arc)-1]:
            ring.append(old);continue
        phi=angle(old); back=math.sin(math.pi*(phi-start_angle)/(end_angle-start_angle))
        p=np.array(vertices[old]); p[0]-=back*(.100*t+.025*math.sin(math.pi*t))
        p[1]+=math.copysign(.036*t*back, p[1]) if abs(p[1])>1e-5 else 0
        p[2]-=back*(.060*t+.045*math.sin(math.pi*t))
        index=len(vertices); vertices.append(p.tolist()); ring.append(index)
        # Original seam attachment follows its existing own field; new cap
        # smoothly belongs to chest, without any upper-arm/forearm ownership.
        own={n:w*(1-t) for n,w in weights[old].items() if n in ['chest','neck','spine']};own['chest']=own.get('chest',0)+t
        total=sum(own.values());weights.append({n:w/total for n,w in own.items()});source_fields.append((old,1-t))
    rings.append(ring)
for row in range(6):
    for col in range(len(arc)-1):
        ids=[rings[row][col],rings[row+1][col],rings[row+1][col+1],rings[row][col+1]]
        uv=[[col/(len(arc)-1),row/6],[col/(len(arc)-1),(row+1)/6],[(col+1)/(len(arc)-1),(row+1)/6],[(col+1)/(len(arc)-1),row/6]]
        clean=[];clean_uv=[]
        for i,u in zip(ids,uv):
            if i not in clean:clean.append(i);clean_uv.append(u)
        if len(clean)>=3:faces.append(clean);uv_faces.append(clean_uv);materials.append(1)
hood_end=len(vertices)
# A shallow native-fitted kangaroo pocket, with clipped upper corners and a
# small central fabric allowance. No torso/face geometry is adopted from donor.
original.data.calc_loop_triangles(); base=np.array([v.co[:] for v in original.data.vertices]); tris=np.array([t.vertices[:] for t in original.data.loop_triangles])
tree=BVHTree.FromPolygons([Vector(p) for p in base],tris.tolist(),all_triangles=True)
def field(point):
    q,normal,tri,distance=tree.find_nearest(Vector(point));ids=tris[tri];matrix=np.column_stack([base[ids[1]]-base[ids[0]],base[ids[2]]-base[ids[0]]])
    yz=np.linalg.lstsq(matrix,np.array(q)-base[ids[0]],rcond=None)[0];b=np.clip([1-sum(yz),yz[0],yz[1]],0,1);b/=sum(b);w={}
    for old,factor in zip(ids,b):
        for n,v in weights[old].items():w[n]=w.get(n,0)+factor*v
    w=sorted(w.items(),key=lambda p:-p[1])[:4];s=sum(v for n,v in w);return {n:v/s for n,v in w},ids,b
pocket=[];pocket_fields={}
for row in range(5):
    t=row/4;z=.995+.140*t;width=.097-.030*max(0,(t-.6)/.4);ring=[]
    for col in range(9):
        u=col/8;y=(u*2-1)*width;hit,normal,tri,dist=tree.ray_cast(Vector((.45,y,z)),Vector((-1,0,0)))
        if hit is None:raise RuntimeError('Native front pocket surface ray missed')
        p=np.array(hit);p[0]+=.0025+.006*math.sin(math.pi*u)*math.sin(math.pi*t)
        i=len(vertices);vertices.append(p.tolist());ring.append(i);w,ids,b=field(p);weights.append(w);source_fields.append((int(ids[int(np.argmax(b))]),0.));pocket_fields[i]=(ids,b)
    pocket.append(ring)
for row in range(4):
    for col in range(8):
        # +X front normal: increasingY crossed with increasingZ.
        faces.append([pocket[row][col],pocket[row][col+1],pocket[row+1][col+1],pocket[row+1][col]])
        uv_faces.append([[col/8,row/4],[(col+1)/8,row/4],[(col+1)/8,(row+1)/4],[col/8,(row+1)/4]]);materials.append(1)
mesh=bpy.data.meshes.new('Clean native hoodie sewn neckline and fitted pocket');mesh.from_pydata(vertices,[],faces);mesh.update()
hoodie=bpy.data.objects.new('Sewn clean hoodie with dropped hood',mesh);bpy.context.collection.objects.link(hoodie);hoodie.parent=root
for bone in rig.data.bones:hoodie.vertex_groups.new(name=bone.name)
for i,w in enumerate(weights):
    for name,value in w.items():hoodie.vertex_groups[name].add([i],value,'REPLACE')
layer=mesh.uv_layers.new(name='UVMap')
for poly,uvs in zip(mesh.polygons,uv_faces):
    for loop,uv in zip(poly.loop_indices,uvs):layer.data[loop].uv=uv
source_id=mesh.attributes.new(name='_SOURCE_ID',type='FLOAT',domain='POINT')
for i,v in enumerate(source_id.data):v.value=i
hoodie.shape_key_add(name='Basis')
for old_key in original.data.shape_keys.key_blocks:
    if old_key.name=='Basis':continue
    key=hoodie.shape_key_add(name=old_key.name);delta=np.array([v.co[:] for v in old_key.data])-base
    for i in range(len(vertices)):
        if i<original_count:d=delta[i]
        elif i<hood_end:
            old,amount=source_fields[i];d=delta[old]*amount
        else:
            ids,b=pocket_fields[i];d=b@delta[ids]
        key.data[i].co=Vector(vertices[i])+Vector(d)
armature=hoodie.modifiers.new('Own unchanged 51-joint rig','ARMATURE');armature.object=rig
# Low-contrast woven material on coherent native UVs replaces unregistered,
# angular donor-shadow stains. It carries no high-frequency baked pose shadows.
size=512; yy,xx=np.mgrid[0:size,0:size];u=xx/(size-1);v=yy/(size-1)
grain=.006*np.sin(2*math.pi*u*180)*np.cos(2*math.pi*v*180)+.008*np.sin(2*math.pi*v*55)
colour=np.clip(np.array([180/255,123/255,51/255])[None,None,:]*(1+grain[:,:,None]),0,1);pixels=np.concatenate([colour,np.ones((size,size,1))],axis=2).astype(np.float32)
tex=bpy.data.images.new('Coherent approved mustard woven albedo',width=size,height=size,alpha=True);tex.pixels.foreach_set(pixels.ravel());tex.filepath_raw=str(out/'coherent-mustard-albedo.png');tex.file_format='PNG';tex.save();tex.pack()
m=bpy.data.materials.new('Coherent approved mustard cotton PBR');m.use_nodes=True;nt=m.node_tree;bs=nt.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.82;bs.inputs['Metallic'].default_value=0;bs.inputs['Specular IOR Level'].default_value=.125
node=nt.nodes.new('ShaderNodeTexImage');node.image=tex;nt.links.new(node.outputs['Color'],bs.inputs['Base Color'])
mesh.materials.append(m);mesh.materials.append(m)
for f,slot in zip(mesh.polygons,materials):f.material_index=slot;f.use_smooth=True
original.hide_render=True;old_hood.hide_render=True;hoodie['appearanceConstruction']='unaccepted04 shared native neckline/chest-owned dropped hood/coherent cotton'
root['rockhopAppearanceCandidate']='unaccepted appearance04 sewn hood and coherent wardrobe'
for o in bpy.data.objects:o.select_set(False)
selected=[o for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]+[root,rig]
for o in selected:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(out/'rider.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(out/'rider.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False,export_attributes=True,export_extras=True,export_morph=True)
controller=json.loads((source.parent/'source-normals-controller.json').read_text());controller.update(status='UNACCEPTED appearance04 sewn hood/coherent wardrobe, unchanged original local correctives plus explicit graft/pocket interpolation',
    candidateMasterSHA256=sha(out/'rider.blend'),candidateGLBSHA256=sha(out/'rider.glb'),parentAppearanceMasterSHA256=sha(source),candidateMeshNames={'cloth':hoodie.name,'jeans':'Separate fitted native trousers control','body':'Canonical body with hidden head interface'})
(out/'corrective-driver.json').write_text(json.dumps(controller,indent=2)+'\n')
assert pins=={str(p):sha(p) for p in [source,reference]}
report={'status':'UNACCEPTED clean sewn-hood/coherent wardrobe construction; continuous matched moving review pending','pins':pins,'recipeSHA256':sha(__file__),
    'masterSHA256':sha(out/'rider.blend'),'quantizedGLBSHA256':sha(out/'rider.glb'),'hoodieName':hoodie.name,
    'originalShirtVertices':original_count,'hoodVerticesAdded':hood_end-original_count,'pocketVerticesAdded':len(vertices)-hood_end,'vertices':len(vertices),'polygons':len(faces),
    'nativeNecklineVertices':neck_ids,'sharedAttachmentArcIDs':arc,'hoodOwner':'Original shared seam, then chest/spine/neck only; no shoulder/upperArm/forearm weights on added cap',
    'albedoSHA256':sha(out/'coherent-mustard-albedo.png'),'albedoBaseSRGBBytes':[180,123,51],'variationFraction':.014,
    'limits':['Protected head/body/jeans/boot02/glove geometry and source identity unchanged; original shirt/hood retained hidden in native master.',
        'Original1250shirt basis/UV/weights/local key deltas retained at same indices; new sewn hood and pocket fields explicit.',
        'Root01 rigid donor hood flap and angular albedo donation are replaced, not claimed visually fixed until matched played review.',
        'Drop-hood shape/pocket are native authored construction consistent with approved wardrobe; not final fabric/collision or source exact-hood preservation.',
        'Protected NORMAL raw-source export derivative must follow native export before engine handoff; native quantization remains explicit.',
        'Remaining sleeve/knee/hem fit, supported bike contact, mobile LOD and M0–M5 acceptance stay open; no player promotion.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print('SEWN_HOOD_WARDROBE_READY',report['vertices'],report['sharedAttachmentArcIDs'],flush=True)
