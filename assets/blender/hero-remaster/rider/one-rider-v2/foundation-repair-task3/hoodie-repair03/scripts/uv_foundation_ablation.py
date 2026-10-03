from pathlib import Path
import sys,json,hashlib,io,numpy as np
from PIL import Image
from scipy.spatial import cKDTree
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');sys.path.insert(0,str(ROOT/'scripts'));from glb import GLB
OUT=ROOT/'hoodie-repair03/uv-normal-foundation01';OUT.mkdir(parents=True,exist_ok=True)
g=GLB(ROOT/'hoodie-repair02/deliverables/rider-compression-v7.glb');pr=g.j['meshes'][0]['primitives'][0]
def arr(i):
 ac=g.j['accessors'][i];k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[ac['type']];a=g.array(i).copy()if'bufferView'in ac else np.zeros((ac['count'],k),dtype='<f4')
 if'sparse'in ac:
  s=ac['sparse'];bi=g.j['bufferViews'][s['indices']['bufferView']];dt={5125:'<u4',5123:'<u2',5121:'u1'}[s['indices']['componentType']];ix=np.frombuffer(g.bin,dt,count=s['count'],offset=bi.get('byteOffset',0)+s['indices'].get('byteOffset',0));bv=g.j['bufferViews'][s['values']['bufferView']];vals=np.frombuffer(g.bin,'<f4',count=s['count']*k,offset=bv.get('byteOffset',0)+s['values'].get('byteOffset',0)).reshape(-1,k);a[ix]=vals
 return a
p=arr(pr['attributes']['POSITION']);uv=arr(pr['attributes']['TEXCOORD_0']);tri=arr(pr['indices']).reshape(-1,3);mt=g.j['materials'][pr['material']];im=g.j['images'][g.j['textures'][mt['pbrMetallicRoughness']['baseColorTexture']['index']]['source']];bv=g.j['bufferViews'][im['bufferView']];raw=bytes(g.bin[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]);image=np.array(Image.open(io.BytesIO(raw)).convert('RGB'));height,width=image.shape[:2]
bary=np.array([[1/3]*3,[.6,.2,.2],[.2,.6,.2],[.2,.2,.6],[.8,.1,.1],[.1,.8,.1],[.1,.1,.8]])
uvs=np.einsum('sk,fkj->fsj',bary,uv[tri]);xy=np.clip(uvs,0,1)*[width-1,height-1];colors=image[np.round(xy[:,:,1]).astype(int),np.round(xy[:,:,0]).astype(int)].astype(float)
blue=(colors[:,:,2]>colors[:,:,0]*1.12)&(colors[:,:,2]>colors[:,:,1]*1.02)&(colors[:,:,0]<140)
gold=(colors[:,:,0]>colors[:,:,1]+15)&(colors[:,:,1]>colors[:,:,2]+12)&(colors[:,:,0]>75)
# Semantic test deliberately excludes valid waist/denim and head/glove regions.
shirt=(p[tri][:,:,1]>1.08).all(1)&(p[tri][:,:,1]<1.46).all(1);bad=np.flatnonzero(shirt&(blue.mean(1)>.15));good=np.flatnonzero(shirt&(gold.mean(1)>.99));cent=p[tri].mean(1);normal=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]]);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-15);tree=cKDTree(cent[good]);donors=[];rows=[];newuv=[];clones=[];nt=tri.copy()
for f in bad:
 distances,indices=tree.query(cent[f],k=min(128,len(good)));choices=[(float(d),int(good[i]))for d,i in zip(np.atleast_1d(distances),np.atleast_1d(indices))if np.dot(normal[f],normal[good[i]])>.65 and np.sign(cent[f,2])==np.sign(cent[good[i],2])]
 if not choices:continue
 dist,donor=min(choices);duv=uv[tri[donor]].copy();targetsign=np.linalg.det(np.c_[uv[tri[f]][1]-uv[tri[f]][0],uv[tri[f]][2]-uv[tri[f]][0]])
 if np.linalg.det(np.c_[duv[1]-duv[0],duv[2]-duv[0]])*targetsign<0:duv=duv[[0,2,1]]
 start=len(p)+len(clones);nt[f]=np.arange(start,start+3);clones.extend(tri[f]);newuv.extend(duv);rows.append({'face':int(f),'donorFace':donor,'donorSourceDistanceM':dist,'sourceBlueSampleFraction':float(blue[f].mean()),'sourcePoints':p[tri[f]].tolist()})
clones=np.asarray(clones,int);newuv=np.array(newuv)
def add(a,typ,comp,normalized=None):
 dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[comp];a=np.ascontiguousarray(a,dtype=dt);g.bin.extend(b'\0'*((-len(g.bin))%4));bi=len(g.j['bufferViews']);g.j['bufferViews'].append({'buffer':0,'byteOffset':len(g.bin),'byteLength':a.nbytes});g.bin.extend(a.tobytes());ai=len(g.j['accessors']);ac={'bufferView':bi,'componentType':comp,'count':len(a),'type':typ};
 if normalized is not None:ac['normalized']=normalized
 if comp==5126:ac.update(min=a.min(0).reshape(-1).tolist(),max=a.max(0).reshape(-1).tolist())
 g.j['accessors'].append(ac);return ai
for name,ai in list(pr['attributes'].items()):
 a=arr(ai);ac=g.j['accessors'][ai];a=np.concatenate([a,a[clones]]);a[len(p):]=newuv if name=='TEXCOORD_0'else a[len(p):];pr['attributes'][name]=add(a,ac['type'],ac['componentType'],ac.get('normalized'))
pr['indices']=add(nt.reshape(-1,1),'SCALAR',5125)
for target in pr['targets']:
 for semantic,ai in list(target.items()):
  a=arr(ai);target[semantic]=add(np.concatenate([a,a[clones]]),'VEC3',5126)
g.j['buffers'][0]['byteLength']=len(g.bin);g.j['asset']['extras']['uvFoundationAblation']={'sourceSHA256':hashlib.sha256(g.raw).hexdigest(),'sourceImageSHA256':hashlib.sha256(raw).hexdigest(),'imagesUnchanged':True,'geometryAndWeightsUnchangedExceptUVSeamDuplicates':True,'localizedUVFaces':len(rows),'newVertices':len(clones),'productionApproved':False,'limits':'UV-only appearance ablation for wrong dark-blue sampled shirt texels; valid waist/thigh denim retained. Does not repair crossings/collapses or normal inversions. New duplicated vertices preserve all51 morph targets and oldvertex socket indices.'};path=OUT/'rider-uv-ablation.glb';g.write(path)
report={'sourceGLBSHA256':hashlib.sha256(g.raw).hexdigest(),'outputGLBSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':rows,'newVertices':len(clones),'maxDonorRestDistanceM':max(r['donorSourceDistanceM']for r in rows),'imageBytesUnchanged':True,'sourceFace6355Mapped':any(r['face']==6355 for r in rows),'note':'Diagnostic semantic shirt UV transfer; separately qualify UV density/continuity and all poses before integration. Not geometry acceptance.'};(OUT/'uv-ablation-provenance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='rows'},indent=2))
