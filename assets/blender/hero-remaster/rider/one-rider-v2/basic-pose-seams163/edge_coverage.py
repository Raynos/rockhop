"""Read-only winding/facing check of the actual two incident source triangles."""
from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/basic-pose-seams163');OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/basic-pose-seams163');raw=(ROOT/'raw-seam-input.json').read_bytes();x=json.loads(raw);edges=[]
for mi,scope in enumerate(x['scopes']):
 P=np.array(x['meshes'][mi]['attrs']['POSITION']);r={}
 for face,sourceID in zip(scope['triangles'],scope['sourceTriangleIDs']):
  for lane in range(3):
   a,b=face[lane],face[(lane+1)%3];q=tuple(P[a]);s=tuple(P[b]);key=tuple(sorted((q,s)));r.setdefault(key,[]).append({'directedPositionEdge':(q,s),'vertexIDs':face,'sourceTriangleID':sourceID,'oppositeVertex':face[(lane+2)%3]})
 edges.append(r)
rows=[]
for seam in x['matchedBoundaryEdges']:
 ga,gb=seam['endpointGroups'];pa=np.array(x['groups'][ga]['position']);pb=np.array(x['groups'][gb]['position']);key=tuple(sorted((tuple(pa),tuple(pb))));body=edges[0][key];glove=edges[1][key];assert len(body)==len(glove)==1;a=body[0];b=glove[0];opposite=a['directedPositionEdge']==tuple(reversed(b['directedPositionEdge']));normals=[];away=[]
 for mi,r in enumerate([a,b]):
  points=np.array(x['meshes'][mi]['attrs']['POSITION'])[r['vertexIDs']];n=np.cross(points[1]-points[0],points[2]-points[0]);n/=max(np.linalg.norm(n),1e-20);normals.append(n);point=np.array(x['meshes'][mi]['attrs']['POSITION'])[r['oppositeVertex']];axis=(pb-pa)/np.linalg.norm(pb-pa);d=point-pa;d-=np.dot(d,axis)*axis;d/=max(np.linalg.norm(d),1e-20);away.append(d)
 rows.append({'endpointGroups':[ga,gb],'bodyTriangleSourceID':a['sourceTriangleID'],'gloveTriangleSourceID':b['sourceTriangleID'],'bodyTriangleVertexIDs':a['vertexIDs'],'gloveTriangleVertexIDs':b['vertexIDs'],'oppositeBoundaryWinding':opposite,'adjacentFaceNormalDot':float(np.dot(*normals)),'edgePerpendicularAwayDirectionDot':float(np.dot(*away))})
r={'kind':'Literal1cloth+1glove incident triangle winding/facing audit; not whole surface intersection test','sourceSHA256':x['sourceSHA256'],'rawInputSHA256':hashlib.sha256(raw).hexdigest(),'edges':len(rows),'oppositeWindingEdges':sum(r['oppositeBoundaryWinding'] for r in rows),'sameWindingEdges':sum(not r['oppositeBoundaryWinding'] for r in rows),'minimumAdjacentFaceNormalDot':min(r['adjacentFaceNormalDot'] for r in rows),'maximumEdgeAwayDirectionDot':max(r['edgePerpendicularAwayDirectionDot'] for r in rows),'rows':rows,'limits':['Opposite winding withmatchingphysicaledge incidence establishes orientablejoinedboundarycoverage. It doesnotproveadjacentfacesarerenderedseamless orfreeofselfintersection/thickness.','Positive awaydirectionDot meansincidentfacesarefoldedtosamesideinrest; notanindependentpenetrationcertificate.','Rest adjacentfaces only; moving intersections/coplanar overlaps inaccessiblewithoutfurthercollisionaudit andvisualreview.']};(OUT/'incident-edge-coverage.json').write_text(json.dumps(r,indent=2)+'\n');print({k:v for k,v in r.items() if k not in ['rows','limits']})
