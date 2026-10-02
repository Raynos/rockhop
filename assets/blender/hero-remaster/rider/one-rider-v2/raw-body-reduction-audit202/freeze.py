"""Freeze read-only source pins, numeric findings and diagnostic contour board."""
import os
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import json,hashlib,time,resource
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1');A=R/'assets/blender/hero-remaster/rider/one-rider-v2/raw-body-reduction-audit202';O=R/'docs/evidence/hero-remaster/one-rider-v2/raw-body-reduction-audit202';D=B/'one-rider-v2/raw-body-reduction-audit202'
assert not (O/'freeze.json').exists(),'Never overwrite frozen audit'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
report=json.loads((O/'report.json').read_text());line=json.loads((O/'lineage.json').read_text());probe=json.loads((O/'probe.json').read_text());inputs=[Path(p)for p in probe['files']]
inputs += [B/'hunyuan21/04'/p for p in ['shape.obj','textured.obj','shape-progress.json','run.log']]
inputs += [B/'hunyuan21-launcher'/p for p in ['rockhop_hunyuan21_runner.py','rockhop_hunyuan21_export.py','rockhop-hunyuan21.sh']]
inputs += [R/'assets/blender/hero-remaster/rider/search-v1/render_hunyuan21.py',R/'assets/blender/hero-remaster/rider/one-rider-v2/candidate-handoff170/map_candidate.py',R/'assets/blender/hero-remaster/rider/one-rider-v2/glove-cleanup/neutral-assembly/build_neutral_assembly.py',R/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/neutral-assembly/report.json',R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind04/build.py',R/'assets/blender/hero-remaster/rider/one-rider-v2/source-axilla189/audit.py']
source=Path('/Users/raynos/ml/img2mesh/Hunyuan3D-2.1');inputs +=[source/'hy3dpaint'/p for p in ['textureGenPipeline.py','DifferentiableRenderer/MeshRender.py','DifferentiableRenderer/mesh_utils.py','utils/uvwrap_utils.py','utils/pipeline_utils.py']]
for p in probe['files']:assert sha(p)==probe['files'][p]['sha256']
generation=json.loads((B/'hunyuan21/04/generation.json').read_text());assert generation['version']=='Hunyuan3D-2.1'and generation['nativeSHA256']==sha(B/'hunyuan21/04/raw-shape.npz')and generation['runnerSHA256']==sha(B/'hunyuan21-launcher/rockhop_hunyuan21_runner.py')
for n in ['raw-shape.npz','raw-shape.glb','shape.glb','model.glb','shape.obj','textured.obj']:assert sha(B/'hunyuan21/04'/n)==generation['outputs'][n]['sha256']
report['inputPins']={str(p):{'sha256':sha(p),'bytes':p.stat().st_size}for p in inputs};report['sourceFilesUnchangedDuringAudit']=True;report['bounds']={'secondsCap':1200,'anonymousMemoryBytesCap':70000000000,'CPUThreads':2,'actualCalculationSeconds':report['seconds'],'peakRSSBytes':report['peakRSSBytes'],'GPU':False,'actualWallBatchUnder1200':True,'memoryNote':'peak RSS~resource receipt for Python process only; anonymous system memory gate recorded below'}
# Source routine literally get_mesh(.cpu().numpy()) shares storage on CPU. Two normalized calls apply inverse B twice; final denormalized call returns B² about bbox centre.
S=np.load(D/'lineage.npz')['reducedPositions'];M=np.array(line['nativeToCurrentRestMatrix']);native=np.load(B/'hunyuan21/04/raw-shape.npz');x= np.load(D/'native-graph.npz');F=x['faces'];E=np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),axis=1);counts=Counter(map(tuple,E));pathchecks=[]
for c in report['meshes']['native']['connections']:
 path=c['pathPhysicalIDs'];bad=[list(sorted((a,b)))for a,b in zip(path,path[1:]) if counts[tuple(sorted((a,b)))]!=2];pathchecks.append({'side':c['label'],'pathEdgeCount':len(path)-1,'allPathEdgesExactlyTwoIncidentTriangles':not bad,'badEdges':bad})
report['rawConnectionPathsAreOrdinaryTwoFaceEdges']=pathchecks
assert all(x['allPathEdgesExactlyTwoIncidentTriangles']for x in pathchecks)
report['measuredRawToReducedConnectionShiftM']={c['label']:report['meshes']['reduced']['connections'][i]['firstConnectionY_M']-c['firstConnectionY_M']for i,c in enumerate(report['meshes']['native']['connections'])}
report['paintFlipMechanismConfidence']='Observed source-derived bbox-centred X180 map and all55000 face incidences verified. Current installed source code plus CPU inpainting call chain explains it, but generation recorded commit only, not modified source-file hashes; historical implementation attribution is an inference.'
# Compact gray line plot is a construction diagnostic, never character render or moving pass.
W,H=1440,1240;im=Image.new('RGB',(W,H),(25,27,31));draw=ImageDraw.Draw(im)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',22);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
draw.text((18,12),'H21-4: unchanged raw / reduced / assembled body contours',font=font,fill='white');draw.text((18,45),'STATIC source geometry audit only; equal canonical axes; no skin or appearance acceptance',font=small,fill=(245,188,89))
for col,name in enumerate(['native','reduced','current']):
 data=json.loads((D/f'{name}-sections.json').read_text());draw.text((col*480+16,78),f'{name.upper()} / '+str(report['meshes'][name]['triangles'])+' triangles',font=font,fill='white')
 for row,y in enumerate([1.18,1.20,1.30]):
  section=next(s for s in data if s['heightY_M']==y);ox=col*480+18;oy=112+row*370;draw.rectangle((ox,oy,ox+445,oy+345),outline=(85,89,99));draw.text((ox+8,oy+8),f'Y={y:.2f}m / {len(section["contours"])} contours',font=small,fill='white')
  # section plot axes: lateralZhorizontal, forwardXvertical; isotropic 320px/metre.
  def xy(p):return (ox+223+p[2]*350,oy+307-(p[0]-.46)*350)
  for contour in section['contours']:
   color=(175,184,197)if contour['label']=='central'else(98,177,223)if contour['label']=='positiveZ'else(219,155,102)
   for s in contour['segments']:draw.line([xy(p)for p in s['positions']],fill=color,width=2)
  draw.text((ox+8,oy+321),'section axes: lateral Z →; forward X ↑',font=small,fill=(170,177,190))
draw.text((18,1220),'Both raw underarms connect around1.190m; reduction changes this by0.206mm /−0.021mm.',font=small,fill='white');im.save(O/'contour-comparison.png')
# Mac VM anonymous pages receipt (system snapshot, no GPU job launched).
import subprocess,re
vm=subprocess.check_output(['/usr/bin/vm_stat'],text=True);page=int(re.search(r'page size of (\d+) bytes',vm).group(1));anon=int(re.search(r'Anonymous pages:\s+(\d+)',vm).group(1))*page;assert anon<70000000000
report['bounds']['anonymousSystemMemoryBytesSnapshot']=anon
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n')
(O/'setup-diagnostics.json').write_text(json.dumps({'initialProbeFailure':'Wrong NumPy broadcast shape failed before output; fixed by adding axis dimension. No source writes.','probeNativeGLBExactNPZFalse':'Provisional probe queried accessor0 rather than POSITION accessor; ignored. Authoritative lineage selects POSITION and verifies bit-exact Float32NPZ and indices.','rejectedProvisionalLineage':'Initially omitted painter bbox-centred X180; retained rejected-provisional-lineage.json. This gave48.977mm median paint→reduced mismatch. Source-derived corrected map reduces maximum to0.870334µm and matches all55000 indexed faces. No fitted transform used.','historicalCodePinLimit':report['paintFlipMechanismConfidence']},indent=2)+'\n')
(O/'README.md').write_text('''# H21-4 pre-decimation body construction audit202

Finding: the high-resolution native shape already has the low fused arm–central construction. Returning to raw344456 triangles alone will not provide the separated high armhole needed for the next repair. This is a static construction proxy, not anatomical ownership, rig suitability or visual acceptance.

Literal source-relative sublevel connections:

| Source | Left +Z | Right −Z |
| --- | ---: | ---: |
| Native raw before cleanup/reduction |1.189948355m|1.190575006m|
| Reduced55000-face shape |1.190154172m|1.190553729m|
| Painted display derivative |1.190153980m|1.190553674m|
| Current source185 body |1.190154076m|1.190553665m|

Raw→reduced shifts are +0.205817mm and −0.021277mm. All four meshes have three closed triangle-section contours atY1.18, then one atY1.20,1.24 and1.30. Raw critical connection paths use ordinary two-face edges, so this finding is not caused by position deduplication or a nonmanifold edge; all172223 native rows are already physically unique. Raw has17 components and10 nonmanifold edges elsewhere; no whole-body topology pass is claimed.

Lineage: `lineage.json` pins a literal source-derived transform, not a fit. RawGLB positions exactly encode nativeNPZ Float32 and face IDs. The painted OBJ is rotated X180 about the reduced bbox centre. That inverse map recovers every painted vertex within0.870334microns and every55000-face incidence. Working-display2 changes only its node rotation and preserves BIN. Neutral assembly's recorded scale/translation and bind04's proper rotation/1.015 scale/.65m shift transfer these coordinates into source185 rest axes. Current body's22240 POSITION rows and33968 faces are bit-exact body11. All selected low underarm rows belowY1.35 match paint positions within2microns;75 higher collar-boundary rows differ by disclosed earlier collar edits.

The current pinned installed CPU painter implementation returns mutating NumPy views in normalized `get_mesh`; two inpainting calls explain the observed bbox-centred X180. Generation recorded the source commit, not historical modified-source-file hashes, so attribution to that implementation is an inference. Exact observed transforms and face correspondence are verified regardless.

Limits: cleanup intermediates and native→reduced face ancestry were not saved. Tiny connection shifts cannot be assigned separately to FloaterRemover, DegenerateFaceRemover or FaceReducer. No comparative pose, contact, skin or appearance score was tested. Parent alone judges. No geometry, weights, rig, head, clothing source files or player assets changed; no GPU work.

Reproduction: run `lineage.py` then `audit.py` with installed unimate Python, CPU2, NumPy/SciPy; immutable outputs are pinned by `freeze.json`. `freeze.py` is once-only. Private NPZ graphs and complete edge-keyed sections preserve actual witnesses. `contour-comparison.png` is a static source-line plot, not a character deliverable. Setup mistakes and the rejected provisional axis assumption remain recorded in `setup-diagnostics.json`.
''')
owned=[p for root in [A,O] for p in sorted(root.glob('*'))if p.is_file()and p.name!='freeze.json'];private=[p for p in sorted(D.glob('*'))if p.is_file()]
freeze={'status':'FROZEN_READ_ONLY_NO_ASSET_OR_SKIN_ACCEPTANCE','inputPins':report['inputPins'],'ownedFiles':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size}for p in owned},'privateOutputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size}for p in private},'sourceUnchanged':True}
(O/'freeze.json').write_text(json.dumps(freeze,indent=2)+'\n');print(json.dumps({'owned':len(owned),'inputs':len(inputs),'private':len(private),'receiptSHA256':sha(O/'freeze.json'),'anonymousMemoryBytes':anon}))
