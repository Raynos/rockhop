"""Check rest vertex links without loading/posing a scene or welding geometry."""
import collections,hashlib,json
from pathlib import Path
import numpy as np
out=Path(__file__).resolve().parent;source=out.parent/'body52/native-fields.npz';n=np.load(source);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check(vertices,triangles):
 links=[[] for _ in range(vertices)]
 for a,b,c in triangles:
  links[a].append((int(b),int(c)));links[b].append((int(c),int(a)));links[c].append((int(a),int(b)))
 bad=[];isolated=[];boundary=[]
 for v,edges in enumerate(links):
  if not edges:isolated.append(v);continue
  graph=collections.defaultdict(list)
  for a,b in edges:graph[a].append(b);graph[b].append(a)
  seen=set();todo=[next(iter(graph))]
  while todo:
   current=todo.pop()
   if current in seen:continue
   seen.add(current);todo.extend(graph[current])
  connected=len(seen)==len(graph);degrees=collections.Counter(len(x) for x in graph.values())
  if connected and degrees=={2:len(graph)}:continue
  if connected and degrees.get(1)==2 and all(k in [1,2] for k in degrees):boundary.append(v);continue
  bad.append({'vertex':v,'linkVertices':len(graph),'connectedLinkVertices':len(seen),'linkDegreeDistribution':dict(degrees)})
 return {'vertices':vertices,'triangles':len(triangles),'nonManifoldVertexLinks':bad,'boundaryVertexLinks':len(boundary),'isolatedVertices':isolated,'closedCycleVertexLinks':vertices-len(bad)-len(boundary)-len(isolated)}
results={}
for label in ['canonicalFour','renderedBody','protectedHead','cheek']:
 xyz=n[label+'XYZ'];tri=n[label+'Triangles'];results[label]={'raw':check(len(xyz),tri)}
 unique,aliases=np.unique(xyz,axis=0,return_inverse=True);results[label]['virtualExactPositionAlias']=check(len(unique),aliases[tri])
assert not results['canonicalFour']['raw']['nonManifoldVertexLinks'] and not results['canonicalFour']['raw']['boundaryVertexLinks'] and not results['canonicalFour']['raw']['isolatedVertices']
report={'status':'READ_ONLY_REST_VERTEX_LINK_TOPOLOGY_VERIFIED','sourceSHA256':sha(source),'recipeSHA256':sha(Path(__file__)),'parts':results,'limits':['Exact position aliases are a metrology view; no topology or source geometry is welded. Native generated-head link defects under virtual aliases do not establish complete oriented export ancestry or justify automatic repair.']};(out/'topology-links.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:{domain:{'nonManifold':len(x['nonManifoldVertexLinks']),'boundary':x['boundaryVertexLinks'],'isolated':len(x['isolatedVertices'])} for domain,x in v.items()} for k,v in results.items()}))
