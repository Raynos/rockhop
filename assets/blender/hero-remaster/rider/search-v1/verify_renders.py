"""Independent read-only frame, source, native export and movie verification."""
from pathlib import Path
import hashlib,json,subprocess,struct
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'rendered'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
def export_count(p):
 data=p.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size])
 return sum(doc['accessors'][q['indices']]['count']//3 for mesh in doc.get('meshes',[]) for q in mesh['primitives'])
for engine in ['hunyuan','trellis']:
 inventory=json.loads((ROOT/f'{engine}-files.json').read_text())
 assert all(sha(Path(f['path']))==f['sha256'] for f in inventory['files'])
for engine in ['hunyuan','trellis']:
 for i in range(1,6):
  stem=f'{i:02d}';base=OUT/engine/stem
  if not (base/'model-render.json').exists():continue
  raw=json.loads((ROOT/engine/f'{stem}.json').read_text())
  for tier,n in [('working',36),('reduced',9),('native-gray',9)]:
   folder=base/tier;m=json.loads((folder/'manifest.json').read_text());f=json.loads((folder/'files.json').read_text())
   assert len(m['views'])==n and len(f['frames'])==n
   assert m['inputSHA256']==sha(Path(m['input']))
   assert f['manifestSHA256']==sha(folder/'manifest.json')
   assert len(list(folder.glob('[0-9][0-9][0-9][0-9].png')))==n
   assert all(abs(v['yaw']-k*360/n)<1e-10 for k,v in enumerate(m['views']))
   assert all(sha(Path(v['path']))==v['sha256'] for v in f['frames'])
   assert sha(Path(f['board']['path']))==f['board']['sha256']
   native_delta=None
   if tier=='native-gray':
    archive=ROOT/engine/(f'{stem}.raw-shape.npz' if engine=='hunyuan' else f'{stem}.npz')
    native_data=np.load(archive);faces=native_data['faces']
    repeated=(faces[:,0]==faces[:,1])|(faces[:,1]==faces[:,2])|(faces[:,0]==faces[:,2])
    native_delta=raw['raw_faces']-m['triangles']
    assert native_delta==int(repeated.sum())
   if tier=='working':
    result=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames,r_frame_rate,width,height','-of','json',str(folder/'orbit.mp4')],text=True))
    stream=result['streams'][0];assert int(stream['nb_read_frames'])==36 and stream['r_frame_rate']=='12/1'
   rows.append({'engine':engine,'design':stem,'tier':tier,'frames':n,'shaAndYawVerified':True,'triangles':m['triangles'],'nativeSourceFaces':raw['raw_faces'] if tier=='native-gray' else None,'nativeExportFaces':export_count(Path(m['input'])) if tier=='native-gray' else None,'importerDiscardedRepeatedIndexFaces':native_delta,'manifestSHA256':sha(folder/'manifest.json')})
  if engine=='trellis':
   d=np.load(ROOT/engine/f'{stem}.npz');v=d['vertices'];expected=v.copy();expected[:,1],expected[:,2]=v[:,2],-v[:,1]
   mesh=trimesh.load(base/'native-gray/native.glb',force='mesh',process=False)
   assert np.array_equal(mesh.vertices,expected) and np.array_equal(mesh.faces,d['faces'])
report={'status':'verified artifacts only; parent visual review pending','completeModels':len(rows)//3,'completeTiers':len(rows),'frames':sum(r['frames'] for r in rows),'results':rows,'allFrozenSourceHashesIntact':True,'trellisNativeCoordinateAndIndexEquality':True,'limits':['Geometry, anatomy and visual acceptance are not asserted','Native HY source retains2/4/6/0/2 repeated-index zero-area faces; Blender discards those during diagnostic import','Static turntable not gameplay','Render timing not a benchmark']}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
