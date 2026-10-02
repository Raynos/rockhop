"""Pinned readers/predicates only; importing never invokes a foreign recipe."""
from pathlib import Path
from collections import defaultdict, Counter
from fractions import Fraction as Q
import ast, copy, math, hashlib, json, os, re, struct, subprocess, time
import numpy as np
from scipy.spatial import cKDTree
R=Path('/Users/raynos/projects/games/rockhop')
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E=R/'docs/evidence/hero-remaster/one-rider-v2/source-ruled194'
S=B/'source-ruled194'
SOURCE=B/'source-preserving-garment185/operator/rider.glb'
SHA='ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
sha=lambda b:hashlib.sha256(b).hexdigest()
pins={};start=time.monotonic();mem=[]
def pin(p,h=None):
 p=Path(p);b=p.read_bytes();v=sha(b);assert h is None or v==h,(p,v,h);pins[str(p)]={'sha256':v,'bytes':len(b)};return b

def save(p,v):
 Path(p).write_text(json.dumps(v,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n')

def check():
 assert time.monotonic()-start<890,'CPU batch watchdog'
 v=subprocess.check_output(['vm_stat'],text=True);page=int(re.search(r'page size of (\d+)',v).group(1));gb=int(re.search(r'Anonymous pages:\s+(\d+)',v).group(1))*page/1e9;assert gb<70;mem.append(gb);return gb

for path,names in [(R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment185/operator.py',{'GLB','strict','projected','edges'}),(R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment185/coplanar-source/audit.py',{'sub','c2','c3','dot','rational_triangle','clip_exact'})]:
 tree=ast.parse(pin(path));nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names];assert {n.name for n in nodes}==names;exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),globals())

def bary(p,t):
 den=c2(sub(t[1],t[0]),sub(t[2],t[0]));b=c2(sub(p,t[0]),sub(t[2],t[0]))/den;c=c2(sub(t[1],t[0]),sub(p,t[0]))/den;return (1-b-c,b,c)

def blend(v,w):return tuple(sum(w[i]*v[i][k] for i in range(3)) for k in range(len(v[0])))
def encode(p):return [[str(x.numerator),str(x.denominator)] for x in p]
def source():
 check();pin(SOURCE,SHA);C=GLB(SOURCE,SHA);a,F=C.primitive(0,0);U,q=np.unique(a['POSITION'],axis=0,return_inverse=True)
 c=json.loads(pin(R/'docs/evidence/hero-remaster/one-rider-v2/physical-cut193/parent-construction-contract.json'))
 attempt=json.loads(pin(E/'attempt.json'));assert attempt['contractSHA256']==pins[attempt['contractPath']]['sha256']
 inv=json.loads(pin(B/'source-seam191/literal-inventory.json'));charts={fi:int(x['id']) for x in inv['UVChartsTouchingScope'] for fi in x['sourceFaceIDs']}
 comparison=json.loads(pin(B/'physical-cut193/domain-source-comparison.json'))['physicalMincut47'];sep=json.loads(pin(B/'physical-cut193/literal-separator.json'))
 ref={}
 for name,sign in [('central',-1),('lateral',1)]:
  arc=c['arcCorrespondence'][name]
  for pid,u in zip(arc['physicalIDs'],arc['normalizedSourceArcLengthStations']):ref[pid]=(Q(u),Q(0.0 if u in [0.,1.] else sign*math.sin(math.pi*u)))
 removed=c['exactRemovedSourceFaceIDs'];refs={fi:tuple(ref[int(pid)] for pid in q[F[fi]]) for fi in removed};assert all(c2(sub(t[1],t[0]),sub(t[2],t[0]))>0 for t in refs.values())
 return C,a,F,U,q,c,charts,comparison,sep,refs
