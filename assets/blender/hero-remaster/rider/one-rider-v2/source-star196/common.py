"""Pinned source readers and predicates only. Never executes a foreign recipe."""
from pathlib import Path
from collections import defaultdict, Counter
from fractions import Fraction as Q
import ast, copy, hashlib, json, math, os, re, struct, subprocess, sys, time
import numpy as np
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/games/rockhop')
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
A=R/'assets/blender/hero-remaster/rider/one-rider-v2/source-star196'
E=R/'docs/evidence/hero-remaster/one-rider-v2/source-star196'
S=B/'source-star196'
SOURCE=B/'source-preserving-garment185/operator/rider.glb'
SHA='ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
CONTRACT=R/'docs/evidence/hero-remaster/one-rider-v2/extrinsic-seam195/parent-construction-contract.json'
start=time.monotonic();pins={};mem=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(p,v):
 Path(p).write_text(json.dumps(v,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist() if isinstance(x,np.ndarray) else str(x))+'\n')
def pin(p,expected=None):
 p=Path(p);raw=p.read_bytes();h=sha(raw);assert expected is None or h==expected,(p,h,expected);pins[str(p)]={'sha256':h,'bytes':len(raw)};return raw

def check():
 assert time.monotonic()-start<1750,'30 minute CPU batch watchdog'
 v=subprocess.check_output(['vm_stat'],text=True);pg=int(re.search(r'page size of (\d+)',v).group(1));gb=int(re.search(r'Anonymous pages:\s+(\d+)',v).group(1))*pg/1e9;assert gb<70;mem.append(gb)

def selected(p,names):
 tree=ast.parse(pin(p));nodes=[x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name in names];assert {x.name for x in nodes}==names;exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),globals())
selected(R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment185/operator.py',{'GLB','strict','projected','edges'})
selected(R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment185/coplanar-source/audit.py',{'sub','c2','c3','dot','rational_triangle','clip_exact'})
selected(R/'assets/blender/hero-remaster/rider/one-rider-v2/source-ruled194/verify.py',{'topology'})

def source():
 check();pin(SOURCE,SHA);C=GLB(SOURCE,SHA);a,F=C.primitive(0,0);U,q=np.unique(a['POSITION'],axis=0,return_inverse=True)
 c=json.loads(pin(CONTRACT));assert c['source185SHA256']==SHA and c['trialLimit']==1
 frozen=R/'docs/evidence/hero-remaster/one-rider-v2/extrinsic-seam195'
 alias=json.loads(pin(frozen/'source-interior-aliases.json'));graph=json.loads(pin(frozen/'source-star-graph.json'))
 pin(frozen/'prospective-contract.json',c['prospectiveContractSHA256']);pin(frozen/'parent-review.json',c['parentReviewSHA256'])
 star=json.loads(pin(R/'docs/evidence/hero-remaster/one-rider-v2/physical-cut193/parent-review.json'));path=json.loads(pin(B/'source-seam191/next-construction-contract.json'))['orderedProspectiveSeamPhysicalIDs']
 sep=json.loads(pin(B/'physical-cut193/literal-separator.json'))
 assert len(path)==45 and set(path)|{4041}==set(c['exactReleasedInteriorPhysicalIDs'])
 assert len(star['removedSourceFaceIDs'])==168 and len(star['orientedFillBoundaryPhysicalIDs'])==78
 return C,a,F,U,q,c,alias,graph,star,path,sep
