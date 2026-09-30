"""Serial common raw-body renderer and pixel-only board composer.

Uses the parent's frozen Blender renderer without changing source bodies.
TRELLIS native display only swaps axes as the installed o_voxel exporter does.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,time
import numpy as np
import trimesh
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent
RENDERER=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/search-v1/render_raw.py')
BLENDER='/Applications/Blender.app/Contents/MacOS/Blender'
POST=Path('/Users/raynos/ml/img2mesh/trellis-mac/deps/trellis2-apple/o-voxel/o_voxel/postprocess.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
OUT=ROOT/'rendered';OUT.mkdir(exist_ok=True)
recipe={'status':'frozen raw-body render invocation; parent judges',
        'renderer':str(RENDERER),'rendererSHA256':sha(RENDERER),'launcherSHA256':sha(Path(__file__)),
        'nativeTrellisTransform':{'source':str(POST),'sourceSHA256':sha(POST),'lines':[476,477],
          'mapping':'(x,y,z) -> (x,z,-y), same as o_voxel.to_glb; no merge, cleanup, remesh, reduction or geometry fit',
          'matrix':[[1,0,0],[0,0,1],[0,-1,0]]},
        'frames':{'working':36,'reduced':9,'native-gray':9},'boardYaws':[0,40,80,120,160,200,240,280,320],
        'video':{'workingFrames':36,'fps':12,'codec':'libx264','pixelFormat':'yuv420p'},
        'limits':['Static unrigged turntable, not gameplay or acceptance',
                  'Working/reduced texture diagnostic sets metallic0; raw PBR source remains unchanged',
                  'Native-gray display uses exact native topology with neutral material only',
                  'Host may be contended; elapsed render time is not a benchmark']}
frozen=OUT/'recipe.json'
if frozen.exists():
 if json.loads(frozen.read_text())!=recipe:raise RuntimeError('Frozen render recipe changed')
else:dump(frozen,recipe)

def board(folder,n):
 manifest=json.loads((folder/'manifest.json').read_text())
 views=manifest['views'];assert len(views)==n
 files=[folder/v['file'] for v in views]
 assert all(f.is_file() for f in files)
 ids=list(range(0,36,4)) if n==36 else list(range(9))
 tile=Image.open(files[0]);w,h=tile.size;header=28
 result=Image.new('RGB',(w*3,(h+header)*3),(23,23,23));draw=ImageDraw.Draw(result)
 for k,frame in enumerate(ids):
  assert abs(views[frame]['yaw']-k*40)<1e-10
  x=k%3*w;y=k//3*(h+header)
  result.paste(Image.open(files[frame]).convert('RGB'),(x,y+header))
  draw.text((x+10,y+8),f'{folder.parent.parent.name} {folder.parent.name} / {folder.name} / yaw {k*40} deg',fill=(235,235,235))
 result.save(folder/'board.png')
 dump(folder/'files.json',{'status':'frame and board inventory; no art acceptance',
      'manifestSHA256':sha(folder/'manifest.json'),
      'frames':[{'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in files],
      'board':{'path':str(folder/'board.png'),'sha256':sha(folder/'board.png'),'bytes':(folder/'board.png').stat().st_size},
      'anglesVerified':True})

completed=[]
for engine in ('hunyuan','trellis'):
 for i in range(1,6):
  stem=f'{i:02d}';base=OUT/engine/stem;base.mkdir(parents=True,exist_ok=True)
  native_dir=base/'native-gray';native_dir.mkdir(exist_ok=True)
  if engine=='hunyuan':native=ROOT/engine/f'{stem}.raw-shape.glb'
  else:
   native=native_dir/'native.glb';archive=ROOT/engine/f'{stem}.npz'
   if not native.exists():
    d=np.load(archive);v=d['vertices'].copy();f=d['faces'].copy()
    transformed=v.copy();transformed[:,1],transformed[:,2]=v[:,2],-v[:,1]
    trimesh.Trimesh(vertices=transformed,faces=f,process=False).export(native)
    dump(native_dir/'native-display.json',{'nativeArchive':str(archive),'nativeArchiveSHA256':sha(archive),
         'displayGLB':str(native),'displaySHA256':sha(native),'vertices':len(v),'faces':len(f),
         'mapping':recipe['nativeTrellisTransform'],'positionDtype':str(v.dtype),'faceDtype':str(f.dtype),
         'limits':['Axis conversion only; source NPZ preserved; no simplification/cleanup']})
  model={'engine':engine,'design':stem,'status':'rendered static diagnostics; parent judges','views':[]}
  for tier,src,gray in [('working',ROOT/engine/f'{stem}.glb',False),('reduced',ROOT/engine/f'{stem}.reduced.glb',False),('native-gray',native,True)]:
   folder=base/tier;n=recipe['frames'][tier];before=sha(src);start=time.time()
   cmd=[BLENDER,'-b','--factory-startup','--python-exit-code','1','--python',str(RENDERER),'--','--input',str(src),'--out',str(folder),'--frames',str(n)]
   if gray:cmd.append('--gray')
   if not (folder/'manifest.json').exists():
    folder.mkdir(exist_ok=True)
    with (folder/'render.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
   manifest=json.loads((folder/'manifest.json').read_text())
   assert manifest['rendererSHA256']==recipe['rendererSHA256']
   assert manifest['inputSHA256']==before and sha(src)==before
   board(folder,n)
   if tier=='working':
    subprocess.run(['ffmpeg','-v','error','-y','-framerate','12','-i',str(folder/'%04d.png'),'-frames:v','36','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-threads','4',str(folder/'orbit.mp4')],check=True)
    video={'path':str(folder/'orbit.mp4'),'sha256':sha(folder/'orbit.mp4'),'bytes':(folder/'orbit.mp4').stat().st_size}
   else:video=None
   model['views'].append({'tier':tier,'command':cmd,'wallSeconds':round(time.time()-start,3),'manifest':str(folder/'manifest.json'),'manifestSHA256':sha(folder/'manifest.json'),'video':video})
  dump(base/'model-render.json',model);completed.append(model)
  dump(OUT/'completed.json',{'status':'parent moving/static review pending','models':completed})
  print(json.dumps({'engine':engine,'design':stem,'completedTiers':['working','reduced','native-gray'],'workingOrbit':str(base/'working/orbit.mp4'),'boards':[str(base/t/'board.png') for t in ['working','reduced','native-gray']]}),flush=True)
