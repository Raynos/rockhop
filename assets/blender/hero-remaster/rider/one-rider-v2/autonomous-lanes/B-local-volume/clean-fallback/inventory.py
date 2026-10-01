"""Read-only new garment donor inventory, no mesh construction or selection."""
from pathlib import Path
import numpy as np,json,hashlib,resource
from PIL import Image
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/B-local-volume/clean-fallback');O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();rows=[]
for name in ['01','02','03','05']:
 d=R/'hunyuan21'/name;j=json.loads((d/'generation.json').read_text());p=d/'raw-shape.npz';a=np.load(p);shapes={k:list(a[k].shape) for k in a.files};jout=j['outputs'];files={}
 for fn in ['raw-shape.npz','raw-shape.glb','model.glb','textured.jpg','textured_roughness.jpg','textured_metallic.jpg']:
  path=d/fn;h=sha(path);record=jout.get(fn);x={'path':str(path),'bytes':path.stat().st_size,'sha256':h,'recordedHashMatches':record and h==record['sha256']}
  if path.suffix=='.jpg':im=Image.open(path);x['dimensions']=list(im.size)
  files[fn]=x
 rows.append({'candidate':'H21-'+name,'use':'Potential NEW whole-hood donor only, no extraction/refinement/appearance selection performed','version':j['version'],'sourceCommit':j['source_commit'],'weightsRevision':j['weights_revision'],'rawFacesRecord':j['raw_faces'],'texturedFacesRecord':j['faces'],'rawNPZShapes':shapes,'shapeStatus':'Retained actual higher-resolution pre-reduction shape, not assumed clean hood topology','files':files,'generationJSON':str(d/'generation.json'),'generationSHA256':sha(d/'generation.json')})
addon=Path('/Users/raynos/Library/Application Support/Blender/5.1/extensions/.user/user_default/mpfb/data/clothes');clothes=[]
for d in sorted(addon.iterdir()):
 if not d.is_dir():continue
 mats=list(d.glob('*.mhmat'));objs=list(d.glob('*.obj'));clothes.append({'name':d.name,'objFiles':[str(p) for p in objs],'materialDeclarations':[{'path':str(p),'sha256':sha(p),'hasExplicitCC0September2020':'explicitly released as CC0 in september 2020' in p.read_text(errors='replace')} for p in mats],'hoodStatus':'Not hood clothing; actual installed thumbnails inspected for casual/sports/work candidates' if ('casual' in d.name or 'sport' in d.name or 'worksuit' in d.name) else 'Name/category is suit,shoe orfedora, no hood candidate'})
report={'status':'Read-only fallback capability/spec inventory, no geometry experiment or direction selection','oldSourceHoodRepairLineageNotReused':True,'excludedH21-04':'Chosen production candidate source-strip lineage; not eligible as renamed fallback','excludedP3':'Automated repair lineage stopped earlier; not silently resumed','newGeneratedPotentialDonors':rows,'installedNativeCC0Clothes':clothes,'installedHoodDonorFound':False,'installedNativeThumbnailsConclusion':'Six male casual sets show shirts, crew-neck sweatshirt, puffer jacket and T-shirts; female casual/sports and male work are T-shirts/overalls, no hood','sourceMeshesUnchanged':True,'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'recipeSHA256':sha(__file__)}
(O/'inventory.json').write_text(json.dumps(report,indent=2)+'\n');print([(x['candidate'],x['rawFacesRecord'],x['rawNPZShapes']) for x in rows]);print('nativeclothes',len(clothes),'hoods',False)
