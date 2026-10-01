"""Independent actual GLB/source/ocular clearance and seam attribute checks."""
from pathlib import Path
import hashlib,io,json,struct
import numpy as np
from PIL import Image
from geometry_checks import surface_clearance,topology,self_test
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
EVIDENCE=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind20/construction01')
source=ROOT/'rig-adapter01/body-bind11/guarded-correction01/rider.glb';candidate=ROOT/'rig-adapter01/body-bind20/construction01/rider.glb';donor=ROOT/'eye-donor01/guarded01/eyes.glb'
def read(path):
    raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return raw,json.loads(raw[20:20+n]),raw[28+n:]
def array(doc,binary,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];item=np.dtype(dtype).itemsize
    return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*item),item)).copy()
a,old,oldb=read(source);b,new,newb=read(candidate);d,eyes,eb=read(donor)
assert hashlib.sha256(b).hexdigest()=='1f5035eeb5de708d70c889af89e574a0b7be10bcdc73beed7d1e4393fb21dd28'
assert newb[:len(oldb)]==oldb
for key in ['nodes','skins','animations','scenes','scene']:assert new[key]==old[key]
for key in ['accessors','bufferViews','images','textures','samplers','materials']:assert new[key][:len(old[key])]==old[key]
assert new['meshes'][0]==old['meshes'][0] and new['meshes'][1]['primitives'][1]==old['meshes'][1]['primitives'][1]
assert len(new['skins'][0]['joints'])==19
original=old['meshes'][1]['primitives'][0];newhead=new['meshes'][1]['primitives'][0]
for key,index in original['attributes'].items():
    before=array(old,oldb,index);after=array(new,newb,newhead['attributes'][key]);assert np.array_equal(before,after[:len(before)])
geometry=np.load(ROOT/'rig-adapter01/body-bind20/construction01/geometry-preexport.npz')
headpos=array(new,newb,newhead['attributes']['POSITION']);headtri=array(new,newb,newhead['indices']).reshape(-1,3)
assert np.array_equal(headpos,geometry['positions']) and np.array_equal(headtri,geometry['sourceTriangles'])
patch=new['meshes'][1]['primitives'][2];pp=array(new,newb,patch['attributes']['POSITION']);pt=array(new,newb,patch['indices']).reshape(-1,3)
assert np.array_equal(pp[pt],geometry['positions'][geometry['graftTriangles']])
for primitive in new['meshes'][1]['primitives'][2:]:
    joints=array(new,newb,primitive['attributes']['JOINTS_0']);weights=array(new,newb,primitive['attributes']['WEIGHTS_0'])
    assert np.array_equal(joints,np.tile([4,0,0,0],(len(joints),1)))
    assert np.array_equal(weights,np.tile([1,0,0,0],(len(weights),1)))
joinedpos=np.concatenate([headpos,pp]);joinedtri=np.concatenate([headtri,pt+len(headpos)])
joined=topology(joinedpos,joinedtri);assert joined['boundaryEdges']==151 and joined['nonManifoldEdges']==0
norm=array(new,newb,patch['attributes']['NORMAL']);uv=array(new,newb,patch['attributes']['TEXCOORD_0'])
assert np.isfinite(pp).all() and np.isfinite(norm).all() and np.isfinite(uv).all()
assert np.max(abs(np.linalg.norm(norm,axis=1)-1))<4*np.finfo(np.float32).eps
u=uv[pt[:,1]]-uv[pt[:,0]];v=uv[pt[:,2]]-uv[pt[:,0]];UVarea=abs(u[:,0]*v[:,1]-u[:,1]*v[:,0])/2
assert UVarea.min()>1e-8
material=new['materials'][patch['material']];oldmaterial=old['materials'][original['material']]
for key in ['metallicFactor','roughnessFactor']:assert material['pbrMetallicRoughness'][key]==oldmaterial['pbrMetallicRoughness'][key]
assert material['extensions']==oldmaterial['extensions']
tex=new['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']];image=new['images'][tex['source']];view=new['bufferViews'][image['bufferView']]
png=newb[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];pixels=np.array(Image.open(io.BytesIO(png)).convert('RGB')).astype(float)/255
assert png==(ROOT/'rig-adapter01/body-bind20/construction01/source-skin-per-corner.png').read_bytes()
tex=old['textures'][oldmaterial['pbrMetallicRoughness']['baseColorTexture']['index']];image=old['images'][tex['source']];view=old['bufferViews'][image['bufferView']]
oldpixels=np.array(Image.open(io.BytesIO(oldb[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])).convert('RGB')).astype(float)/255
oldUV=array(new,newb,newhead['attributes']['TEXCOORD_0']);oldN=array(new,newb,newhead['attributes']['NORMAL'])
def sample(bitmap,UV):
    h,w=bitmap.shape[:2];x=UV[:,0]*w-.5;y=UV[:,1]*h-.5;x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);fx=x-x0;fy=y-y0
    return sum(bitmap[np.clip(y0+dy,0,h-1),np.clip(x0+dx,0,w-1)]*((fx if dx else 1-fx)*(fy if dy else 1-fy))[:,None] for dx in [0,1] for dy in [0,1])
seam=json.loads((EVIDENCE/'skin-normal-per-corner-preexport.json').read_text());seam_error=0.
for edge in seam['sourceEdges']:
    ti=edge['graftTriangle'];i,j=edge['graftCorners'];sourceids=edge['sourceVertexIDs'];fraction=np.linspace(0,1,65)[:,None]
    targetUV=(1-fraction)*uv[pt[ti,i]]+fraction*uv[pt[ti,j]]
    sourceUV=(1-fraction)*oldUV[sourceids[0]]+fraction*oldUV[sourceids[1]]
    seam_error=max(seam_error,float(abs(sample(pixels,targetUV)-sample(oldpixels,sourceUV)).max()))
    assert np.array_equal(norm[pt[ti,i]],oldN[sourceids[0]]) and np.array_equal(norm[pt[ti,j]],oldN[sourceids[1]])
assert seam_error<=8/255

def hit(points,faces,y,z):
    xyz=points[faces].astype(float);yz=xyz[:,:,1:];a=yz[:,1]-yz[:,0];b=yz[:,2]-yz[:,0];delta=np.array([y,z])-yz[:,0]
    det=a[:,0]*b[:,1]-a[:,1]*b[:,0];ids=np.flatnonzero(abs(det)>1e-15)
    u=(delta[ids,0]*b[ids,1]-delta[ids,1]*b[ids,0])/det[ids];v=(a[ids,0]*delta[ids,1]-a[ids,1]*delta[ids,0])/det[ids]
    bary=np.c_[1-u-v,u,v];valid=(bary>=-1e-8).all(1)
    return float((bary[valid]*xyz[ids[valid],:,0]).sum(1).max()) if valid.any() else None
checks=[];actual=[]
for i,mesh in enumerate(eyes['meshes']):
    primitive=new['meshes'][1]['primitives'][3+i];ep=array(new,newb,primitive['attributes']['POSITION']);ef=array(new,newb,primitive['indices']).reshape(-1,3)
    origin=mesh['primitives'][0];oldpoints=array(eyes,eb,origin['attributes']['POSITION']);oldfaces=array(eyes,eb,origin['indices']).reshape(-1,3)
    assert np.array_equal(ef,oldfaces)
    for key in ['NORMAL','TEXCOORD_0']:assert np.array_equal(array(new,newb,primitive['attributes'][key]),array(eyes,eb,origin['attributes'][key]))
    name=mesh['name'];eye='positiveZ' if name.startswith('L') else 'negativeZ';cy,cz,apex=(1.6965,.032,.7469700990846553) if eye=='positiveZ' else (1.697,-.0332,.747949309)
    offset=np.array([apex-.0152355616-.004,cy,cz-(.033 if eye=='positiveZ' else -.033)])
    assert np.array_equal(ep,(oldpoints+offset).astype('<f4'))
    skin=headpos[headtri].astype(float);mask=(skin.min(1)<=ep.max(0)+.00025).all(1)&(skin.max(1)>=ep.min(0)-.00025).all(1)
    for category,surface in [('native_joined_graft',pp[pt].astype(float)),('all_retained_source_skin',skin[mask])]:
        result=surface_clearance(surface,ep[ef].astype(float),reach=.00025)
        checks.append({'actualSurface':name,'category':category,**result})
        assert result['distanceLowerBoundM']>=.0001,(name,category,result)
    actual.append({'surface':name,'topology':topology(ep,ef),'UVNormalsIndicesExact':True})
    if name.endswith('sclera_iris'):
        for y,z in [(cy,cz),(cy-.002,cz),(cy+.002,cz),(cy,cz-.005),(cy,cz+.005)]:
            iris=hit(ep,ef,y,z);patchhit=hit(pp,pt,y,z);skin=hit(headpos,headtri,y,z)
            assert iris is not None and (patchhit is None or iris>patchhit+.0001) and (skin is None or iris>skin+.0001)
            actual.append({'eye':eye,'rayYZ':[y,z],'irisFrontX':iris,'graftFrontX':patchhit,'skinFrontX':skin,'visible':True})
assert source.read_bytes()==a and candidate.read_bytes()==b and donor.read_bytes()==d
report={'status':'PASS independent actual-export CPU contract, source-edge and actual-eye geometry checks; art unaccepted',
    'candidateSHA256':hashlib.sha256(b).hexdigest(),'sourceSHA256':hashlib.sha256(a).hexdigest(),
    'originalBinaryPrefixExactBytes':len(oldb),'bodyCheek19RigAnimationsExact':True,'sourceHeadOriginalAttributesExact':True,
    'graftFrozenPositionsExact':True,'joinedTopology':joined,'allFinite':True,'minimumUVTriangleArea':float(UVarea.min()),
    'graftAndEyeHeadJoint4WeightsExact':True,'embeddedConvertedPNGExact':True,
    'sourceEdgeNormalValuesExact':True,'sourceEdgesChecked':len(seam['sourceEdges']),'maximumSourceEdgeColorError':seam_error,
    'actualEyeChecks':checks,'actualEyeTopologyAndRays':actual,'geometryAlgorithmSelfTests':self_test(),
    'limits':['No appearance grade or gameplay motion acceptance.','Eye surfaces remain open-backed; exact surface checks do not invent closed volumes.','Original source UV/normal hard splits are preserved at each seam edge.','Both protected-source coverage and declared-aperture area receipts apply to exact exported source positions/indices.']}
(EVIDENCE/'independent-export-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['actualEyeChecks','actualEyeTopologyAndRays']},indent=2))
