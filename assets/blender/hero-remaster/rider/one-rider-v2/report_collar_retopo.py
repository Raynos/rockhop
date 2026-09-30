"""Freeze actual local rim trial, including visible failures before correction."""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image,ImageDraw
r=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/collar-retopo1')
o=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/collar/retopo1');o.mkdir(parents=True,exist_ok=True)
assert not (o/'parent-verdict.json').exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
board=Image.new('RGB',(1280,2688),(22,25,28));draw=ImageDraw.Draw(board);rows=[]
for col,mode in enumerate(['pbr','gray']):
 m=json.loads((r/mode/'manifest.json').read_text());shutil.copyfile(r/mode/'manifest.json',o/f'{mode}-manifest.json')
 for i,row in enumerate(m['views']):
  p=r/mode/row['file'];assert sha(p)==row['sha256'];shutil.copyfile(p,o/f'{mode}-{i}.png')
  board.paste(Image.open(p).convert('RGB'),(col*640,i*672+32));draw.text((col*640+8,i*672),f'{mode} actual rim / yaw {row["yaw"]}',fill='white');rows.append({'path':str(p),'sha256':sha(p)})
board.save(o/'actual-rim.jpg',quality=93);shutil.copyfile(r/'report.json',o/'construction.json')
(o/'parent-verdict.json').write_text(json.dumps({'status':'REJECTED local rim trial1; no head attached','failedFixes':1,'visibleDefects':['Unsmooth source-to-authored ring transition and pointed remaining shoulder-rim anchors','Donor UV interpolation produces dark striped texture artifacts','Uniform authored ring reads thin and synthetic rather than soft cloth'],'geometry':'One105edge open rim and0nonmanifold edges; topology alone is not visual acceptance','sourceUnchanged':True,'framesVerified':rows,'nextSpecificCorrection':'Smooth ordered arc-length rim/anchor transition with local normal continuity; explicit continuous UV/new neutral cloth material preview instead of disconnected donor coordinates. One correction only.','limits':['No accepted hood silhouette/texture/skin join','No deformation/rig/player promotion']},indent=2)+'\n')
(o/'README.md').write_text('''# Explicit local collar retopology: rejected first trial\n\nThe graph-cut technique remains stopped. This distinct local retopology\ntrial removes a40mm strip around the earlier failed collar circuit and\nbridges the retained real source boundary to an explicitly authored hood\nopening. It removes old hair but fails appearance: pointed source anchors,\na thin synthetic rim and dark donor-UV stripes remain. No new head joins it.\n\nActual matched PBR/gray four-angle renders and construction/source hashes\nare frozen here. All retained source triangles preserve exact positions\nand UVs; new collar triangles use disclosed donor UVs. Those UVs are not\na usable bake. The source body/raw data are untouched.\n\nOne correction will smooth the ordered rim/anchor transition and preview\nnew cloth with continuous UVs and a neutral material. Full matched texture\nbaking and actual neck deformation remain required before acceptance.\n''')
