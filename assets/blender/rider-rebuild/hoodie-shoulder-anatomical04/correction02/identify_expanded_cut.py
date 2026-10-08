"""Readonly connected seam scope: consume penetrating boundary vertex stars.
No positions change, no geometry/native save, no fitting or parameter search.
"""
import ast,collections,hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[5]
def main():
 d=np.load(ROOT/'harness/out/rider-rebuild/hoodie-shoulder-anatomical04/correction02-intake01/saved-panels.npz');c=json.loads((ROOT/'assets/blender/rider-rebuild/hoodie-shoulder-anatomical04/panel-controls.json').read_text())
 tree=ast.parse((Path(__file__).parent/'diagnose_saved_arrays.py').read_text());scope={'np':np};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='inside'],type_ignores=[]),'readonly-body-parity','exec'),scope)
 faces=[d['cornerVertexIds'][s:s+n].tolist()for s,n in zip(d['polygonStarts'],d['polygonCounts'])];edgefaces=collections.defaultdict(list);vertexfaces=collections.defaultdict(set)
 for fi,vs in enumerate(faces):
  for v in vs:vertexfaces[v].add(fi)
  for a,b in zip(vs,vs[1:]+vs[:1]):edgefaces[tuple(sorted((a,b)))].append(fi)
 of=d['_panel04_original_face_id'];side=d['_panel04_side'];cache={};reports=[]
 for label,value in (('L',1),('R',2)):
  original={f for comp in c['components']if comp['side']==label for ring in comp['adjacentFaces']for f in ring}
  selected={fi for fi,old in enumerate(of)if old in original or(old==-1 and side[fi]==value)};seedcount=len(selected);rounds=[]
  while True:
   edges=[edge for edge,fs in edgefaces.items()if sum(fi in selected for fi in fs)==1];boundary=sorted({v for edge in edges for v in edge});unknown=[v for v in boundary if v not in cache]
   result=scope['inside'](d['vertices'][unknown],d['canonicalBodyVertices'],d['canonicalBodyFaces'])if unknown else []
   cache.update(zip(unknown,map(bool,result)));penetrating=[v for v in boundary if cache[v]];rounds.append({'boundaryVertices':len(boundary),'penetratingBoundaryVertices':penetrating})
   if not penetrating:break
   previous=len(selected)
   for v in penetrating:selected.update(vertexfaces[v])
   assert len(selected)>previous
  outgoing={}
  for fi in selected:
   vs=faces[fi]
   for a,b in zip(vs,vs[1:]+vs[:1]):
    if sum(f in selected for f in edgefaces[tuple(sorted((a,b)))])==1:assert a not in outgoing;outgoing[a]=b
  remaining=set(outgoing);loops=[]
  while remaining:
   start=min(remaining);loop=[start];current=outgoing[start]
   while current!=start:assert current not in loop;loop.append(current);current=outgoing[current]
   remaining-=set(loop);loops.append(loop)
  reports.append({'side':label,'initialFaces':seedcount,'actualExpandedFaceIds':sorted(selected),'expandedFaceCount':len(selected),'topologyScopeRounds':rounds,'orientedBoundaryCycles':loops,'boundaryXYZ':[[d['vertices'][i].tolist()for i in loop]for loop in loops],'allCutBoundaryVerticesOutsideCanonicalBody':True})
 report={'accepted':False,'stage':'CONNECTED_EXPANDED_JOIN_CUT_IDENTIFIED_FROM_ACTUAL_SAVED_TOPOLOGY','actualNativeSHA256':'1ad5c5aa21553bbb3eb84898572200b2d4418e81e1e1995d774a763707f0124f','sides':reports,'limits':['Outside boundary vertex parity supports scope selection, not cloth enclosure.','No garment/body positions changed. This is not a fit, gain search or new native.','New tailoring must allow source join/support reconstruction and true paired shell orientation; no preservation of every failed derivative point.']}
 out=ROOT/'docs/evidence/rider-rebuild/hoodie-shoulder-anatomical04/correction02/expanded-cut.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps([{'side':r['side'],'faces':r['expandedFaceCount'],'boundaryLoops':[len(l)for l in r['orientedBoundaryCycles']],'scopeRounds':len(r['topologyScopeRounds'])}for r in reports]))
if __name__=='__main__':main()
