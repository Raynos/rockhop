from base import *
import shutil,hashlib
shutil.copyfile(OUT/'shape-lane/shape-retop-uvsafe.npz',OUT/'v4-shape-input.npz');shutil.copyfile(OUT/'rig-lane/weights-ls-corrected.npz',OUT/'v4-weight-input.npz')
b=np.load(OUT/'v4-shape-input.npz');nw=np.load(OUT/'v4-weight-input.npz');pos=[b[f'p{i}']for i in range(5)];weights=[nw[f'W{i}']for i in range(5)];tri=[b[f'tr{i}']for i in range(5)]
np.savez(OUT/'v4-bind.npz',**{f'p{i}':p for i,p in enumerate(pos)},**{f'W{i}':w for i,w in enumerate(weights)},**{f'tr{i}':t for i,t in enumerate(tri)})
for kind,t in [('rest',0),('raise',.5),('raise',1),('sit',0),('sit',.5),('sit',1)]:
 D=raise_pose(t)if kind=='raise'else sit_pose(t,True)if kind=='sit'else np.repeat(np.eye(4)[None],N,axis=0);pts=deform(pos,weights,D,kind=='sit');np.savez(OUT/'poses'/f'v4-{kind}-{t}.npz',**{f'p{i}':q for i,q in enumerate(pts)},**{f'tr{i}':q for i,q in enumerate(tri)},matrices=D)
for k in range(49):
 for label,ps,ws,natural in [('control',POS,W,False),('candidate',pos,weights,True)]:
  D=sit_pose(k/48,natural);pts=deform(ps,ws,D,True);np.savez(OUT/'poses'/f'v4-movie-{label}-{k:03d}.npz',**{f'p{i}':q for i,q in enumerate(pts)},**{f'tr{i}':q for i,q in enumerate(tri if natural else TRI)},matrices=D)
(OUT/'v4-provenance.json').write_text(json.dumps({'controlSHA256':hashlib.sha256(G.raw).hexdigest(),'shapeSHA256':hashlib.sha256((OUT/'v4-shape-input.npz').read_bytes()).hexdigest(),'weightsSHA256':hashlib.sha256((OUT/'v4-weight-input.npz').read_bytes()).hexdigest(),'neckAngleFraction':.30,'headAngleFraction':.10,'correctives':False,'same19BoneBind':True,'productionApproved':False},indent=2))
print('v4 frozen')
