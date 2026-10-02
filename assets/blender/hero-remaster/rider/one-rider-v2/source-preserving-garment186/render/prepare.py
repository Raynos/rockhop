"""Neutral static view: remove only skins, animations and node.skin JSON."""
from pathlib import Path
import json,struct,hashlib,copy
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');A=R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment186/render';E=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment186/render';S=B/'source-preserving-garment186/render';S.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();src=B/'source-preserving-garment185/operator/rider.glb';raw=src.read_bytes();assert sha(raw)=='ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5';n,typ=struct.unpack_from('<II',raw,12);assert typ==0x4e4f534a;d=json.loads(raw[20:20+n]);original=copy.deepcopy(d);tail=raw[20+n:];oldSkinCount=len(d.get('skins',[]));oldSkinNodes=[i for i,v in enumerate(d['nodes'])if 'skin'in v];oldAnimations=len(d.get('animations',[]));d.pop('skins',None);d.pop('animations',None)
for v in d['nodes']:v.pop('skin',None)
js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);out=struct.pack('<III',0x46546c67,2,20+len(js)+len(tail))+struct.pack('<II',len(js),0x4e4f534a)+js+tail;p=S/'neutral-assembly01.glb';assert not p.exists();p.write_bytes(out);outn=struct.unpack_from('<I',out,12)[0];assert out[20+outn:]==tail
check=copy.deepcopy(d)
for k in ['skins','animations']:
 if k in original:check[k]=original[k]
for i in oldSkinNodes:check['nodes'][i]['skin']=original['nodes'][i]['skin']
assert check==original
oldRecipe=R/'assets/blender/hero-remaster/rider/one-rider-v2/clean-upper-shell01/continuous-sculpt179/render.py';s=oldRecipe.read_text();render=s.replace(str(B/'clean-upper-shell01/continuous-sculpt179'),str(S)).replace(str(R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/continuous-sculpt179'),str(E));assert render!=s;assert render.replace(str(S),str(B/'clean-upper-shell01/continuous-sculpt179')).replace(str(E),str(R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/continuous-sculpt179'))==s;(A/'render.py').write_text(render)
for k in ['blender-config','blender-scripts','logs']:(S/k).mkdir(exist_ok=True)
verifier=R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment185/verify_frozen.py'
result={'status':'NEUTRAL_JSON_ONLY_STATICVIEW_VERIFIED','source':str(src),'sourceSHA256':sha(raw),'neutralGLB':str(p),'neutralSHA256':sha(out),'binaryChunkHeaderAndBINExact':True,'allGeometryAccessorMaterialImageTransformJSONExact':True,'removedSkinCount':oldSkinCount,'removedSkinNodeIDs':oldSkinNodes,'removedAnimationCount':oldAnimations,'original19JointSkinAssetAcceptedAnimated':False,'settingsRecipe':str(oldRecipe),'settingsRecipeSHA256':sha(oldRecipe.read_bytes()),'renderRecipeSHA256':sha((A/'render.py').read_bytes()),'exactRecipeExceptPaths':True,'owned185VerifierSHA256':sha(verifier.read_bytes()),'prepareSHA256':sha(Path(__file__).read_bytes())};(E/'preparation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
