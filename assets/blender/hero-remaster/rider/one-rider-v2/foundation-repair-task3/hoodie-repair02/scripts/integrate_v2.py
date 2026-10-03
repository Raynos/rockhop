from base import *
import shutil,hashlib
# Freeze teammate outputs before integrating; later lane work cannot silently change this variant.
shutil.copyfile(OUT/'shape-lane/shoulder-only.npz',OUT/'v2-shoulder-input.npz');shutil.copyfile(OUT/'rig-lane/anatomical-weights.npz',OUT/'v2-weight-input.npz')
b=np.load(OUT/'v2-shoulder-input.npz');new=[b[f'p{i}'].copy()for i in range(5)];nw=np.load(OUT/'v2-weight-input.npz');weights=[nw[f'W{i}'].copy()for i in range(5)]
for i in [0,2]:
 p=POS[i];y=p[:,1];z=abs(p[:,2]);x=p[:,0];ease=smooth((y-1.08)/.12)*smooth((1.49-y)/.15)*smooth((.215-z)/.08)*smooth((x-.65)/.12);new[i][:,0]-=.027*ease
np.savez(OUT/'v2-bind.npz',**{f'p{i}':p for i,p in enumerate(new)},**{f'W{i}':w for i,w in enumerate(weights)})
for layer,pos,w,natural in [('control',POS,W,False),('shape',new,W,False),('weights',new,weights,False),('posture',new,weights,True)]:
 for kind,t in [('rest',0),('raise',.5),('raise',1),('sit',0),('sit',.5),('sit',1)]:
  D=raise_pose(t)if kind=='raise'else sit_pose(t,natural)if kind=='sit'else np.repeat(np.eye(4)[None],N,axis=0);points=deform(pos,w,D,kind=='sit');np.savez(OUT/'poses'/f'v2-{layer}-{kind}-{t}.npz',**{f'p{i}':q for i,q in enumerate(points)},matrices=D)
for k in range(49):
 for layer,pos,w,natural in [('control',POS,W,False),('posture',new,weights,True)]:
  D=sit_pose(k/48,natural);points=deform(pos,w,D,True);np.savez(OUT/'poses'/f'v2-movie-{layer}-{k:03d}.npz',**{f'p{i}':q for i,q in enumerate(points)},matrices=D)
(OUT/'v2-provenance.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(G.raw).hexdigest(),'headGeometryExact':all(np.array_equal(new[i],POS[i])for i in [3,4]),'handGeometryExact':np.array_equal(new[1],POS[1]),'weightsInputSHA256':hashlib.sha256((OUT/'v2-weight-input.npz').read_bytes()).hexdigest(),'shoulderInputSHA256':hashlib.sha256((OUT/'v2-shoulder-input.npz').read_bytes()).hexdigest(),'chestEaseMaxM':.027,'neckForwardFractionOfTorsoAngle':.30,'headForwardFractionOfTorsoAngle':.10,'restGussetLift':False,'correctiveTargets':False,'scope':'First integrated foundation progress; not accepted T-pose or whole sitting repair.'},indent=2));print('V2 INTEGRATED')
