from pathlib import Path
import sys,json,hashlib,numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');OUT=ROOT/'hoodie-repair03';sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
sys.path.insert(0,str(ROOT/'hoodie-repair02/rig-lane/mechanical-suite'));from source34 import source34_world_matrices
sys.path.insert(0,str(ROOT/'hoodie-repair02/shape-lane'));from compression_target import CompressionTarget
sys.path.insert(0,str(ROOT/'hoodie-repair02/shape-lane/volume-lane'));from surface_slide import TorsoSurfaceSlide
OUT=ROOT/'hoodie-repair03';(OUT/'evidence').mkdir(exist_ok=True,parents=True)
D,prov=source34_world_matrices(304);b=np.load(ROOT/'hoodie-repair02/v7-bind.npz');pp=[b[f'p{i}']for i in range(5)];ww=[b[f'W{i}']for i in range(5)];tri=[b[f'tr{i}']for i in range(5)];(OUT/'poses').mkdir(exist_ok=True)
# Exact same actual gameplay matrices and source original closed-grip morphs.
variants={'source':deform(POS,W,D,True),'v7-plain':deform(pp,ww,D,True)}
method=CompressionTarget();variants['v7-cage'],meta=method.target(D,posed=deform(method.cage.pos,method.cage.w,D,True))
slide=TorsoSurfaceSlide();variants['volume-slide'],sm=slide.target(D,posed=deform(pp,ww,D,True))
rows=[]
for name,pts in variants.items():
 file=OUT/'poses'/f'game304-{name}.npz';np.savez(file,**{f'p{i}':p for i,p in enumerate(pts)},**{f'tr{i}':t for i,t in enumerate(TRI if name=='source'else tri)},matrices=D)
 rows.append({'variant':name,'probe':'actualbody34frame304-reference','fraction':1,'path':str(file)})
prov.update({'screenshotExactMeshIdentity':'unconfirmed; source34side304 is closest camera/time reference','sameGameWorldMatrices':True,'primitiveMatricesDelta':max(float(abs(source34_world_matrices(304,primitive=i)[0]-D).max())for i in range(len(json.loads(Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34/candidate-cpu/pose-manifest.json').read_text())['primitives']))),'compression':meta,'slide':sm,'originalGripMorphsApplied':True,'rows':rows,'productionApproved':False})
(OUT/'evidence/game304-preparation.json').write_text(json.dumps(prov,indent=2)+'\n');(OUT/'evidence/game304-manifest.json').write_text(json.dumps({'topology_path':str(ROOT/'hoodie-repair02/v7-bind.npz'),'rows':rows[1:]},indent=2)+'\n');(OUT/'evidence/game304-source-manifest.json').write_text(json.dumps({'rows':rows[:1]},indent=2)+'\n');print(json.dumps({'cage':meta,'slide':sm,'primitiveMatrixDelta':prov['primitiveMatricesDelta']},indent=2))
