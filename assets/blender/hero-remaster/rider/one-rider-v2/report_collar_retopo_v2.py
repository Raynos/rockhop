"""Freeze actual local rim trial, including visible failures before correction."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image,ImageDraw
r=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/collar-retopo2')
o=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/collar/retopo2');o.mkdir(parents=True,exist_ok=True)
assert not (o/'parent-verdict.json').exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
board=Image.new('RGB',(1280,2688),(22,25,28));draw=ImageDraw.Draw(board);rows=[]
for col,mode in enumerate(['pbr','gray']):
 m=json.loads((r/mode/'manifest.json').read_text());shutil.copyfile(r/mode/'manifest.json',o/f'{mode}-manifest.json')
 for i,row in enumerate(m['views']):
  p=r/mode/row['file'];assert sha(p)==row['sha256'];shutil.copyfile(p,o/f'{mode}-{i}.png')
  board.paste(Image.open(p).convert('RGB'),(col*640,i*672+32));draw.text((col*640+8,i*672),f'{mode} actual rim / yaw {row["yaw"]}',fill='white');rows.append({'path':str(p),'sha256':sha(p)})
board.save(o/'actual-rim.jpg',quality=93);shutil.copyfile(r/'report.json',o/'construction.json')
(o/'parent-verdict.json').write_text(json.dumps({'status':'REJECTED local rim trial2; explicit elliptical rim technique stopped','failedFixes':2,'visibleDefects':['Source-to-rim transition retains pointed side anchors despite boundary smoothing','Intended separate plain-cloth preview material did not survive Trimesh multi-material export; native donor UV stripes remain','Elliptical rim still reads synthetic rather than the source soft folded cloth'],'geometry':'One105edge open rim and0nonmanifold edges; topology alone is not visual acceptance','sourceUnchanged':True,'framesVerified':rows,'nextSpecificCorrection':'STOP elliptical ring retopology after two appearance failures. Native Blender face-corner UV/material assignment and wider garment-aware local sculpt/retopology are required; no third ring tweak.','limits':['No accepted hood silhouette/texture/skin join','No deformation/rig/player promotion']},indent=2)+'\n')
(o/'README.md').write_text('''# Explicit local collar retopology: second failure

Parent rejects the second rim: source side anchors remain pointed and the
elliptical rim still reads synthetic. The intended plain-cloth preview
material did not survive Trimesh multi-material export; native donor-UV
stripes remain visible. This is a pipeline failure as well as an art failure,
not an accepted material preview or completed continuous UV layout.

Actual PBR/gray four-angle views are frozen alongside construction/source
hashes. One105edge opening remains and no new head attaches. Original
source stays untouched; local105boundary vertices move at most9.724mm.

Stop this elliptical ring technique after two failed fixes. The specific
alternative is garment-aware local retopology/sculpt in native Blender,
with actual face-corner UV/material assignment verified after reimport.
No third ring tweak, accepted hood/skin join, deformation or texture pass.
''')
