"""Pose-dependent geometric underarm cage. Preserves exact rest and sewn aliases.
Target compresses low generated batwing toward the lower sleeve envelope; does not
claim physical cloth behavior. Float64 output, portable inverse-LBS morph possible.
"""
from pathlib import Path
import sys,numpy as np,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
OUT=Path(__file__).parent;rig=np.load(ROOT/'hoodie-repair02/rig-lane/anatomical-weights.npz');ww=[rig[f'W{i}']for i in range(5)];rest=np.load(OUT/'shoulder-r0.035.npz');pp=[rest[f'p{i}'].copy()for i in range(5)]
# Modest chest rest envelope reduction, independent of skinning/materials.
q=np.array(rest['uniquePositions']);x,y,z=U.T;cloth=np.zeros(len(U),bool);cloth[np.unique(CT)]=True
chest=smooth((y-1.08)/.12)*smooth((1.49-y)/.15)*smooth((.215-abs(z))/.08)*smooth((x-.65)/.12)*cloth
q[:,0]-=.030*chest;pp=[q[INV[OFF[i]:OFF[i+1]]].copy()for i in range(5)]
np.savez(OUT/'envelope-rest.npz',**{f'p{i}':v for i,v in enumerate(pp)})
rows=[]
for t in [0,.25,.5,.75,1]:
 D=raise_pose(t);skin=deform(pp,ww,D);allp=np.concatenate(skin);world=np.zeros_like(U);np.add.at(world,INV,allp);world/=np.bincount(INV)[:,None];target=world.copy();alter=np.zeros(len(U),bool)
 for sg,a in [(1,6),(-1,10)]:
  sy=world[:,1];sz=world[:,2]*sg;rot=D[a,:3,:3];v=rot@(P[a+1]-P[a]);slope=v[1]/max(v[2]*sg,.025)
  # Lower envelope is a round underarm junction, then the actual authored sleeve
  # centreline minus 70mm garment radius. No flattened outer sleeve/global gussetlift.
  sleeveFloor=P[a,1]+(sz-abs(P[a,2]))*slope-.075
  blend=smooth((sz-.205)/.075)*smooth((.82-sz)/.13)
  depth=np.maximum(sleeveFloor-sy,0)
  # Complete T: 85% compression of the excessive low panel depth. Side torso below
  # z=.205 is held, sleeves already above the floor get zero corrective.
  lift=.85*depth*blend*smooth(t)*cloth*(U[:,2]*sg>0)*smooth((U[:,1]-1.105)/.055)*smooth((1.49-U[:,1])/.045)
  target[:,1]+=lift;alter|=lift>1e-9
 out=[skin[i]+(target-world)[INV[OFF[i]:OFF[i+1]]]for i in range(5)]
 np.savez(OUT/f'raise-target-{t}.npz',**{f'p{i}':v for i,v in enumerate(out)},matrices=D,**{f'control{i}':v for i,v in enumerate(skin)})
 disp=np.linalg.norm(target-world,axis=1);rows.append({'t':t,'changedUnique':int(alter.sum()),'maxPosedCorrectionM':float(disp.max()),'headExact':all(np.array_equal(out[i],skin[i])for i in [3,4]),'handsExact':np.array_equal(out[1],skin[1]),'notes':'Posed morph target only. Must assess triangles and visible sleeve radius. No rest gusset lift.'});print(rows[-1],flush=True)
(OUT/'pose-target-provenance.json').write_text(json.dumps({'sourceSHA256':'186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e','ownershipFile':str(ROOT/'hoodie-repair02/rig-lane/anatomical-weights.npz'),'rows':rows,'method':'Monotone upward compression of generated underarm low depth toward rotated sleeve centreline lower envelope, z-side activation holds torso. No meshes detached; all exact source seam aliases move together. Chest rest reduction30mm. Candidate only, not acceptance.'},indent=2))
