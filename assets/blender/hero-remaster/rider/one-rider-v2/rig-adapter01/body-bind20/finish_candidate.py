"""CPU-only compatible source-skin conversion and guarded candidate export.

Reads the single frozen geometry; never rebuilds, recuts or searches geometry.
"""
from pathlib import Path
import copy,hashlib,io,json,struct
from collections import defaultdict
import numpy as np
from scipy.interpolate import RBFInterpolator
from PIL import Image
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
OUT=ROOT/'rig-adapter01/body-bind20/construction01'
EVIDENCE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind20/construction01')
assert not (OUT/'rider.glb').exists(),'Never overwrite frozen exports'
for name in ['source-conservation-preexport.json','surgical-area-preexport.json']:
    assert json.loads((EVIDENCE/name).read_text())['status'].startswith('PASS')
geometry=json.loads((EVIDENCE/'geometry-preexport.json').read_text())
source=ROOT/'rig-adapter01/body-bind11/guarded-correction01/rider.glb';donor=ROOT/'eye-donor01/guarded01/eyes.glb'
def load(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return raw,json.loads(raw[20:20+n]),raw[28+n:]
raw,doc,original=load(source);draw,ddoc,dbin=load(donor)
assert hashlib.sha256(raw).hexdigest()==geometry['sourceSHA256']
assert hashlib.sha256(draw).hexdigest()=='c11e5273b7e8d82a94a46d46c853e0ad42e7caeb2328716bc4a5c4090170d0fb'
def array(document,binary,index):
    a=document['accessors'][index];v=document['bufferViews'][a['bufferView']];lanes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];width=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],lanes),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',lanes*width),width)).copy()
saved=np.load(OUT/'geometry-preexport.npz');positions=saved['positions'];output=saved['sourceTriangles'];bridge=saved['graftTriangles']
p=doc['meshes'][1]['primitives'][0];attrs={key:array(doc,original,index) for key,index in p['attributes'].items()}
expanded={key:saved['attribute_'+key] for key in attrs}
used=np.unique(bridge);patchpos=positions[used];lookup={int(q):i for i,q in enumerate(used)}
sourceactive=np.unique(output);physicalsource=defaultdict(list)
for i in sourceactive:physicalsource[tuple(positions[i])].append(int(i))
shared={int(i):physicalsource[tuple(positions[i])] for i in used if tuple(positions[i]) in physicalsource}
# Geometric interior normals; exact inherited source normals at physical seam.
normal=np.zeros((len(positions),3),dtype=float)
face_norm=np.cross(positions[bridge[:,1]].astype(float)-positions[bridge[:,0]],positions[bridge[:,2]].astype(float)-positions[bridge[:,0]])
for corner in range(3):np.add.at(normal,bridge[:,corner],face_norm)
normal=normal[used];normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-30)
seam_angles=[]
for i,ids in shared.items():
    inherited=expanded['NORMAL'][i].astype(float);inherited/=np.linalg.norm(inherited)
    normal[lookup[i]]=inherited
    alternatives=expanded['NORMAL'][ids].astype(float);alternatives/=np.linalg.norm(alternatives,axis=1,keepdims=True)
    seam_angles.extend(np.degrees(np.arccos(np.clip(alternatives@inherited,-1,1))).tolist())
assert np.isfinite(normal).all() and np.max(abs(np.linalg.norm(normal,axis=1)-1))<1e-12
# Same source PBR factors/specular extension; source images are retained exactly.
material=copy.deepcopy(doc['materials'][p['material']]);texindex=material['pbrMetallicRoughness']['baseColorTexture']['index']
image=doc['images'][doc['textures'][texindex]['source']];view=doc['bufferViews'][image['bufferView']]
pixels=np.array(Image.open(io.BytesIO(original[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])).convert('RGB')).astype(float)/255

def sample(bitmap,uv):
    h,w=bitmap.shape[:2];x=uv[:,0]*w-.5;y=uv[:,1]*h-.5
    x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);fx=x-x0;fy=y-y0
    return sum(bitmap[np.clip(y0+dy,0,h-1),np.clip(x0+dx,0,w-1)]*((fx if dx else 1-fx)*(fy if dy else 1-fy))[:,None] for dx in [0,1] for dy in [0,1])
def linear(x):return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4)
def srgb(x):return np.where(x<=.0031308,12.92*x,1.055*np.maximum(x,0)**(1/2.4)-.055)
selection=np.load(ROOT/'rig-adapter01/body-bind20/sheet-preflight01/sheet-selection.npz')
outer_vertices=np.unique(selection['sourceTriangles'][selection['exteriorSourceFaces']])
bitmap=np.zeros((1024,2048,3),dtype=np.uint8);newuv=np.zeros((len(used),2),dtype=float);skin_reports=[]
for ei,(eye,cy,cz) in enumerate([('positiveZ',1.6965,.032),('negativeZ',1.697,-.0332)]):
    mask=abs(patchpos[:,2]-cz)<.024;localids=np.flatnonzero(mask)
    boundary=np.array([i for i in shared if abs(positions[i,2]-cz)<.024],dtype=int)
    boundarycolors=sample(pixels,expanded['TEXCOORD_0'][boundary])
    yy=abs(positions[outer_vertices,1]-cy);zz=abs(positions[outer_vertices,2]-cz)
    healthy=outer_vertices[((yy>.011)&(yy<.021)&(zz<.027))|((zz>.020)&(zz<.029)&(yy<.018))]
    colors=sample(pixels,expanded['TEXCOORD_0'][healthy]);skin=(colors[:,0]>.28)&(colors[:,0]>colors[:,1])&(colors[:,1]>colors[:,2])&(colors.mean(1)>.28)
    healthy=healthy[skin];colors=colors[skin];assert len(healthy)>30
    training=np.concatenate([positions[healthy,1:],positions[boundary,1:]])
    values=np.concatenate([linear(colors),linear(boundarycolors)])
    key=np.round(training,7);unique,groups=np.unique(key,axis=0,return_inverse=True)
    sums=np.zeros((len(unique),3));np.add.at(sums,groups,values);values=sums/np.bincount(groups)[:,None]
    interpolation=RBFInterpolator(unique,values,kernel='linear',neighbors=min(32,len(unique)),smoothing=0)
    width=.046;height=.038;zleft=cz-width/2;ytop=cy+height/2
    ygrid=ytop-(np.arange(1024)+.5)/1024*height;zgrid=zleft+(np.arange(1024)+.5)/1024*width
    for row in range(0,1024,32):
        y,z=np.meshgrid(ygrid[row:row+32],zgrid,indexing='ij');field=interpolation(np.c_[y.ravel(),z.ravel()]).reshape(y.shape+(3,))
        bitmap[row:row+32,ei*1024:(ei+1)*1024]=(srgb(field).clip(0,1)*255+.5).astype(np.uint8)
    newuv[localids,0]=(ei+(patchpos[localids,2]-zleft)/width)/2
    newuv[localids,1]=(ytop-patchpos[localids,1])/height
    buv=np.c_[(ei+(positions[boundary,2]-zleft)/width)/2,(ytop-positions[boundary,1])/height]
    bakedcolors=sample(bitmap.astype(float)/255,buv)
    errors=abs(bakedcolors-boundarycolors)
    skin_reports.append({'eye':eye,'healthyExteriorSourceSamples':len(healthy),'boundaryColorConstraints':len(boundary),
        'maximumBoundaryChannelError':float(errors.max()),'meanBoundaryChannelError':float(errors.mean()),
        'boundaryTolerance':8/255,'oldPaintedIrisExcludedFromHealthySamples':True})
assert np.isfinite(newuv).all() and ((newuv>=0)&(newuv<=1)).all()
report={'status':'PASS compatible source-skin/normal CPU conversion' if all(r['maximumBoundaryChannelError']<=8/255 for r in skin_reports) and max(seam_angles,default=0)<=.25 else 'REJECTED source-skin/normal conversion before export',
    'sourceSHA256':hashlib.sha256(raw).hexdigest(),'sourceSkinImageBytesUnchanged':True,'originalPBRFactorsCopied':True,
    'normalMethod':'Area-weighted actual joined geometry interiors; inherited source boundary normals',
    'maximumPhysicalSourceSeamNormalAngleDegrees':max(seam_angles,default=0),'normalToleranceDegrees':.25,
    'skinConversion':skin_reports,'newAtlasDimensions':[2048,1024],'candidateExported':False,'GPUWorkPerformed':False,
    'limits':['CPU texel and normal compatibility does not establish parent appearance approval.','Skin converts measured healthy current11 exterior and exact original boundary colors, not historical rider assets.','Planar skin UVs may stretch on hidden inward walls; original source/donor detail and UVs remain exact.']}
(EVIDENCE/'skin-normal-preexport.json').write_text(json.dumps(report,indent=2)+'\n')
Image.fromarray(bitmap).save(OUT/'source-skin-conversion.png')
np.savez_compressed(OUT/'skin-normal-preexport.npz',positions=patchpos,normals=normal.astype('<f4'),UV=newuv.astype('<f4'))
print(json.dumps(report,indent=2),flush=True)
assert report['status'].startswith('PASS'),'Stop incompatible skin/normal conversion without export'
# Only now export a private, unaccepted CPU candidate with exact original prefix.
encoded_image=io.BytesIO();Image.fromarray(bitmap).save(encoded_image,format='PNG')
binary=bytearray(original);result=copy.deepcopy(doc)
def append(data,target=None):
    binary.extend(b'\0'*((-len(binary))%4));offset=len(binary);binary.extend(data);entry={'buffer':0,'byteOffset':offset,'byteLength':len(data)}
    if target:entry['target']=target
    result['bufferViews'].append(entry);return len(result['bufferViews'])-1
def put(a,kind,ctype,target=34962):
    a=np.ascontiguousarray(a);entry={'bufferView':append(a.tobytes(),target),'componentType':ctype,'count':len(a),'type':kind}
    if kind=='VEC3':entry.update(min=a.min(0).tolist(),max=a.max(0).tolist())
    result['accessors'].append(entry);return len(result['accessors'])-1
head=result['meshes'][1]['primitives'][0]
for key,old in attrs.items():
    value=expanded[key];assert np.array_equal(value[:len(old)],old)
    spec=doc['accessors'][p['attributes'][key]];head['attributes'][key]=put(value,spec['type'],spec['componentType'])
head['indices']=put(output.astype('<u4').ravel(),'SCALAR',5125,34963)
result['images'].append({'name':'Current11 measured orbital skin conversion','bufferView':append(encoded_image.getvalue()),'mimeType':'image/png'})
result['textures'].append({'source':len(result['images'])-1,'sampler':doc['textures'][texindex].get('sampler',0)})
material['name']='Current11 skin on actual CC0 native anatomical lids';material['pbrMetallicRoughness']['baseColorTexture']={'index':len(result['textures'])-1}
result['materials'].append(material)
localtri=np.array([[lookup[int(q)] for q in t] for t in bridge],dtype='<u4');count=len(used)
head['attributes']['POSITION']=head['attributes']['POSITION']
result['meshes'][1]['primitives'].append({'attributes':{'POSITION':put(patchpos,'VEC3',5126),'NORMAL':put(normal.astype('<f4'),'VEC3',5126),
    'TEXCOORD_0':put(newuv.astype('<f4'),'VEC2',5126),'JOINTS_0':put(np.tile(np.array([4,0,0,0],dtype='<u2'),(count,1)),'VEC4',5123),
    'WEIGHTS_0':put(np.tile(np.array([1,0,0,0],dtype='<f4'),(count,1)),'VEC4',5126)},'indices':put(localtri.ravel(),'SCALAR',5125,34963),'material':len(result['materials'])-1,'mode':4})
imageoffset=len(result['images']);texoffset=len(result['textures']);sampoffset=len(result['samplers']);matoffset=len(result['materials'])
for im in ddoc['images']:
    im=copy.deepcopy(im);view=ddoc['bufferViews'][im['bufferView']];im['bufferView']=append(dbin[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]);result['images'].append(im)
result['samplers'].extend(copy.deepcopy(ddoc['samplers']))
for tex in ddoc['textures']:
    tex=copy.deepcopy(tex);tex['source']+=imageoffset;tex['sampler']+=sampoffset;result['textures'].append(tex)
for m in ddoc['materials']:
    m=copy.deepcopy(m)
    if 'baseColorTexture' in m['pbrMetallicRoughness']:m['pbrMetallicRoughness']['baseColorTexture']['index']+=texoffset
    result['materials'].append(m)
fits={g['eye']:g['selectedActualSurfaceCheck']['depthShiftM'] for g in geometry['nativeGrafts'] if 'selectedActualSurfaceCheck' in g}
for mesh in ddoc['meshes']:
    donorprim=mesh['primitives'][0];name=mesh['name'];eye='positiveZ' if name.startswith('L') else 'negativeZ'
    cy,cz,apex=(1.6965,.032,.7469700990846553) if eye=='positiveZ' else (1.697,-.0332,.747949309)
    values={key:array(ddoc,dbin,index) for key,index in donorprim['attributes'].items()}
    offset=np.array([apex-.0152355616+fits[eye],cy,cz-(.033 if eye=='positiveZ' else -.033)])
    values['POSITION']=(values['POSITION']+offset).astype('<f4');count=len(values['POSITION'])
    values['JOINTS_0']=np.tile(np.array([4,0,0,0],dtype='<u2'),(count,1));values['WEIGHTS_0']=np.tile(np.array([1,0,0,0],dtype='<f4'),(count,1))
    primitive=copy.deepcopy(donorprim);primitive['attributes']={key:put(value,'VEC'+str(value.shape[1]),5123 if key=='JOINTS_0' else 5126) for key,value in values.items()}
    primitive['indices']=put(array(ddoc,dbin,donorprim['indices']).ravel(),'SCALAR',ddoc['accessors'][donorprim['indices']]['componentType'],34963)
    primitive['material']+=matoffset;result['meshes'][1]['primitives'].append(primitive)
assert bytes(binary[:len(original)])==original
for key in ['nodes','skins','animations','scenes','scene']:assert result[key]==doc[key]
assert result['meshes'][0]==doc['meshes'][0] and result['meshes'][1]['primitives'][1]==doc['meshes'][1]['primitives'][1]
assert len(result['skins'][0]['joints'])==19
result['buffers'][0]['byteLength']=len(binary);encoded=json.dumps(result,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);binary+=b'\0'*((-len(binary))%4)
glb=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(binary))+struct.pack('<I4s',len(encoded),b'JSON')+encoded+struct.pack('<I4s',len(binary),b'BIN\0')+binary
(OUT/'rider.glb').write_bytes(glb)
export={'status':'UNACCEPTED private native anatomical graft candidate; parent moving appearance review required','output':str(OUT/'rider.glb'),
    'SHA256':hashlib.sha256(glb).hexdigest(),'sourceSHA256':hashlib.sha256(raw).hexdigest(),'current11Unchanged':source.read_bytes()==raw,
    'actualDonorUnchanged':donor.read_bytes()==draw,'originalBinaryPrefixExactBytes':len(original),'bodyCheek19RigAnimationsExact':True,
    'fitDepthShiftsM':fits,'candidateExported':True,'GPUWorkPerformed':False,
    'limits':['No Blender/game rendering, face quality grade or game-ready claim.','Parent must verify exported accessors/float32 contact clearance and inspect played motion before acceptance.']}
(EVIDENCE/'candidate-export.json').write_text(json.dumps(export,indent=2)+'\n')
print(json.dumps(export,indent=2))
