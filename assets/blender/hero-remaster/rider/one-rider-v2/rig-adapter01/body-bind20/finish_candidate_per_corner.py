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
assert (EVIDENCE/'skin-normal-preexport.json').exists(),'Preserve prior conversion guard receipt'
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
# Reuse the measured planar field only for interior skin. Actual source edge
# UVs are baked independently into triangle charts, preserving source aliases.
field=np.array(Image.open(OUT/'source-skin-conversion.png').convert('RGB')).astype(float)/255
physical,weld=np.unique(positions,axis=0,return_inverse=True)
edge_faces=defaultdict(list)
for fi,t in enumerate(output):
    for j in range(3):edge_faces[tuple(sorted((int(weld[t[j]]),int(weld[t[(j+1)%3]]))))].append((fi,int(t[j]),int(t[(j+1)%3])))
boundary={edge:entries[0] for edge,entries in edge_faces.items() if len(entries)==1}
cell=48;canvas=2048;columns=canvas//cell
assert len(bridge)<=columns*columns
bitmap=np.zeros((canvas,canvas,3),dtype=np.uint8)
patchpos=positions[bridge].reshape(-1,3)
newuv=np.zeros((len(patchpos),2),dtype='<f4')
corner_normals=normal[[lookup[int(i)] for i in bridge.ravel()]].copy()
source_edge_records=[];chart_records=[]
for ti,t in enumerate(bridge):
    ox=(ti%columns)*cell;oy=(ti//columns)*cell
    corners=np.array([[ox+2,oy+2],[ox+45,oy+2],[ox+2,oy+45]],dtype=float)
    newuv[ti*3:ti*3+3]=(corners+.5)/canvas
    gx,gy=np.meshgrid(np.arange(cell),np.arange(cell));u=(gx.ravel()-2)/43;vv=(gy.ravel()-2)/43
    bary=np.c_[1-u-vv,u,vv];bary=np.maximum(bary,0);bary/=bary.sum(1,keepdims=True)
    sample_positions=bary@positions[t]
    eye=0 if sample_positions[:,2].mean()>0 else 1
    cy,cz=(1.6965,.032) if eye==0 else (1.697,-.0332)
    fieldUV=np.c_[(eye+(sample_positions[:,2]-(cz-.023))/.046)/2,((cy+.019)-sample_positions[:,1])/.038]
    colors=sample(field,fieldUV)
    seams=[]
    for j in range(3):
        key=tuple(sorted((int(weld[t[j]]),int(weld[t[(j+1)%3]]))))
        if key in boundary:
            sourceface,a,b=boundary[key]
            source_ids=[a if weld[a]==weld[t[j]] else b,b if weld[b]==weld[t[(j+1)%3]] else a]
            seams.append((j,(j+1)%3,source_ids,sourceface))
    assert len(seams)<=1,'A chart with multiple incompatible inherited source edges needs separate construction'
    if seams:
        a,b,sourceids,sourceface=seams[0]
        amount=bary[:,a]+bary[:,b]
        frac=np.divide(bary[:,b],amount,out=np.zeros_like(amount),where=amount>1e-15)
        directUV=(1-frac[:,None])*expanded['TEXCOORD_0'][sourceids[0]]+frac[:,None]*expanded['TEXCOORD_0'][sourceids[1]]
        originalcolor=sample(pixels,directUV)
        colors=colors*(1-amount[:,None]**2)+originalcolor*amount[:,None]**2
        corner_normals[ti*3+a]=expanded['NORMAL'][sourceids[0]]
        corner_normals[ti*3+b]=expanded['NORMAL'][sourceids[1]]
        source_edge_records.append({'graftTriangle':ti,'sourceTriangle':sourceface,'graftCorners':[a,b],'sourceVertexIDs':sourceids})
    else:
        # Keep single inherited corner values where a native-facing triangle
        # touches a source vertex without containing a source boundary edge.
        for j,i in enumerate(t):
            if int(i) in shared:
                sourceid=min(shared[int(i)],key=lambda q:np.linalg.norm(expanded['TEXCOORD_0'][q]-expanded['TEXCOORD_0'][i]))
                target=sample(pixels,expanded['TEXCOORD_0'][[sourceid]])[0]
                amount=bary[:,j]**2;colors=colors*(1-amount[:,None])+target*amount[:,None]
                corner_normals[ti*3+j]=expanded['NORMAL'][sourceid]
    assert np.isfinite(colors).all()
    bitmap[oy:oy+cell,ox:ox+cell]=(colors.reshape(cell,cell,3).clip(0,1)*255+.5).astype(np.uint8)
    chart_records.append({'triangle':ti,'sourceBoundaryEdges':len(seams),'eye':eye})
# Independent actual edge interpolation check against original source PNG.
errors=[];normal_errors=[]
for edge in source_edge_records:
    ti=edge['graftTriangle'];a,b=edge['graftCorners'];sourceids=edge['sourceVertexIDs'];t=np.linspace(0,1,65)[:,None]
    uv=(1-t)*newuv[ti*3+a]+t*newuv[ti*3+b]
    originalUV=(1-t)*expanded['TEXCOORD_0'][sourceids[0]]+t*expanded['TEXCOORD_0'][sourceids[1]]
    error=abs(sample(bitmap.astype(float)/255,uv)-sample(pixels,originalUV)).max()
    edge['maximumChannelError']=float(error);errors.append(float(error))
    for corner,sourceid in zip([a,b],sourceids):
        normal_errors.append(float(abs(corner_normals[ti*3+corner]-expanded['NORMAL'][sourceid]).max()))
assert len(source_edge_records)==sum(1 for edge in boundary if any(weld[i] in edge for i in used) and all(point in set(weld[used]) for point in edge))
normal=corner_normals.astype('<f4');localtri=np.arange(len(patchpos),dtype='<u4').reshape(-1,3)
uvtri=newuv[localtri];UVarea=np.abs(np.cross(uvtri[:,1]-uvtri[:,0],uvtri[:,2]-uvtri[:,0]))/2
assert np.isfinite(normal).all() and np.max(abs(np.linalg.norm(normal,axis=1)-1))<4*np.finfo(np.float32).eps
assert UVarea.min()>1e-8
report={'status':'PASS per-corner source-edge skin/normal conversion' if max(errors,default=0)<=8/255 and max(normal_errors,default=0)==0 else 'REJECTED per-corner conversion before export',
    'sourceSHA256':hashlib.sha256(raw).hexdigest(),'sameFrozenGeometry':True,'geometryChanged':False,
    'normalMethod':'Area-weighted interiors; each actual source boundary edge inherits exact original corner normals, preserving original hard splits',
    'sourceBoundaryEdgesMatched':len(source_edge_records),'sourceEdgeSamplesPerEdge':65,
    'maximumSourceEdgeChannelError':max(errors,default=0),'colorTolerance':8/255,
    'maximumSourceEdgeNormalComponentError':max(normal_errors,default=0),'originalPBRFactorsCopied':True,
    'atlasDimensions':[canvas,canvas],'triangleChartCount':len(bridge),'minimumUVTriangleArea':float(UVarea.min()),
    'candidateExported':False,'GPUWorkPerformed':False,'sourceEdges':source_edge_records,
    'limits':['Existing source normal/UV discontinuities remain exact; they are not silently averaged away.','Interior healthy-skin field is reused from the retained first conversion, with direct original source UV sampling on every seam edge.','Numerical texture compatibility is not a rendered appearance grade.']}
(EVIDENCE/'skin-normal-per-corner-preexport.json').write_text(json.dumps(report,indent=2)+'\n')
Image.fromarray(bitmap).save(OUT/'source-skin-per-corner.png')
np.savez_compressed(OUT/'skin-normal-per-corner.npz',positions=patchpos,normals=normal,UV=newuv,triangles=localtri)
print(json.dumps({k:v for k,v in report.items() if k!='sourceEdges'},indent=2),flush=True)
assert report['status'].startswith('PASS'),'Stop incompatible per-corner conversion without export'
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
count=len(patchpos)
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
