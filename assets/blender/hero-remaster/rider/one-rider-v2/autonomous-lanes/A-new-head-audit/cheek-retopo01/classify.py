"""Read-only physical triangle components and cheek boundary provenance."""
import bpy,json,hashlib,collections
from pathlib import Path
S=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit/generation/h21-buzz-native01/model.glb')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01/cheek-retopo01')
O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if (O/'classification.json').exists():raise RuntimeError('Frozen classification exists')
digest=sha(S);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(S));obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh=obj.data
positionIDs={};positions=[];mapping=[]
for v in mesh.vertices:
 key=tuple(v.co)
 if key not in positionIDs:positionIDs[key]=len(positions);positions.append(key)
 mapping.append(positionIDs[key])
edges=collections.defaultdict(list);faces=[];uv=mesh.uv_layers.active
for face in mesh.polygons:
 indices=[mapping[v] for v in face.vertices];faces.append(indices)
 for n in range(3):
  a,b=indices[n],indices[(n+1)%3];edges[tuple(sorted((a,b)))].append({'face':face.index,'a':a,'b':b,'sourceVertexA':face.vertices[n],'sourceVertexB':face.vertices[(n+1)%3],'uvA':list(uv.data[face.loop_indices[n]].uv),'uvB':list(uv.data[face.loop_indices[(n+1)%3]].uv)})
parents=list(range(len(faces)))
def root(x):
 while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
 return x
for incidence in edges.values():
 for row in incidence[1:]:a=root(row['face']);b=root(incidence[0]['face']);parents[a]=b
components=collections.defaultdict(list)
for i in range(len(faces)):components[root(i)].append(i)
componentIDs={face:n for n,values in enumerate(sorted(components.values(),key=len,reverse=True)) for face in values}
boundary={key:rows[0] for key,rows in edges.items() if len(rows)==1};adj=collections.defaultdict(list)
for a,b in boundary:adj[a].append(b);adj[b].append(a)
unseen=set(boundary);circuits=[]
while unseen:
 seed=next(iter(unseen));walk=[seed[0]];current=seed[0];previous=None;rows=[]
 for _ in range(len(boundary)+1):
  if len(adj[current])!=2:raise RuntimeError('Non-degree-two boundary')
  nextVertex=next(v for v in adj[current] if v!=previous)
  edge=tuple(sorted((current,nextVertex)));unseen.discard(edge);rows.append(boundary[edge]);previous,current=current,nextVertex
  if current==walk[0]:break
  walk.append(current)
 else:raise RuntimeError('Boundary did not close')
 coords=[positions[v] for v in walk]
 circuits.append({'vertices':walk,'vertexCount':len(walk),'positionBounds':[[min(p[k] for p in coords) for k in range(3)],[max(p[k] for p in coords) for k in range(3)]],'faceComponents':sorted(set(componentIDs[row['face']] for row in rows)),'sourceFaces':[row['face'] for row in rows],'boundaryHalfedges':rows})
counts=[{'id':n,'faceCount':len(values),'sourceFaceIndices':values if len(values)<200 else None} for n,values in enumerate(sorted(components.values(),key=len,reverse=True))]
images=[{'material':m.name,'image':n.image.name,'size':list(n.image.size),'node':n.name} for m in mesh.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
report={'status':'UNACCEPTED read-only physical adjacency classification','source':str(S),'sourceSHA256':digest,'sourceSHA256After':sha(S),'recipeSHA256':sha(Path(__file__)),'mesh':obj.name,'sourceVertices':len(mesh.vertices),'sourceFaces':len(faces),'exactPositionUniqueVertices':len(positions),'positionWeldTolerance':0,'componentCount':len(counts),'components':counts,'circuits':circuits,'edgeIncidenceAbove2':sum(len(v)>2 for v in edges.values()),'images':images,'limits':['Exact position coincidence used for diagnosis of UV-split geometry only; original indices/UV/materials untouched.','This output does not fill openings or accept component removal.']}
assert sha(S)==digest
(O/'classification.json').open('x').write(json.dumps(report,indent=2)+'\n');print('CLASSIFICATION_FROZEN',[(row['id'],row['faceCount']) for row in counts],[(r['vertexCount'],r['faceComponents']) for r in circuits],flush=True)
