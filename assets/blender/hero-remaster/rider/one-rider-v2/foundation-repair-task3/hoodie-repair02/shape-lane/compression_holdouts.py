from pathlib import Path
import sys,json,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));from base import *
from differential_cage import Cage
from local_triangle_corrective import LocalTriangleCorrective
OUT=Path(__file__).parent;cage=Cage();edit=LocalTriangleCorrective();rows=[]
for kind,t in [('raise',.125),('raise',.375),('raise',.625),('raise',.875),('sit',.25),('sit',.75)]:
 D=raise_pose(t)if kind=='raise'else sit_pose(t,natural=True);p,m=cage.target(D);q,cm=edit.target(p);np.savez(OUT/f'compression-holdout-{kind}-{t}.npz',**{f'p{i}':v for i,v in enumerate(q)},matrices=D);r={'pose':kind,'t':t,'cage':m,'contact':cm};rows.append(r);print(r,flush=True)
(OUT/'compression-holdout-provenance.json').write_text(json.dumps({'poses':rows,'neckCoupling':'New sit_pose natural reads current .2/.2 coupledneck base source; Tprobes unaffected. Matrices stored exactly in eachNPZ.','independence':'Four interkeyarmraises andtwounseen quarter/ridingstates; differentfractionsfrom8initialfitprobes. Deterministicmemoryless edit no warmstart. Not fullcontinuous/CCD.'},indent=2))
