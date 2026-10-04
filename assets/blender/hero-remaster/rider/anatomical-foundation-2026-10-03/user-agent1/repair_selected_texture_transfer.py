"""Isolate ray-bake failure with direct source-UV sampling on frozen geometry.

Every occupied atlas texel queries the registered original donor surface.
No UV interpolation across source triangles, new colors, or geometry change.
This transfer candidate remains unaccepted pending root's matched played view.
"""
import argparse, hashlib, json, math, struct, sys, time, zlib
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','registration-recipe','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
source,recipe,out,evidence=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','registration-recipe','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'direct-transfer.blend').exists(),'Keep frozen derivatives'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={str(p):sha(p) for p in [source,recipe]}
assert pins[str(source)]=='6ef79e38e3dc86b635977ba17a2f2f6100721715b002c4e831b8bcce90ed4e93'
bpy.ops.wm.open_mainfile(filepath=str(source))
high=bpy.data.objects['Exact selected Hunyuan high-poly PBR donor, display frame only']
body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
old=bpy.data.objects['Selected Hunyuan underarm fitted wearable, unrigged']
pattern=bpy.data.objects['Separate fitted sweatshirt control, hood not constructed']
definition=recipe.read_text();definition=definition[definition.index('height=.472'):definition.index('lineage=[]')]
exec(compile(definition,str(recipe),'exec'))
high.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in high.data.loop_triangles],dtype=np.int32)
loop=np.array([t.loops[:] for t in high.data.loop_triangles],dtype=np.int32)
donor=np.array([v.co[:] for v in high.data.vertices],dtype=np.float64)
registered=np.empty_like(donor)
for side,sign in [('R',1),('L',-1)]:
    ids=np.flatnonzero(donor[:,0]>=0 if sign==1 else donor[:,0]<0);p=donor[ids]
    torso=p@torso_matrix[:3,:3].T+torso_matrix[:3,3];s=source_anchors[side];target=target_anchors[side]
    distances=[];options=[]
    for segment in [0,1]:
        axis=s[segment+1]-s[segment];u=np.clip((p-s[segment])@axis/np.dot(axis,axis),0,1);center=s[segment]+u[:,None]*axis
        rotation=np.array(Vector(display_to_native@axis).rotation_difference(Vector(target[segment+1]-target[segment])).to_matrix())@display_to_native
        options.append(target[segment]+u[:,None]*(target[segment+1]-target[segment])+(p-center)@rotation.T*.50)
        distances.append(np.linalg.norm(p-center,axis=1))
    arm=np.where((distances[0]<=distances[1])[:,None],options[0],options[1])
    alpha=np.clip(((np.abs(p[:,0])-.36)-np.maximum(.46-p[:,2],0)*.22)/.15,0,1);alpha=alpha*alpha*(3-2*alpha)
    registered[ids]=(1-alpha[:,None])*torso+alpha[:,None]*arm
checks=np.linspace(0,len(donor)-1,257,dtype=int)
registration_error=max(np.linalg.norm(registered[i]-register(donor[i])[0]) for i in checks)
assert registration_error<1e-12
tree=BVHTree.FromPolygons([Vector(p) for p in registered],tri.tolist(),all_triangles=True)
sourceUV=np.array([u.uv[:] for u in high.data.uv_layers.active.data],dtype=np.float64)
old.data.calc_loop_triangles();gtri=np.array([t.vertices[:] for t in old.data.loop_triangles],dtype=np.int32)
gloops=np.array([t.loops[:] for t in old.data.loop_triangles],dtype=np.int32)
xyz=np.array([v.co[:] for v in old.data.vertices]);atlasUV=np.array([u.uv[:] for u in old.data.uv_layers.active.data])
resolution=2048;owner=np.full((resolution,resolution),-1,dtype=np.int32);points=np.zeros((resolution,resolution,3),dtype=np.float32)
for i,(vs,ls) in enumerate(zip(gtri,gloops)):
    uv=atlasUV[ls]*resolution-.5;lo=np.maximum(np.ceil(uv.min(0)).astype(int),0);hi=np.minimum(np.floor(uv.max(0)).astype(int),resolution-1)
    if np.any(hi<lo):continue
    yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];q=np.stack([xx,yy],axis=-1)-uv[0]
    mat=np.column_stack([uv[1]-uv[0],uv[2]-uv[0]])
    if abs(np.linalg.det(mat))<1e-10:continue
    b=q@np.linalg.inv(mat).T;b=np.concatenate([1-b.sum(-1,keepdims=True),b],axis=-1);inside=np.all(b>=-1e-6,axis=-1)
    target=owner[lo[1]:hi[1]+1,lo[0]:hi[0]+1];target[inside]=i
    points[lo[1]:hi[1]+1,lo[0]:hi[0]+1][inside]=b[inside]@xyz[vs]
yy,xx=np.nonzero(owner>=0);sourceIds=np.empty(len(xx),dtype=np.int32);bary=np.empty((len(xx),3));uvs=np.empty((len(xx),2));distance=np.empty(len(xx))
start=time.monotonic()
for k,(y,x) in enumerate(zip(yy,xx)):
    q,n,t,d=tree.find_nearest(Vector(points[y,x]));p=registered[tri[t]]
    pair=np.linalg.lstsq(np.column_stack([p[1]-p[0],p[2]-p[0]]),np.array(q)-p[0],rcond=None)[0]
    b=np.clip([1-sum(pair),pair[0],pair[1]],0,1);b/=sum(b)
    sourceIds[k]=t;bary[k]=b;uvs[k]=b@sourceUV[loop[t]];distance[k]=d
    if k%100000==0:print('DIRECT_TRANSFER_QUERY',k,len(xx),round(time.monotonic()-start,1),flush=True)

def image_pixels(img):
    p=np.empty(len(img.pixels),dtype=np.float32);img.pixels.foreach_get(p);return p.reshape(img.size[1],img.size[0],4)
def linear(c):return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def encoded(c):return np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
def sample(p,uv,srgb=False):
    h,w=p.shape[:2];q=(uv%1)*[w,h]-.5;i=np.floor(q).astype(int);a=q-i
    values=[p[(i[:,1]+dy)%h,(i[:,0]+dx)%w,:3] for dx,dy in [(0,0),(1,0),(0,1),(1,1)]]
    if srgb:values=[linear(v) for v in values]
    v=(values[0]*(1-a[:,0,None])+values[1]*a[:,0,None])*(1-a[:,1,None])+(values[2]*(1-a[:,0,None])+values[3]*a[:,0,None])*a[:,1,None]
    return encoded(v) if srgb else v
def png(path,p):
    rgb=np.rint(np.clip(p[::-1],0,1)*255).astype(np.uint8)
    def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
    raw=b''.join(b'\x00'+row.tobytes() for row in rgb)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',resolution,resolution,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b''))
mat=high.data.materials[0];textures=[n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
base=next(n for n in textures if n.image.colorspace_settings.name=='sRGB')
orm=next(n for n in textures if n.image.colorspace_settings.name=='Non-Color')
sampleBase=sample(image_pixels(base.image),uvs,True);sampleORM=sample(image_pixels(orm.image),uvs)
outputs={};arrays={}
for label,node,values in [('base-color',base,sampleBase),('orm',orm,sampleORM)]:
    p=np.zeros((resolution,resolution,3),dtype=np.float32);p[yy,xx]=values;mask=owner>=0
    # Twelve texels of deterministic neighboring color padding; never fill a
    # missing interior with invented colors. All occupied texels were queried.
    for iteration in range(12):
        total=np.zeros_like(p);count=np.zeros_like(owner)
        for dy,dx in [(1,0),(-1,0),(0,1),(0,-1)]:
            shifted=np.roll(mask,(dy,dx),(0,1));shiftp=np.roll(p,(dy,dx),(0,1))
            if dy==1:shifted[0]=False
            if dy==-1:shifted[-1]=False
            if dx==1:shifted[:,0]=False
            if dx==-1:shifted[:,-1]=False
            total+=shiftp*shifted[:,:,None];count+=shifted
        fill=(~mask)&(count>0);p[fill]=total[fill]/count[fill,None];mask|=fill
    path=out/(label+'.png');png(path,p);arrays[label]=p
    outputs[label]={'path':str(path),'SHA256':sha(path),'occupiedPixels':len(xx),'sourceImage':node.image.name,'colorSpace':node.image.colorspace_settings.name}
oldMat=old.data.materials[0];oldBase=next(n.image for n in oldMat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'base-color' in n.image.name)
oldRough=next(n.image for n in oldMat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'roughness' in n.image.name)
baked=image_pixels(oldBase)[yy,xx,:3];rough=image_pixels(oldRough)[yy,xx,0]
miss=np.all(baked<1/255,axis=1)&(rough<1/255)
error=np.linalg.norm(linear(baked)-linear(sampleBase),axis=1)
new=old.copy();new.data=old.data.copy();bpy.context.collection.objects.link(new);new.name='Selected donor direct-UV transfer on unchanged source13, unaccepted'
newMat=mat.copy();newMat.name='Exact selected donor channels, direct source13 atlas';new.data.materials.clear();new.data.materials.append(newMat)
for node in newMat.node_tree.nodes:
    if node.type=='TEX_IMAGE' and node.image:
        label='base-color' if node.image.colorspace_settings.name=='sRGB' else 'orm'
        node.image=bpy.data.images.load(str(out/(label+'.png')),check_existing=False);node.image.colorspace_settings.name=outputs[label]['colorSpace']
old.hide_render=True;old.hide_set(True);new.hide_render=False;new.hide_set(False)
assert np.array_equal(xyz,np.array([v.co[:] for v in new.data.vertices]))
new['accepted']=False;new['constructionStage']='Direct actual donor surface UV transfer, unchanged frozen source13 geometry; root played review pending'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'direct-transfer.blend'),compress=True)
np.savez_compressed(out/'direct-transfer.npz',atlasPixelXY=np.column_stack([xx,yy]),sourceTriangle=sourceIds,sourceBarycentric=bary,sourceUV=uvs,sourceDistanceM=distance,oldBakeMiss=miss)
report={'status':'UNACCEPTED actual donor transfer repair on unchanged geometry','pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'direct-transfer.blend'),'correspondenceSHA256':sha(out/'direct-transfer.npz'),
        'registrationMaxErrorM':registration_error,'textures':outputs,'occupiedAtlasTexels':len(xx),'oldBakeBlackBaseAndZeroRoughnessCount':int(miss.sum()),'oldBakeMissFraction':float(miss.mean()),
        'linearBaseColorL2Percentiles':np.percentile(error,[0,50,95,100]).tolist(),'sourceDistanceMPercentiles':np.percentile(distance,[0,50,95,100]).tolist(),'nativeGeometryMaximumChangeM':0,
        'method':'Exact source triangle/UV sampled per occupied unchanged-atlas texel from nearest registered donor point; original channels/colorspaces/Principled graph, linear-light base interpolation then explicit sRGB PNG encoding; no selected-to-active rays or source seam interpolation',
        'limits':['Nearest source point can select a folded or interior donor surface; matched played comparison is required, not numerical art acceptance.','Original source13 fitted silhouette is unchanged and remains root-rejected; material repair alone does not restore hood/cuff/hem shape.','No skin, collision, broad motion, new inference or normal-player promotion. Body/head/51bind/source13/source14 remain frozen; allM0-M5 open.']}
assert pins=={p:sha(p) for p in pins}
(evidence/'transfer.json').write_text(json.dumps(report,indent=2)+'\n');print('DIRECT_TRANSFER_READY',len(xx),'oldMiss',int(miss.sum()),'seconds',round(time.monotonic()-start,1),flush=True)
