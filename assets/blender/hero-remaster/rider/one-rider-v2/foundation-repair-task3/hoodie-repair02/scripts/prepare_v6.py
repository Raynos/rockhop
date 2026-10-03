from base import *
import hashlib
sys.path.insert(0,str(OUT/'shape-lane'));from differential_cage import Cage;from local_triangle_corrective import LocalTriangleCorrective;from compression_target import CompressionTarget
method=CompressionTarget();cage=method.cage;rows=[]
for k in range(49):
 D=sit_pose(k/48,True);corrected,mm=method.target(D,posed=deform(cage.pos,cage.w,D,True));cm=mm["cage"];lm=mm["localTriangleCorrective"];file=OUT/'poses'/f'v6-movie-candidate-{k:03d}.npz';np.savez(file,**{f'p{i}':v for i,v in enumerate(corrected)},**{f'tr{i}':tr for i,tr in enumerate(cage.tri)},matrices=D);rows.append({'key':k,'time':k/24,'cage':cm,'local':lm});print(k,lm['finalPairs'],lm['maxAdditionalCorrectionM'],flush=True)
for k,t in enumerate([.137,.371,.613,.887]):
 D=sit_pose(t,True);corrected,mm=method.target(D,posed=deform(cage.pos,cage.w,D,True));cm=mm["cage"];lm=mm["localTriangleCorrective"];np.savez(OUT/'poses'/f'v6-direct-holdout-{k}.npz',**{f'p{i}':v for i,v in enumerate(corrected)},matrices=D)
(OUT/'v6-target-provenance.json').write_text(json.dumps({'sourceGLBSHA256':hashlib.sha256(G.raw).hexdigest(),'restBind':'v5-bind.npz','neckFraction':.2,'headFraction':.2,'headAndGloveRigid':True,'originalClosedGripMorphsApplied':True,'scripts':{n:hashlib.sha256((OUT/'shape-lane'/n).read_bytes()).hexdigest()for n in ['differential_cage.py','local_triangle_corrective.py','compression_target.py']},'rows':rows,'limits':'Offline compression cage and literal local separating corrective. No cloth forces, continuous collision certificate or saddle support; arbitrary blends unqualified.'},indent=2));print('V6 TARGETS COMPLETE')
