"""ONE bounded local albedo correction on frozen body20 geometry.

Healthy source-exterior colour interpolation is convex (no RBF overshoot).
Actual seam edges still use direct original source UVs. Geometry, UV, normals,
poses, eyes and all old BIN/accessors remain exact; append one texture/material.
"""
from pathlib import Path
import copy,hashlib,io,json,struct
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OUT=ROOT/'rig-adapter01/body-bind22/skin-field01';OUT.mkdir(parents=True,exist_ok=True)
EVIDENCE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind22')
source=ROOT/'rig-adapter01/body-bind20/construction01/rider.glb';raw=source.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
assert hashlib.sha256(raw).hexdigest()=='1f5035eeb5de708d70c889af89e574a0b7be10bcdc73beed7d1e4393fb21dd28'
assert not (OUT/'rider.glb').exists(),'Frozen candidate must never be overwritten'
assert (EVIDENCE/'material-diagnosis.json').exists(),'Diagnose before correction'
def array(index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];item=np.dtype(dtype).itemsize
 return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*item),item)).copy()
def image_for_material(index):
 material=doc['materials'][index];tex=doc['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']];im=doc['images'][tex['source']];view=doc['bufferViews'][im['bufferView']]
 return np.array(Image.open(io.BytesIO(binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])).convert('RGB')).astype(float)/255

def sample(bitmap,uv):
 h,w=bitmap.shape[:2];x=uv[:,0]*w-.5;y=uv[:,1]*h-.5;x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);fx=x-x0;fy=y-y0
 return sum(bitmap[np.clip(y0+dy,0,h-1),np.clip(x0+dx,0,w-1)]*((fx if dx else 1-fx)*(fy if dy else 1-fy))[:,None] for dx in [0,1] for dy in [0,1])
pr=doc['meshes'][1]['primitives'];head=pr[0];patch=pr[2];positions=array(patch['attributes']['POSITION']);tri=array(patch['indices']).reshape(-1,3);UV=array(patch['attributes']['TEXCOORD_0'])
headpos=array(head['attributes']['POSITION']);headUV=array(head['attributes']['TEXCOORD_0']);originalskin=image_for_material(head['material']);oldatlas=image_for_material(patch['material'])
selection=np.load(ROOT/'rig-adapter01/body-bind20/sheet-preflight01/sheet-selection.npz');outer=np.unique(selection['sourceTriangles'][selection['exteriorSourceFaces']])
models=[];training_reports=[]
for eye,cy,cz in [('positiveZ',1.6965,.032),('negativeZ',1.697,-.0332)]:
 yy=abs(headpos[outer,1]-cy);zz=abs(headpos[outer,2]-cz)
 ids=outer[((yy>.011)&(yy<.021)&(zz<.027))|((zz>.020)&(zz<.029)&(yy<.018))]
 colors=sample(originalskin,headUV[ids]);skin=(colors[:,0]>.28)&(colors[:,0]>colors[:,1])&(colors[:,1]>colors[:,2])&(colors.mean(1)>.28)
 ids=ids[skin];colors=colors[skin];assert len(ids)>30
 xy=headpos[ids,1:];unique,groups=np.unique(np.round(xy,7),axis=0,return_inverse=True);sumcolor=np.zeros((len(unique),3));np.add.at(sumcolor,groups,colors);values=sumcolor/np.bincount(groups)[:,None]
 models.append((cKDTree(unique),values))
 training_reports.append({'eye':eye,'sourceVertices':ids.tolist(),'healthySamples':len(ids),'uniqueYZSamples':len(unique),
     'RGBMinimum':values.min(0).tolist(),'RGBMaximum':values.max(0).tolist(),'medianRGB':np.median(colors,0).tolist(),
     'selection':'Same source-exterior healthy region as prior bake; dark painted eye/brow colours excluded, no original head pixels edited'})
# No black unused texture area: use measured local skin median as mip fallback.
median=np.median(np.concatenate([models[0][1],models[1][1]]),0)
canvas=2048;cell=48;columns=canvas//cell;bitmap=np.tile((median*255+.5).astype(np.uint8),(canvas,canvas,1))
seam=json.loads((EVIDENCE.parent/'body-bind20/construction01/skin-normal-per-corner-preexport.json').read_text())
source_edges={q['graftTriangle']:q for q in seam['sourceEdges']}
# Preserve inherited single-corner source UV aliases like the previous recipe.
physical_head={}
for i in np.unique(array(head['indices']).reshape(-1,3)):
 physical_head.setdefault(tuple(headpos[i]),[]).append(int(i))
for ti,t in enumerate(tri):
 ox=(ti%columns)*cell;oy=(ti//columns)*cell
 gx,gy=np.meshgrid(np.arange(cell),np.arange(cell));u=(gx.ravel()-2)/43;v=(gy.ravel()-2)/43
 bary=np.maximum(np.c_[1-u-v,u,v],0);bary/=bary.sum(1,keepdims=True)
 points=np.einsum('ij,jk->ik',bary,positions[t].astype(float))
 eye=0 if points[:,2].mean()>0 else 1;tree,values=models[eye]
 distances,neighbors=tree.query(points[:,1:],k=min(8,len(values)),workers=1)
 weights=1/np.maximum(distances,.0001)**2;weights/=weights.sum(1,keepdims=True)
 colors=np.sum(values[neighbors]*weights[:,:,None],axis=1)
 assert np.all(colors>=values.min(0)-1e-12) and np.all(colors<=values.max(0)+1e-12),'Convex bounded skin, no overshoot'
 if ti in source_edges:
  edge=source_edges[ti];a,b=edge['graftCorners'];sourceids=edge['sourceVertexIDs'];amount=bary[:,a]+bary[:,b]
  frac=np.divide(bary[:,b],amount,out=np.zeros_like(amount),where=amount>1e-15)
  uv=(1-frac[:,None])*headUV[sourceids[0]]+frac[:,None]*headUV[sourceids[1]]
  direct=sample(originalskin,uv);colors=colors*(1-amount[:,None]**2)+direct*amount[:,None]**2
 else:
  for j,point in enumerate(positions[t]):
   if tuple(point) in physical_head:
    # A single inherited corner does not alter native core (no source vertex
    # exists there). Match a retained source alias at actual boundary points.
    sourceid=physical_head[tuple(point)][0];amount=bary[:,j]**2;direct=sample(originalskin,headUV[[sourceid]])[0]
    colors=colors*(1-amount[:,None])+direct*amount[:,None]
 assert np.isfinite(colors).all()
 bitmap[oy:oy+cell,ox:ox+cell]=(colors.reshape(cell,cell,3).clip(0,1)*255+.5).astype(np.uint8)
# Test original source edges and chart gutter values before export.
edge_errors=[]
for ti,edge in source_edges.items():
 a,b=edge['graftCorners'];ids=edge['sourceVertexIDs'];f=np.linspace(0,1,65)[:,None]
 actualUV=(1-f)*UV[tri[ti,a]]+f*UV[tri[ti,b]];expectedUV=(1-f)*headUV[ids[0]]+f*headUV[ids[1]]
 edge_errors.append(float(abs(sample(bitmap.astype(float)/255,actualUV)-sample(originalskin,expectedUV)).max()))
assert max(edge_errors)<=8/255,'Do not break preserved source seams'
centroidUV=UV[tri].mean(1);centroidcolor=sample(bitmap.astype(float)/255,centroidUV);oldcolor=sample(oldatlas,centroidUV)
region={}
for eye,ids in [('positive_native',np.arange(336)),('negative_native',np.arange(764,1100))]:
 oldl=np.sum(oldcolor[ids]*[.2126,.7152,.0722],1);newl=np.sum(centroidcolor[ids]*[.2126,.7152,.0722],1)
 region[eye]={'oldMeanUnlitLuma':float(oldl.mean()),'newMeanUnlitLuma':float(newl.mean()),'newLumaPercentiles':np.percentile(newl,[0,10,50,90,100]).tolist(),
     'fractionNewBelow025':float((newl<.25).mean()),'originalGeometryUVNormalsUnchanged':True}
Image.fromarray(bitmap).save(OUT/'healthy-source-skin-atlas.png')
report={'status':'UNACCEPTED one local skin-field correction; parent matched render needed','sourceSHA256':hashlib.sha256(raw).hexdigest(),
 'method':'Convex8-neighbour source-exterior colour reconstruction; retain direct original source edge UV colours; measured skin-colour atlas padding',
 'training':training_reports,'regions':region,'sourceSeamEdges':len(edge_errors),'samplesPerSeam':65,'maximumSeamChannelError':max(edge_errors),
 'shaderChanges':False,'eyeMaterialChanges':False,'geometryChanges':False,'paddingChange':'Unused black atlas area replaced by measured source-skin median; every occupied48px chart and gutter regenerated',
 'limits':['Localized albedo intervention only; no rendered face score is claimed.','Actual GPU LOD and eye-film optical response remain parent render questions.','Existing source paint at preserved seam edges remains.']}
(EVIDENCE/'skin-correction.json').write_text(json.dumps(report,indent=2)+'\n')
# Append-only image/material; change exactly the graft primitive material index.
result=copy.deepcopy(doc);newbin=bytearray(binary);newbin.extend(b'\0'*((-len(newbin))%4));offset=len(newbin)
png=io.BytesIO();Image.fromarray(bitmap).save(png,format='PNG');newbin.extend(png.getvalue())
result['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(png.getvalue())})
result['images'].append({'name':'Healthy source skin native-eye field22','bufferView':len(result['bufferViews'])-1,'mimeType':'image/png'})
oldtex=doc['textures'][doc['materials'][patch['material']]['pbrMetallicRoughness']['baseColorTexture']['index']]
result['textures'].append({'source':len(result['images'])-1,'sampler':oldtex.get('sampler',0)})
material=copy.deepcopy(doc['materials'][patch['material']]);material['name']='Native lid source-skin pigment correction22';material['pbrMetallicRoughness']['baseColorTexture']['index']=len(result['textures'])-1
result['materials'].append(material);result['meshes'][1]['primitives'][2]['material']=len(result['materials'])-1
assert result['accessors']==doc['accessors']
for key in ['nodes','skins','animations','scenes','scene','samplers']:assert result[key]==doc[key]
assert bytes(newbin[:len(binary)])==binary
result['buffers'][0]['byteLength']=len(newbin);j=json.dumps(result,separators=(',',':')).encode();j+=b' '*((-len(j))%4);newbin.extend(b'\0'*((-len(newbin))%4))
glb=struct.pack('<4sII',b'glTF',2,28+len(j)+len(newbin))+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(newbin),b'BIN\0')+newbin
(OUT/'rider.glb').write_bytes(glb);report['candidateSHA256']=hashlib.sha256(glb).hexdigest();report['candidate']=str(OUT/'rider.glb');report['originalBinaryPrefixBytes']=len(binary)
(EVIDENCE/'skin-correction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='training'},indent=2))
assert source.read_bytes()==raw
