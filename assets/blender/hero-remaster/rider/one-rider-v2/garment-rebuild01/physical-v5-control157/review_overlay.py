"""Frozen11 renderer + mappedV5GLB + one source-bound anatomical-axis branch."""
from pathlib import Path
import json,hashlib,shutil
repo=Path('/Users/raynos/projects/games/rockhop');source=repo/'harness/out/hero-remaster/new-rider-body11-build';out=repo/'harness/out/hero-remaster/new-rider-physical-v5-control157-overlay'
proof=json.loads((repo/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/physical-v5-control157/mapping-report.json').read_text());candidate=Path(proof['candidate']);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(candidate.read_bytes())==proof['candidateSHA256'];assert not out.exists();shutil.copytree(source,out)
catalog=json.loads((out/'model-catalog.json').read_text());changes=[]
for model in catalog['models']:
 if model['logical'] not in ['models/rider-street-mustard.glb','models/rider-street-mustard-lod.glb']:continue
 oldurl=model['url'];oldsha=model['sha256'];newurl=oldurl.replace(oldsha[:16],proof['candidateSHA256'][:16]);path=out/newurl;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(candidate.read_bytes())
 for p in out.rglob('*'):
  if p.is_file() and p.suffix in ['.js','.json','.html']:
   s=p.read_text();n=s.replace(oldurl,newurl).replace(oldsha,proof['candidateSHA256'])
   if n!=s:p.write_text(n)
 model.update(url=newurl,sha256=proof['candidateSHA256'],bytes=candidate.stat().st_size);changes.append({'logical':model['logical'],'oldURL':oldurl,'newURL':newurl})
 assert sha(path.read_bytes())==proof['candidateSHA256']
assert len(changes)==2;(out/'model-catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
hero=json.loads((out/'hero-review.json').read_text());hero['sourceBuild']=str(source);hero['mapping']={m['logical']:str(candidate) for m in catalog['models'] if m['logical'] in ['models/rider-street-mustard.glb','models/rider-street-mustard-lod.glb']};hero['models']=catalog['models'];hero['privateFreshC19RigAdapter']=True;(out/'hero-review.json').write_text(json.dumps(hero,indent=2)+'\n')
# Frozen bundle exposes the exact constructor axis capture, with unmangled identifiers.
# This private-only inline branch is equivalent to the source adapter's14childaxes.
anchor='this.d0.set(name,new Vector3(0,1,0).applyQuaternion(q).normalize())'
children={'pelvis':'spine','spine':'chest','chest':'neck','neck':'head'}
for sd in ['L','R']:
 children.update({'shoulder.'+sd:'upperArm.'+sd,'upperArm.'+sd:'forearm.'+sd,'forearm.'+sd:'hand.'+sd,'thigh.'+sd:'shin.'+sd,'shin.'+sd:'foot.'+sd})
replacement='this.d0.set(name,(()=>{let freshC19Axes=false;this.scene.traverse(o=>{if(o.userData.rockhopFreshC19RestAxes==="WORLD_ALIGNED_EXPLICIT_CHILD_DIRECTIONS")freshC19Axes=true});const next='+json.dumps(children,separators=(',',':'))+'[name];if(freshC19Axes&&next){const child=this.bones.get(next);if(!child)throw new Error("FreshC19 anatomical child missing");const direction=child.getWorldPosition(new Vector3).sub(b.getWorldPosition(new Vector3));if(direction.lengthSq()<1e-10)throw new Error("FreshC19 rest axis collapsed");return direction.normalize()}return new Vector3(0,1,0).applyQuaternion(q).normalize()})())'
matched=[]
for p in (out/'assets').glob('*.js'):
 s=p.read_text()
 if anchor not in s:continue
 assert s.count(anchor)==1;before=sha(p.read_bytes());p.write_text(s.replace(anchor,replacement));matched.append({'file':str(p.relative_to(out)),'beforeAxisPatchSHA256':before,'afterAxisPatchSHA256':sha(p.read_bytes()),'beforeChars':len(s),'afterChars':len(p.read_text())})
assert len(matched)==1
report={'kind':'Frozen11 exact renderer/physics/materials/bike plus exact V5 mapped C19 static shape/weights and one explicit14childaxis branch','sourceBuild':str(source),'candidateSHA256':proof['candidateSHA256'],'releaseBuild':False,'changes':changes,'axisPatch':matched,'axisMap':children,'limits':'Private diagnostics only. Frozen filename remains intentionally stable; not a release immutable-cache or bundle/performance gate. Legacy source11fallback axis expression unchanged; source34flag binds fresh path. Actual browser axis/pose proof required before appearance review.'}
(out/'fresh-rig-overlay.json').write_text(json.dumps(report,indent=2)+'\n');(repo/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/physical-v5-control157/review-overlay-proof.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
