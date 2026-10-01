"""CPU base-colour/mip/provenance audit before any material change."""
from pathlib import Path
import hashlib,io,json,struct
import numpy as np
from PIL import Image
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind22');OUT.mkdir(parents=True,exist_ok=True)
p=ROOT/'rig-adapter01/body-bind20/construction01/rider.glb';raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
assert hashlib.sha256(raw).hexdigest()=='1f5035eeb5de708d70c889af89e574a0b7be10bcdc73beed7d1e4393fb21dd28'
def array(index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];item=np.dtype(dtype).itemsize
 return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*item),item)).copy()
def bitmap_for_material(index):
 m=doc['materials'][index];tex=doc['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']];im=doc['images'][tex['source']];v=doc['bufferViews'][im['bufferView']]
 return np.array(Image.open(io.BytesIO(binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).convert('RGB')).astype(float)/255

def sample(bitmap,uv):
 h,w=bitmap.shape[:2];x=uv[:,0]*w-.5;y=uv[:,1]*h-.5;x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);fx=x-x0;fy=y-y0
 return sum(bitmap[np.clip(y0+dy,0,h-1),np.clip(x0+dx,0,w-1)]*((fx if dx else 1-fx)*(fy if dy else 1-fy))[:,None] for dx in [0,1] for dy in [0,1])
pr=doc['meshes'][1]['primitives'];patch=pr[2];positions=array(patch['attributes']['POSITION']);uv=array(patch['attributes']['TEXCOORD_0']);tri=array(patch['indices']).reshape(-1,3)
atlas=bitmap_for_material(patch['material']);sourceatlas=bitmap_for_material(pr[0]['material'])
area=np.linalg.norm(np.cross(positions[tri[:,1]]-positions[tri[:,0]],positions[tri[:,2]]-positions[tri[:,0]]),axis=1)/2
centroid=positions[tri].mean(1);UV=uv[tri].mean(1);color=sample(atlas,UV);luma=np.sum(color*[.2126,.7152,.0722],axis=1)
assert np.isfinite(color).all() and np.isfinite(luma).all()
selections={'positive_native':np.arange(336),'negative_native':np.arange(764,1100),'positive_front_join':np.arange(336,535),'negative_front_join':np.arange(1100,1301)}
healthy_report=json.loads((OUT.parent/'body-bind20/construction01/skin-normal-preexport.json').read_text())
field=np.array(Image.open(ROOT/'rig-adapter01/body-bind20/construction01/source-skin-conversion.png').convert('RGB')).astype(float)/255
stats={};mip=atlas.copy();mip_reports=[]
for name,ids in selections.items():
 c=color[ids];lum=luma[ids];weight=area[ids];weight/=weight.sum()
 stats[name]={'triangleCentroidMeanRGB':c.mean(0).tolist(),'areaWeightedLuma':float(lum@weight),'lumaPercentiles':np.percentile(lum,[0,10,50,90,100]).tolist(),'fractionLumaBelow025':float((lum<.25).mean()),'unlitColourOnly':True}
for level in range(7):
 values=sample(mip,UV);lum=np.sum(values*[.2126,.7152,.0722],axis=1)
 mip_reports.append({'level':level,'dimensions':[mip.shape[1],mip.shape[0]],'regions':{name:{'meanLuma':float(lum[ids].mean()),'meanLumaDeltaVsMip0':float((lum[ids]-luma[ids]).mean()),'maxAbsoluteLumaDeltaVsMip0':float(abs(lum[ids]-luma[ids]).max())} for name,ids in selections.items()}})
 mip=np.array(Image.fromarray((mip*255+.5).astype(np.uint8)).resize((mip.shape[1]//2,mip.shape[0]//2),Image.Resampling.BOX)).astype(float)/255
# Healthy sample provenance reconstructed from the exact source sheet selection.
selection=np.load(ROOT/'rig-adapter01/body-bind20/sheet-preflight01/sheet-selection.npz');headpos=array(pr[0]['attributes']['POSITION']);headuv=array(pr[0]['attributes']['TEXCOORD_0']);outer_vertices=np.unique(selection['sourceTriangles'][selection['exteriorSourceFaces']])
healthy=[]
for eye,cy,cz in [('positiveZ',1.6965,.032),('negativeZ',1.697,-.0332)]:
 yy=abs(headpos[outer_vertices,1]-cy);zz=abs(headpos[outer_vertices,2]-cz);ids=outer_vertices[((yy>.011)&(yy<.021)&(zz<.027))|((zz>.020)&(zz<.029)&(yy<.018))]
 c=sample(sourceatlas,headuv[ids]);valid=(c[:,0]>.28)&(c[:,0]>c[:,1])&(c[:,1]>c[:,2])&(c.mean(1)>.28);c=c[valid];ids=ids[valid]
 healthy.append({'eye':eye,'sourceSkinSamples':len(ids),'medianRGB':np.median(c,0).tolist(),'lumaPercentiles':np.percentile(np.sum(c*[.2126,.7152,.0722],axis=1),[0,10,50,90,100]).tolist()})
# Texture pigment exists without any shader, eye opacity or material lighting.
field_compare=[]
for name,ids in selections.items():
 eye=0 if name.startswith('positive') else 1;cy,cz=(1.6965,.032) if eye==0 else (1.697,-.0332)
 v=centroid[ids];fuv=np.c_[(eye+(v[:,2]-(cz-.023))/.046)/2,((cy+.019)-v[:,1])/.038];fieldcol=sample(field,fuv)
 field_compare.append({'region':name,'meanRetainedPlanarFieldLuma':float((np.sum(fieldcol*[.2126,.7152,.0722],axis=1)).mean()),'meanActualChartLuma':float(luma[ids].mean()),'meanAbsoluteFieldVsChartRGB':float(abs(fieldcol-color[ids]).mean())})
report={'status':'CPU material diagnosis before correction','sourceCandidateSHA256':hashlib.sha256(raw).hexdigest(),'inspectedPlayedComparisons':['body20/played01/actual-before-after-textured.jpg','body20/played01/actual-before-after-gray.jpg'],
 'actualUnlitSkinChartStatistics':stats,'healthySourceSamples':healthy,'retainedFieldVsActualChart':field_compare,'mipSimulation':mip_reports,
 'graftMaterial':doc['materials'][patch['material']],'sampler':doc['samplers'][doc['textures'][doc['materials'][patch['material']]['pbrMetallicRoughness']['baseColorTexture']['index']]['sampler']],
 'eyeMaterials':doc['materials'][6:8],
 'chartLayout':{'cellPixels':48,'triangleCharts':1525,'atlasPixels':2048,'filledRows':37,'blackUnusedRows':272,'nativeChartRows':{'positive':[0,7],'negative':[18,26]},'gutterToChartCornersPixels':2.5},
 'diagnosis':['Dark pigment is already in actual unlit native-lid albedo and its retained planar interior field; eye shader response is not required to create it.','CPU mip simulation separately measures filter changes; it cannot identify the actual GPU LOD chosen in the played frames.','The source cornea is a neutral3.5percent-alpha standard-PBR film without refraction. Its weak eye appearance remains a distinct lighting/shader hypothesis, not a proved cause of skin pigment.'],
 'limits':['No GPU/render was performed; CPU mip BOX simulation uses sRGB-encoded channel averaging, and is not a WebGL shader capture.','Texture pigment and shader/filter contributions may coexist.','Current20 geometry/material/source remain untouched.']}
(OUT/'material-diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['mipSimulation','graftMaterial','sampler','eyeMaterials']},indent=2))
print(json.dumps(mip_reports,indent=2))
