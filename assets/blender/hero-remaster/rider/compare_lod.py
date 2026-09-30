"""Report V5→V6 LOD rest-surface approximation changes, without an art verdict."""
import argparse,sys,json,struct,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser();ap.add_argument('--before',required=True);ap.add_argument('--after',required=True);ap.add_argument('--out',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
def read(path):
 b=Path(path).read_bytes();n=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+n]);return d,b[28+n:],hashlib.sha256(b).hexdigest()
def mesh(doc,bin,name):
 node=next(n for n in doc['nodes'] if n.get('name')==name);p=doc['meshes'][node['mesh']]['primitives'][0]
 def acc(ai):
  a=doc['accessors'][ai];v=doc['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];size=struct.calcsize(fmt)*n;offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size)
  return [struct.unpack_from('<'+fmt*n,bin,offset+i*stride) for i in range(a['count'])]
 pos=acc(p['attributes']['POSITION']);indices=[x[0] for x in acc(p['indices'])];tri=[indices[i:i+3] for i in range(0,len(indices),3)];joints=acc(p['attributes']['JOINTS_0']);weights=acc(p['attributes']['WEIGHTS_0']);names=[doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']];head=[names[js[max(range(4),key=lambda j:ws[j])]]=='head' for js,ws in zip(joints,weights)];return pos,tri,head
bd,bb,bsha=read(a.before);ad,ab,asha=read(a.after);bp,bt,bh=mesh(bd,bb,'Street_remaster_neural_full_body');ap,at,ah=mesh(ad,ab,'Street_remaster_neural_full_body')
bvh0=BVHTree.FromPolygons([Vector(p) for p in bp],bt,all_triangles=True);bvh1=BVHTree.FromPolygons([Vector(p) for p in ap],at,all_triangles=True)
def summary(values):
 values=sorted(values);return {'samples':len(values),'medianMetres':values[len(values)//2],'p95Metres':values[min(len(values)-1,int(len(values)*.95))],'maxMetres':max(values)}
def bounds(ps):return {'minimum':[min(p[c] for p in ps) for c in range(3)],'maximum':[max(p[c] for p in ps) for c in range(3)]}
def region(p,name,isHead):
 if name=='head':return isHead
 # The changed body region excludes the original wrist/hand tips.
 if name=='bodyOutsideWrists':return not (.75<p[1]<1.05 and abs(p[2])>.26 and p[0]>.83)
 return True
reports={}
for name in ['wholeBody','bodyOutsideWrists','head']:
 before=[p for p,h in zip(bp,bh) if region(p,name,h)];after=[p for p,h in zip(ap,ah) if region(p,name,h)]
 reports[name]={'beforeBounds':bounds(before),'afterBounds':bounds(after),'beforeToAfter':summary([bvh1.find_nearest(Vector(p))[3] for p in before]),'afterToBefore':summary([bvh0.find_nearest(Vector(p))[3] for p in after])}
report={'before':a.before,'beforeSHA256':bsha,'after':a.after,'afterSHA256':asha,'method':'Bidirectional vertex-to-triangle nearest-surface distances in exact raw glTF rest coordinates; bounded approximation proxy, not a moving visual acceptance claim.','headRegion':'Vertices whose largest skin influence is the head bone, covering the generated face/jaw/crown, excluding separate preserved authored strands.','bodyTrianglesBefore':len(bt),'bodyTrianglesAfter':len(at),'regions':reports,'authoredContactsAndHeadStrands':'byte-identical V5 LOD donor meshes; see clean-lod-source proof','scopeException':'Full-derived body simplified after skin-aware positional welding because original V5 LOD had no closed topological forearm-winding cycle.'}
Path(a.out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
