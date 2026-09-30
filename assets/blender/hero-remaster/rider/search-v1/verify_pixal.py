from pathlib import Path
import hashlib,json,subprocess
import numpy as np
import trimesh

ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
report={'status':'artifact integrity only; parent anatomy review pending','subjects':[],'limits':['No rig, motion, physics, contact or phone acceptance','Pixal generation resolution/export remeshing differs from frozen TRELLIS lane']}
for i in range(1,6):
    design=f'{i:02d}';source=ROOT/'pixal'/design;base=ROOT/'rendered/pixal'/design
    result=json.loads((source/'result.json').read_text())
    for name,r in result['files'].items():assert sha(source/name)==r['sha256']
    d=np.load(source/'native.npz');v=d['vertices'].copy();v[:,0]*=-1;v[:,2]*=-1
    native=trimesh.load(base/'native.glb',process=False,force='mesh')
    assert np.array_equal(native.faces,d['faces']) and np.array_equal(native.vertices,v)
    records=[]
    for tier,n in [('working',36),('reduced',9),('native-gray',9)]:
        folder=base/tier;m=json.loads((folder/'manifest.json').read_text());f=json.loads((folder/'files.json').read_text())
        assert len(m['views'])==len(f['frames'])==n
        for k,(view,frame) in enumerate(zip(m['views'],f['frames'])):
            assert abs(view['yaw']-180-k*360/n)<1e-10
            assert sha(folder/frame['file'])==frame['sha256']
        assert sha(folder/'board.png')==f['boardSHA256']
        if tier=='working':
            video=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames,r_frame_rate','-of','json',str(folder/'orbit.mp4')],text=True))['streams'][0]
            assert video['nb_read_frames']=='36' and video['r_frame_rate']=='12/1'
        if tier=='native-gray':assert m['triangles']==len(d['faces'])
        records.append({'tier':tier,'frames':n,'triangles':m['triangles'],'inputSHA256':m['inputSHA256']})
    report['subjects'].append({'id':design,'nativeFaces':len(d['faces']),'exactNativeVerticesAndIndicesAfterRecordedAxisConversion':True,'tiers':records})
(ROOT/'rendered/pixal/verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Five Pixal inputs/outputs,270 frames,15 boards and5 complete orbits verified')
