"""Read-only proof of one append-only material candidate and CPU mip controls."""
from pathlib import Path
import copy,hashlib,io,json,struct
import numpy as np
from PIL import Image
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
EVIDENCE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind22')
source=ROOT/'rig-adapter01/body-bind20/construction01/rider.glb';candidate=ROOT/'rig-adapter01/body-bind22/skin-field01/rider.glb'
def read(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return raw,json.loads(raw[20:20+n]),raw[28+n:]
a,old,ab=read(source);b,new,bb=read(candidate)
assert hashlib.sha256(a).hexdigest()=='1f5035eeb5de708d70c889af89e574a0b7be10bcdc73beed7d1e4393fb21dd28'
assert hashlib.sha256(b).hexdigest()=='cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff'
assert bb[:len(ab)]==ab,'ALL original BIN bytes exact'
assert new['accessors']==old['accessors']
for key in ['images','bufferViews','textures','materials']:assert new[key][:-1]==old[key] and len(new[key])==len(old[key])+1
for key in ['nodes','skins','animations','scenes','scene','samplers']:assert new[key]==old[key]
expected=copy.deepcopy(old['meshes']);expected[1]['primitives'][2]['material']=len(new['materials'])-1
assert new['meshes']==expected,'Exactly one primitive material-index change; no geometry changes'
expected_material=copy.deepcopy(old['materials'][old['meshes'][1]['primitives'][2]['material']]);expected_material['name']='Native lid source-skin pigment correction22';expected_material['pbrMetallicRoughness']['baseColorTexture']['index']=len(new['textures'])-1
assert new['materials'][-1]==expected_material
assert new['textures'][-1]['sampler']==old['textures'][old['materials'][old['meshes'][1]['primitives'][2]['material']]['pbrMetallicRoughness']['baseColorTexture']['index']].get('sampler',0)
assert len(new['skins'][0]['joints'])==19

def array(doc,binary,index):
 v=doc['bufferViews'][doc['accessors'][index]['bufferView']];p=doc['accessors'][index];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[p['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[p['componentType']];size=np.dtype(dtype).itemsize
 return np.ndarray((p['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+p.get('byteOffset',0),strides=(v.get('byteStride',width*size),size)).copy()
def bitmap(doc,binary,primitive):
 m=doc['materials'][primitive['material']];tex=doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']];image=doc['images'][tex['source']];v=doc['bufferViews'][image['bufferView']]
 png=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
 return np.array(Image.open(io.BytesIO(png)).convert('RGB')).astype(float)/255,png

def sample(bitmap,uv):
 h,w=bitmap.shape[:2];x=uv[:,0]*w-.5;y=uv[:,1]*h-.5;x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);fx=x-x0;fy=y-y0
 return sum(bitmap[np.clip(y0+dy,0,h-1),np.clip(x0+dx,0,w-1)]*((fx if dx else 1-fx)*(fy if dy else 1-fy))[:,None] for dx in [0,1] for dy in [0,1])
head=new['meshes'][1]['primitives'][0];patch=new['meshes'][1]['primitives'][2];atlas,png=bitmap(new,bb,patch);originalskin,_=bitmap(new,bb,head);oldatlas,_=bitmap(old,ab,old['meshes'][1]['primitives'][2])
assert png==(ROOT/'rig-adapter01/body-bind22/skin-field01/healthy-source-skin-atlas.png').read_bytes()
UV=array(new,bb,patch['attributes']['TEXCOORD_0']);tri=array(new,bb,patch['indices']).reshape(-1,3);headUV=array(new,bb,head['attributes']['TEXCOORD_0'])
seam=json.loads((EVIDENCE.parent/'body-bind20/construction01/skin-normal-per-corner-preexport.json').read_text());maximum=0.
for edge in seam['sourceEdges']:
 ti=edge['graftTriangle'];i,j=edge['graftCorners'];ids=edge['sourceVertexIDs'];f=np.linspace(0,1,65)[:,None]
 uv=(1-f)*UV[tri[ti,i]]+f*UV[tri[ti,j]];sourceUV=(1-f)*headUV[ids[0]]+f*headUV[ids[1]]
 maximum=max(maximum,float(abs(sample(atlas,uv)-sample(originalskin,sourceUV)).max()))
assert maximum<=8/255
uv=UV[tri].mean(1);regions={'positive_native':np.arange(336),'negative_native':np.arange(764,1100)}
mip_stats=[];older=oldatlas.copy();newer=atlas.copy()
for level in range(7):
 oldcolor=sample(older,uv);newcolor=sample(newer,uv);oldlum=np.sum(oldcolor*[.2126,.7152,.0722],1);newlum=np.sum(newcolor*[.2126,.7152,.0722],1)
 mip_stats.append({'level':level,'dimensions':[newer.shape[1],newer.shape[0]],'regions':{name:{'oldMeanLuma':float(oldlum[ids].mean()),'newMeanLuma':float(newlum[ids].mean()),'newMinLuma':float(newlum[ids].min()),'fractionNewBelow025':float((newlum[ids]<.25).mean())} for name,ids in regions.items()}})
 if level==0:assert all((newlum[ids]>=.28).all() for ids in regions.values())
 for name in ['older','newer']:
  value=older if name=='older' else newer
  reduced=np.array(Image.fromarray((value*255+.5).astype(np.uint8)).resize((value.shape[1]//2,value.shape[0]//2),Image.Resampling.BOX)).astype(float)/255
  if name=='older':older=reduced
  else:newer=reduced
# Gutter has no unfilled black pixels in any occupied chart, and unused padding
# has measured source skin, not transparent/black arbitrary raster values.
black=np.all(atlas==0,axis=2)
assert not black.any()
assert np.isfinite(atlas).all()
assert source.read_bytes()==a and candidate.read_bytes()==b
report={'status':'PASS read-only append-only material/texture and CPU chart controls; appearance unaccepted',
 'sourceSHA256':hashlib.sha256(a).hexdigest(),'candidateSHA256':hashlib.sha256(b).hexdigest(),'originalBinaryPrefixExactBytes':len(ab),
 'accessorListsAndBytesExact':True,'geometryUVNormalsPose19RigAnimationsExact':True,'eyeMaterialsExact':True,'sourceSkinOutsideGraftExact':True,
 'exactDocumentChange':'Append one bufferView/image/texture/material, increase buffer length and change graft primitive material index only',
 'oldMaterialFactorsAndSamplerUnchanged':True,'sourceSeamEdges':len(seam['sourceEdges']),'maximumSeamChannelError':maximum,
 'newAtlasBlackPixels':int(black.sum()),'PNGBytesExact':True,'CPUEncodedSRGBMipControls':mip_stats,
 'limits':['CPU mip means do not establish actual WebGL LOD or sampled lighting.','The material-only change does not improve physical eye optics or guarantee a7/10 face.','Parent must render matched controls before accepting this candidate.']}
(EVIDENCE/'independent-material-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='CPUEncodedSRGBMipControls'},indent=2))
print(json.dumps(mip_stats,indent=2))
