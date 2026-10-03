from pathlib import Path
import sys,numpy as np,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
from target_arm_plane_rejected import target
OUT=Path(__file__).parent;rig=np.load(ROOT/'hoodie-repair02/rig-lane/anatomical-weights.npz');weights=[rig[f'W{i}']for i in range(5)];r=np.load(OUT/'envelope-rest.npz');positions=[r[f'p{i}']for i in range(5)];rows=[]
for kind,t in [('raise',0),('raise',.25),('raise',.5),('raise',.75),('raise',1),('sit',0),('sit',.5),('sit',1)]:
 D=raise_pose(t)if kind=='raise'else sit_pose(t,natural=True);p,m=target(positions,weights,D,POS,P);np.savez(OUT/f'generic-{kind}-{t}.npz',**{f'p{i}':v for i,v in enumerate(p)},matrices=D);m.update(pose=kind,t=t);rows.append(m);print(m,flush=True)
(OUT/'generic-target-provenance.json').write_text(json.dumps(rows,indent=2))
