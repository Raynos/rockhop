"""Actual local garment separation on a reviewed curved source hem.

L0 preserves every old outer position, UV, normal and weight. L1 additionally
assigns material ownership: hoodie excludes leg bones; pants waist attaches
to pelvis with an intrinsic seam-distance transition. Hidden rim/waist lining
is construction only, not a saddle support or anatomical-volume certificate.
"""
from pathlib import Path
import sys, json, hashlib, io
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.ndimage import uniform_filter
from PIL import Image

ROOT = Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
sys.path.insert(0, str(ROOT/'scripts'))
from glb import GLB
G = GLB(ROOT/'deliverables/C19.glb')
PR = [p for m in G.j['meshes'] for p in m['primitives']]
bind = np.load(ROOT/'experiments/C19-bind.npz')
seam_path = ROOT/'hoodie-repair03/lower-foundation/seam-proposals/texture-clues.npz'
seam = np.load(seam_path)
cycle, alias, shirt = seam['cycle'], seam['aliases'], seam['shirtFaces']
P = [G.array(p['attributes']['POSITION']).astype(float) for p in PR]
T = [G.array(p['indices']).reshape(-1,3).astype(int) for p in PR]
UV = [G.array(p['attributes']['TEXCOORD_0']).astype(float) for p in PR]
N = [G.array(p['attributes']['NORMAL']).astype(float) for p in PR]
W = [bind[f'W{i}'].copy() for i in range(5)]
_, global_alias = np.unique(np.concatenate(P), axis=0, return_inverse=True)
offset = np.r_[0,np.cumsum([len(p)for p in P])]
weld = [global_alias[offset[i]:offset[i+1]].copy()for i in range(5)]
garment = [np.zeros(len(p),int)for p in P]
garment[1][:] = 4; garment[2][:] = 1; garment[3][:] = garment[4][:] = 3
tf0 = shirt[:len(T[0])]
shirt_vertices = np.unique(T[0][tf0]); pant_vertices = np.unique(T[0][~tf0])
shared = np.intersect1d(shirt_vertices,pant_vertices)
assert len(shared)==33
shirt_only = np.setdiff1d(shirt_vertices,pant_vertices)
garment[0][shirt_only] = 1; garment[0][pant_vertices] = 2
positions = [p.tolist()for p in P]; weights = [w.tolist()for w in W]
uvs = [u.tolist()for u in UV]; normals = [n.tolist()for n in N]
old_vertex = [list(range(len(p)))for p in P]
welds = [w.tolist()for w in weld]; garments = [g.tolist()for g in garment]
regions = [['original']*len(p)for p in P]
next_weld = int(global_alias.max()+1)
shirt_weld = {int(u):next_weld+i for i,u in enumerate(cycle)}
next_weld += len(cycle)
raw_seam = np.flatnonzero(np.isin(alias[:len(P[0])],cycle))
assert len(raw_seam)==134
for v in np.intersect1d(raw_seam,shirt_only):
    welds[0][v] = shirt_weld[int(alias[v])]

def append(point, weight, tex, normal, old, physical, material, region):
    index = len(positions[0]); positions[0].append(np.asarray(point).tolist())
    weights[0].append(np.asarray(weight).tolist()); uvs[0].append(np.asarray(tex).tolist())
    normals[0].append(np.asarray(normal).tolist()); old_vertex[0].append(int(old))
    welds[0].append(int(physical)); garments[0].append(int(material)); regions[0].append(region)
    return index

duplicates = {}
for old in shared:
    u = int(alias[old])
    duplicates[int(old)] = append(P[0][old],W[0][old],UV[0][old],N[0][old],old,shirt_weld[u],1,'separated-shirt-seam')
for f in np.flatnonzero(tf0):
    T[0][f] = [duplicates.get(int(v),int(v))for v in T[0][f]]
shirt_ring = []; pant_ring = []
for u in cycle:
    candidates = np.flatnonzero(alias[:len(P[0])]==u)
    sv = next(int(v)for v in candidates if v in shirt_vertices)
    pv = next(int(v)for v in candidates if v in pant_vertices)
    shirt_ring.append(duplicates.get(sv,sv)); pant_ring.append(pv)

# New UV islands use existing opaque gold and denim atlas rectangles. No image
# changes and no source-row UV changes. New patch outer rows are UV duplicates.
mat = G.j['materials'][PR[0]['material']]
image = G.j['images'][G.j['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
bv = G.j['bufferViews'][image['bufferView']]
raw = bytes(G.bin[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']])
im = np.asarray(Image.open(io.BytesIO(raw)).convert('RGBA')).astype(float)
rgb = im[:,:,:3]; opaque = im[:,:,3]==255
gold = (rgb[:,:,0]>rgb[:,:,1]+15)&(rgb[:,:,1]>rgb[:,:,2]+12)&(rgb[:,:,0]>75)&opaque
blue = (rgb[:,:,2]>rgb[:,:,0]*1.12)&(rgb[:,:,2]>rgb[:,:,1]*1.02)&(rgb[:,:,0]<140)&opaque
donors = {}
for name, mask in [('gold',gold),('denim',blue)]:
    score = uniform_filter(mask.astype(float),size=17,mode='constant')
    yy,xx = np.where(score>.99999)
    assert len(xx), f'No verified opaque source {name} rectangle'
    k = len(xx)//2; donors[name] = np.array([xx[k]/im.shape[1],yy[k]/im.shape[0]])
centre = seam['sourcePoints'][cycle].mean(0)
def patch_uv(point,kind):
    return donors[kind]+(np.asarray(point)[[0,2]]-centre[[0,2]])*.016/.5

new_faces = []; face_regions = []
# The source hoodie is a zero-thickness open garment. Keep the actual cut
# hem open instead of adding a tiny inward strip that pierced the waist lining.
# This preserves all outer source rows and makes no thickness/body claim.
outer_p = []; inner_p = []
for ring_index,row in enumerate(pant_ring):
    point=np.array(positions[0][row]); inner=point.copy()
    inner[[0,2]]=centre[[0,2]]+(point[[0,2]]-centre[[0,2]])*.90
    inner[1]-=.006
    angle=2*np.pi*ring_index/len(cycle);direction=np.array([np.cos(angle),np.sin(angle)])
    outer_p.append(append(point,weights[0][row],donors['denim']+.006*direction,normals[0][row],row,welds[0][row],2,'waist-UV-seam'))
    inner_p.append(append(inner,weights[0][row],donors['denim']+.004*direction,[0,1,0],-1,next_weld,2,'inward-waist-lining')); next_weld+=1
cap_point=centre.copy();cap_point[1]-=.010
pelvis=np.zeros(19);pelvis[0]=1
cap=append(cap_point,pelvis,donors['denim'],[0,1,0],-1,next_weld,2,'hidden-waist-cap');next_weld+=1
for k in range(len(cycle)):
    j=(k+1)%len(cycle)
    new_faces.extend([[outer_p[j],inner_p[k],outer_p[k]],[outer_p[j],inner_p[j],inner_p[k]],[inner_p[j],cap,inner_p[k]]])
    face_regions.extend(['pants-waist-lining']*2+['hidden-waist-cap'])
T[0]=np.concatenate([T[0],np.array(new_faces,int)])
positions=[np.array(p)for p in positions];weights=[np.array(w)for w in weights]
uvs=[np.array(u)for u in uvs];normals=[np.array(n)for n in normals]
# Normals on newly authored rows only; existing source normal rows stay exact.
face_p=positions[0][T[0]];face_n=np.cross(face_p[:,1]-face_p[:,0],face_p[:,2]-face_p[:,0]);ns=np.zeros_like(positions[0])
for k in range(3):np.add.at(ns,T[0][:,k],face_n)
ns/=np.maximum(np.linalg.norm(ns,axis=1,keepdims=True),1e-15)
normals[0][len(P[0]):]=ns[len(P[0]):]
for old,new in duplicates.items():normals[0][new]=N[0][old]
new_edge_parents=np.repeat(np.arange(len(cycle)),3)
new_ring_rows=np.tile([0,1,2],len(cycle))

out=ROOT/'hoodie-repair03/lower-foundation/construction02';out.mkdir(parents=True,exist_ok=True)
for label in ['L0-separation','L1-material-ownership']:
    w=[a.copy()for a in weights]
    if label.startswith('L1'):
        role=np.array(garments[0]);sel=role==1;w[0][sel,13:]=0
        total=w[0][sel].sum(1);assert (total>0).all();w[0][sel]/=total[:,None]
        # Intrinsic pants distance from the actual reviewed seam, not height.
        pf=T[0][np.all(role[T[0]]==2,axis=1)]
        edges=np.unique(np.sort(np.concatenate([pf[:,[0,1]],pf[:,[1,2]],pf[:,[0,2]]]),axis=1),axis=0)
        el=np.linalg.norm(positions[0][edges[:,0]]-positions[0][edges[:,1]],axis=1)
        graph=coo_matrix((np.r_[el,el],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(role),len(role))).tocsr()
        distance=dijkstra(graph,directed=False,indices=pant_ring,min_only=True)
        beta=np.clip(1-distance/.12,0,1);beta=beta*beta*(3-2*beta);beta[role!=2]=0
        w[0]*=(1-beta[:,None]);w[0][:,0]+=beta
        # Reconcile the field on the authoritative physical garment welds,
        # including UV duplicates. Average within a group before sparsity;
        # original group support agrees, so this introduces no new joints.
        allw=np.concatenate(w);allids=np.concatenate([np.array(x)for x in welds]);off=np.r_[0,np.cumsum([len(x)for x in w])]
        for u in np.unique(allids):
            rows=np.flatnonzero(allids==u)
            if len(rows)>1 and not np.array_equal(allw[rows],np.repeat(allw[rows[:1]],len(rows),axis=0)):
                mean=allw[rows].mean(0);mean/=mean.sum();assert (mean>1e-8).sum()<=4
                allw[rows]=mean
        w=[allw[off[i]:off[i+1]].copy()for i in range(5)]
    payload={}
    for i in range(5):
        payload.update({f'p{i}':positions[i],f'W{i}':w[i],f'tr{i}':T[i],f'uv{i}':uvs[i],f'n{i}':normals[i],f'oldVertex{i}':np.array(old_vertex[i],int),f'physicalWeld{i}':np.array(welds[i],int),f'garmentId{i}':np.array(garments[i],int)})
    payload.update(newFacesPrimitive0=np.arange(len(G.array(PR[0]['indices']))//3,len(T[0])),newFaceKind=np.array(face_regions),newVertexKind0=np.array(regions[0]),sourceFaceParents0=np.r_[np.arange(len(G.array(PR[0]['indices']))//3),np.full(len(new_faces),-1)],newFaceSourceCurveEdge=new_edge_parents,newFaceRingConstructionRow=new_ring_rows,seamSourceWeldCycle=cycle,shirtRing=np.array(shirt_ring),pantRing=np.array(pant_ring),matrices=np.repeat(np.eye(4)[None],19,axis=0))
    path=out/f'{label}.npz';np.savez(path,**payload)
    report={'status':'UNACCEPTED structural garment-separation ablation; rest/pose/contact/render gates pending','sourceSHA256':hashlib.sha256(G.raw).hexdigest(),'reviewedSeamSHA256':hashlib.sha256(seam_path.read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'variant':label,'sourceInstancesOnSeam':134,'sharedRawInstancesCloned':33,'oldOuterPositionsAndUVExact':all(np.array_equal(positions[i][:len(P[i])],P[i])and np.array_equal(uvs[i][:len(UV[i])],UV[i])for i in range(5)),'sourceImagesUnchanged':True,'physicalGroups':'Separate hoodie/pants welds even when source ancestry and rest positions coincide; UV duplicates share their own garment welds. Original other source aliases retained.','construction':'Open zero-thickness source hoodie hem; inward pants lining/cap only. No tiny hoodie rim. New UV rings use ordered arc parameter, not folded XZ projection.', 'newFaces':len(new_faces),'newVertices':len(positions[0])-len(P[0]),'maxInfluences':max(int((a>1e-8).sum(1).max())for a in w),'weightSumsMaxError':max(float(abs(a.sum(1)-1).max())for a in w),'limits':'Hoodie has an open single-surface hem, without a thickness claim. Waist cap is hidden lining, not anatomical mass/pressure or saddle support. Source outer L0 deformation unchanged; L1 ownership field must be evaluated independently. No runtime or whole-character approval.'}
    path.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
