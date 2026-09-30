from pathlib import Path
import hashlib,json,subprocess,time
import numpy as np
import trimesh
from PIL import Image,ImageDraw

ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')
RENDER=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/search-v1/render_raw.py')
OUT=ROOT/'rendered/pixal';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
frozen=sha(RENDER)
for i in range(1,6):
    design=f'{i:02d}';source=ROOT/'pixal'/design
    while not (source/'result.json').exists():
        if (source/'failure.json').exists():raise RuntimeError('Pixal generation failed; no auto retry')
        time.sleep(5)
    base=OUT/design;base.mkdir(parents=True,exist_ok=True)
    native=base/'native.glb'
    if not native.exists():
        d=np.load(source/'native.npz');v=d['vertices'].copy();f=d['faces'].copy()
        # Exact native pipeline composition: o_voxel(x,z,-y), then
        # Pixal OUTPUT_TRANSFORMS['pixal3d'] = (-x,-z,-y): (-x,y,-z).
        v[:,0]*=-1;v[:,2]*=-1
        trimesh.Trimesh(vertices=v,faces=f,process=False).export(native)
        dump(base/'native-display.json',{'archiveSHA256':sha(source/'native.npz'),'displaySHA256':sha(native),'vertexCount':len(v),'triangles':len(f),'axisTransform':[[-1,0,0],[0,1,0],[0,0,-1]],'source':'Pixal generate_mps native o_voxel+o_voxel_native_export OUTPUT_TRANSFORMS','geometryProcessing':'axis conversion only; unchanged faces, no remesh/cleanup/reduction'})
    models=[]
    for tier,model,n,gray in [('working',source/'working.glb',36,False),('reduced',source/'reduced.glb',9,False),('native-gray',native,9,True)]:
        folder=base/tier;folder.mkdir(exist_ok=True)
        if not (folder/'manifest.json').exists():
            cmd=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup','--python-exit-code','1','--python',str(RENDER),'--','--input',str(model),'--out',str(folder),'--frames',str(n),'--yaw-offset','180']
            if gray:cmd.append('--gray')
            with (folder/'render.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        m=json.loads((folder/'manifest.json').read_text());assert m['rendererSHA256']==frozen and m['inputSHA256']==sha(model)
        w,h=512,768;board=Image.new('RGB',(3*w,3*(h+28)),(23,23,23));draw=ImageDraw.Draw(board)
        ids=list(range(0,36,4)) if n==36 else list(range(9))
        for k,frame in enumerate(ids):
            assert abs(m['views'][frame]['yaw']-180-k*40)<1e-10
            x=k%3*w;y=k//3*(h+28)
            board.paste(Image.open(folder/f'{frame:04d}.png').convert('RGB'),(x,y+28))
            draw.text((x+8,y+8),f'pixal {design} / {tier} / relative yaw {k*40} deg',fill='white')
        board.save(folder/'board.png')
        if n==36:subprocess.run(['ffmpeg','-v','error','-y','-framerate','12','-i',str(folder/'%04d.png'),'-frames:v','36','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-threads','4',str(folder/'orbit.mp4')],check=True)
        dump(folder/'files.json',{'status':'unaccepted Pixal diagnostic','frontAxisCameraOffset':180,'frames':[{'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(folder.glob('[0-9][0-9][0-9][0-9].png'))],'boardSHA256':sha(folder/'board.png'),'inputSHA256':sha(model)})
        models.append({'tier':tier,'manifestSHA256':sha(folder/'manifest.json'),'boardSHA256':sha(folder/'board.png')})
    dump(base/'model-render.json',{'design':design,'engine':'pixal','tiers':models,'status':'parent review pending'})
    print('Pixal rendered',design,flush=True)
