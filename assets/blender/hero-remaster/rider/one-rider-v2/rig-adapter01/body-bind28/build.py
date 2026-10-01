"""One fixed iris-annulus albedo correction; no geometry, optics or source edits."""
from pathlib import Path
import copy,hashlib,io,json,struct
import numpy as np
from PIL import Image
from scipy.ndimage import label
np.seterr(all='raise')
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
SOURCE=ROOT/'body-bind22/skin-field01/rider.glb';RUN=ROOT/'body-bind28/iris-albedo01';OUT=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind28');PROPOSAL=OUT.parent/'body-bind27'
RUN.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def frozen(path,raw):
 if path.exists():assert path.read_bytes()==raw,'Frozen candidate/payload cannot be overwritten'
 else:path.write_bytes(raw)
def decode(rgb):return np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
def encode(rgb):return np.where(rgb<=.0031308,12.92*rgb,1.055*np.maximum(rgb,1e-300)**(1/2.4)-.055)
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
raw=SOURCE.read_bytes();assert sha(raw)=='cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff';n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);original=copy.deepcopy(j);binary=raw[28+n:];assert len(binary)%4==0
proposal=json.loads((PROPOSAL/'eye-appearance-audit.json').read_text());assert proposal['sourceSHA256']==sha(raw)
pr=j['meshes'][1]['primitives'];assert pr[4]['material']==pr[6]['material']==6
material=j['materials'][6];assert material['alphaMode']=='OPAQUE';assert material['pbrMetallicRoughness']['roughnessFactor']==.35;assert material['pbrMetallicRoughness']['metallicFactor']==0;assert material['pbrMetallicRoughness']['baseColorFactor']==[1,1,1,1]
textureIndex=material['pbrMetallicRoughness']['baseColorTexture']['index'];texture=j['textures'][textureIndex];imageIndex=texture['source'];image=j['images'][imageIndex];view=j['bufferViews'][image['bufferView']];sourcePNG=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];assert sha(sourcePNG)==proposal['eyeTexturePNG_SHA256']
pixels=np.array(Image.open(io.BytesIO(sourcePNG)).convert('RGBA'));assert pixels.shape==(1024,1024,4);rgb=pixels[:,:,:3].astype(float)/255;linear=decode(rgb);lum=np.sum(linear*np.array([.2126,.7152,.0722]),axis=2);yy,xx=np.indices(pixels.shape[:2]);dark=(pixels[:,:,:3].max(2)<20)&(pixels[:,:,3]==255);components,_=label(dark);pupil=np.zeros(dark.shape,bool)
for eye in proposal['eyes']:
 landmark=eye['pupilAndIris'];component=components==landmark['pupilTextureComponent'];assert int(component.sum())==landmark['pupilTexturePixels'];pupil|=component
# All bright source sclera is outside both authorized radial annuli. This guard
# detects unexpected atlas/centre mismatch; it does not invent a new edit mask.
sclera=(rgb.min(2)>.5)&(np.ptp(rgb,axis=2)<.15)
weights=np.zeros(lum.shape);targetLinear=np.zeros_like(linear);intent=np.array([.263,.155,.100]);intentLinear=decode(intent);intentY=float(np.sum(intentLinear*[.2126,.7152,.0722]));eyes=[]
for eye in proposal['eyes']:
 cx,cy=eye['pupilAndIris']['pupilTextureCentre'];radius=np.hypot(xx-cx,yy-cy);annulus=(radius>=52)&(radius<=110);protected=pupil|(pixels[:,:,3]!=255);eligible=annulus&~protected;assert not np.any(annulus&sclera),'Authorized ring unexpectedly crosses bright sclera'
 feather=smooth((radius-52)/6)*smooth((110-radius)/6);feather[~eligible]=0;assert not np.any((weights>0)&(feather>0))
 median=float(np.median(lum[eligible]));assert median>0;relative=np.maximum(lum[eligible]/median,0)**.75;wanted=relative[:,None]*intentLinear;assert wanted.max()<=1,'Fixed curve requires no clipping'
 targetLinear[eligible]=wanted;weights+=feather;eyes.append({'eye':eye['eye'],'opaquePrimitive':eye['sourcePrimitive'],'pupilCentrePixels':[cx,cy],'pupilComponent':eye['pupilAndIris']['pupilTextureComponent'],'pupilPixels':eye['pupilAndIris']['pupilTexturePixels'],'annulusPixels':int(annulus.sum()),'eligiblePixels':int(eligible.sum()),'activeFeatherPixels':int((feather>0).sum()),'sourceLinearLuminanceMedian':median,'maximumTargetLinearChannel':float(wanted.max()),'minimumPupilProtectedRadius':float(radius[pupil&annulus].min()) if np.any(pupil&annulus) else None})
active=weights>0;corrected=pixels.copy();mixed=(1-weights[active,None])*linear[active]+weights[active,None]*targetLinear[active];encoded=encode(mixed);assert np.isfinite(encoded).all();assert encoded.min()>=0 and encoded.max()<=1;corrected[active,:3]=np.floor(encoded*255+.5).astype(np.uint8)
assert np.array_equal(corrected[:,:,3],pixels[:,:,3]);assert np.array_equal(corrected[~active],pixels[~active]);assert np.array_equal(corrected[pupil|sclera],pixels[pupil|sclera]);assert SOURCE.read_bytes()==raw
output=io.BytesIO();Image.fromarray(corrected,'RGBA').save(output,format='PNG',compress_level=9);png=output.getvalue();frozen(RUN/'source-eye-atlas.png',sourcePNG);frozen(RUN/'iris-brown-albedo.png',png)
maskfile=RUN/'exact-mask.npz';maskIO=io.BytesIO();np.savez_compressed(maskIO,weight=weights,active=active,pupilProtected=pupil,scleraProtected=sclera);frozen(maskfile,maskIO.getvalue())
newView=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(png)});newImage=len(j['images']);j['images'].append({'bufferView':newView,'mimeType':'image/png','name':'Iris annulus warm-brown28; original pupil/sclera pixels preserved'});newTexture=len(j['textures']);tex=copy.deepcopy(texture);tex['source']=newImage;j['textures'].append(tex);newMaterial=len(j['materials']);mat=copy.deepcopy(material);mat['name']='CC0 eye with fixed iris-annulus albedo28';mat['pbrMetallicRoughness']['baseColorTexture']['index']=newTexture;j['materials'].append(mat)
for i in [4,6]:pr[i]['material']=newMaterial
newBIN=binary+png+b'\x00'*((-len(png))%4);j['buffers'][0]['byteLength']=len(newBIN);js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((-len(js))%4);result=struct.pack('<III',0x46546c67,2,28+len(js)+len(newBIN))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(newBIN),0x004e4942)+newBIN;frozen(RUN/'rider.glb',result)
assert newBIN[:len(binary)]==binary
settings={'oneConstruction':True,'noParameterSweep':True,'radialAnnulusPixels':[52,110],'interiorFeatherPixels':6,'feather':'product of two cubic smoothsteps, fully weighted58..104px','pupilProtection':'Exact two original dark connected components from committed27 audit override annulus','brightScleraGuard':'source min(encodedRGB)>.5 and max-min<.15; no overlap with annuli; all outside active pixels preserved','alphaProtection':'All alpha values exact; only originally alpha255 RGB eligible','fixedIntentEncodedSRGB':intent.tolist(),'intentLinearRGB':intentLinear.tolist(),'intentLinearLuminance':intentY,'sourceFibreCurve':'Per-eye source linear luminance normalized by annulus median, exponent0.75, times fixed target linear RGB; feathers blend in linear RGB','quantization':'standard sRGB transfer; floor(value*255+.5)','originalOpaqueEyeRoughness':.35,'hiddenCorneaMaterialsUnchanged':True,'catchlightsEmissionOpticsAdded':False,'eyes':eyes}
report={'source':str(SOURCE),'sourceSHA256':sha(raw),'candidate':str(RUN/'rider.glb'),'candidateSHA256':sha(result),'candidateBytes':len(result),'sourcePNG_SHA256':sha(sourcePNG),'candidatePNG_SHA256':sha(png),'maskNPZ_SHA256':sha(maskfile.read_bytes()),'originalBinaryPrefixExactBytes':len(binary),'oldGeometryAccessorsUVNormalsSkin19RigHeadHoodNeckExact':True,'onlyMaterialIndexChanges':{'mesh':1,'primitives':[4,6],'old':6,'new':newMaterial},'addedAtlasViewImageTextureMaterial':[newView,newImage,newTexture,newMaterial],'activePixels':int(active.sum()),'changedRGBPixels':int(np.any(corrected[:,:,:3]!=pixels[:,:,:3],axis=2).sum()),'alphaOutsidePupilScleraPixelsExact':True,'sourceUnchanged':True,'proposalSHA256':{'README.md':sha((PROPOSAL/'README.md').read_bytes()),'parent-judgment.json':sha((PROPOSAL/'parent-judgment.json').read_bytes()),'eye-appearance-audit.json':sha((PROPOSAL/'eye-appearance-audit.json').read_bytes())},'settings':settings,'limits':'One unaccepted albedo-only candidate. Geometry, gaze, aperture and baseline hidden-cornea behavior unchanged; no moving visual score or optical improvement proved.'}
(OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'settings.json').write_text(json.dumps(settings,indent=2)+'\n');(OUT/'model-map.json').write_text(json.dumps({'models/rider-street-mustard.glb':str(RUN/'rider.glb'),'models/rider-street-mustard-lod.glb':str(RUN/'rider.glb')},indent=2)+'\n');print(json.dumps({'candidateSHA256':sha(result),'candidateBytes':len(result),'changedRGBPixels':report['changedRGBPixels'],'activePixels':report['activePixels'],'pngSHA256':sha(png)}))
