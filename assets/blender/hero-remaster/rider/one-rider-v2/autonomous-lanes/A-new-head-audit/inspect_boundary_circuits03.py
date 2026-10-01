"""Read-only connected circuits from frozen cheek forensic segments, CPU only."""
import json,hashlib
from pathlib import Path
from collections import defaultdict
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01/gray-diagnostic03')
source=O/'cheek-surface-forensic.json';j=json.loads(source.read_text());rows=[]
for variant in j['variants']:
 graph=defaultdict(set)
 for edge in variant['positionDiagnosticBoundarySegmentsNearCheeks']:
  a,b=[tuple(round(x,7) for x in p) for p in edge];graph[a].add(b);graph[b].add(a)
 unseen=set(graph);components=[]
 while unseen:
  todo=[unseen.pop()];seen=set(todo)
  while todo:
   p=todo.pop()
   for q in graph[p]:
    if q not in seen:seen.add(q);unseen.discard(q);todo.append(q)
  components.append({'vertices':len(seen),'degreeCounts':{str(d):sum(len(graph[p])==d for p in seen) for d in set(len(graph[p]) for p in seen)},'bounds':[[min(p[k] for p in seen) for k in range(3)],[max(p[k] for p in seen) for k in range(3)]]})
 rows.append({'variant':variant['label'],'components':components})
(O/'boundary-circuits-forensic.json').open('x').write(json.dumps({'status':'UNACCEPTED read-only guard; no mesh repair','inputSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'recipeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variants':rows,'finding':'Four degree-two circuits: 37/19 left, 38/17 right, preserved across raw/reduced/painted. Inner circuits may bound isolated front islands; do not assume two plain holes.','limits':['Supersedes README provisional two-circuit patch proposal.','Coincidence rounding diagnostic, not closed-volume acceptance.','No source indices or geometry modified.']},indent=2)+'\n')
