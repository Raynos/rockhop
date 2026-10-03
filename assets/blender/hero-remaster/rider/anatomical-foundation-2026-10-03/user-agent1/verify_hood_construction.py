"""Measured sewn attachment and unchanged original shirt fields, not art pass."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source',required=True);ap.add_argument('--out',required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,out=Path(a.source).resolve(),Path(a.out).resolve();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source));old=bpy.data.objects['Separate fitted sweatshirt control, hood not constructed'];new=bpy.data.objects['Sewn clean hoodie with dropped hood'];count=len(old.data.vertices)
position=max((old.data.vertices[i].co-new.data.vertices[i].co).length for i in range(count));assert position==0
assert [list(f.vertices) for f in new.data.polygons[:len(old.data.polygons)]]==[list(f.vertices) for f in old.data.polygons]
uv=max((old.data.uv_layers.active.data[i].uv-new.data.uv_layers.active.data[i].uv).length for i in range(len(old.data.loops)));assert uv==0
w=lambda o,i:{o.vertex_groups[g.group].name:g.weight for g in o.data.vertices[i].groups if g.weight>0}
assert all(w(old,i)==w(new,i) for i in range(count))
key_errors={k.name:max((k.data[i].co-new.data.shape_keys.key_blocks[k.name].data[i].co).length for i in range(count)) for k in old.data.shape_keys.key_blocks};assert max(key_errors.values())<1e-7
owners=sorted({name for i in range(count,count+90) for name in w(new,i)});assert set(owners)<=set(['chest','neck','spine'])
edge_faces={}
for f in new.data.polygons:
 for aa,bb in zip(f.vertices,list(f.vertices[1:])+[f.vertices[0]]):
  edge=tuple(sorted((aa,bb)));edge_faces[edge]=edge_faces.get(edge,0)+1
old_edges={}
for f in old.data.polygons:
 for aa,bb in zip(f.vertices,list(f.vertices[1:])+[f.vertices[0]]):
  edge=tuple(sorted((aa,bb)));old_edges[edge]=old_edges.get(edge,0)+1
neck_edges={edge for edge,c in old_edges.items() if c==1 and min(old.data.vertices[i].co.z for i in edge)>1.5}
assert len(neck_edges)==20
sewn=sorted(edge for edge in neck_edges if edge_faces[edge]==2)
assert len(sewn)==16
report={'status':'Sewn native attachment and old shirt fields verified; moving shape/clearance pending','masterSHA256':sha(source),'recipeSHA256':sha(__file__),
 'originalVertices':count,'currentVertices':len(new.data.vertices),'oldBasisPositionErrorM':position,'oldUVError':uv,'oldPolygonsUnchanged':True,'oldWeightsUnchanged':True,
 'maximumOriginalKeyVectorErrorsM':key_errors,'newHoodOnlyOwners':owners,'sewnNecklineEdges':sewn,'sewnNecklineEdgeCount':len(sewn),
 'limits':['Sewn edge incidence verifies topological attachment, not cloth material behavior or complete triangle clearance.',
 'Pocket is a separately fitted surface component within the hoodie mesh; seam/interior detail still needs played qualification.',
 'No face/identity, originalbody/rig/jeans/accessory geometry or normal player promotion.']}
out.write_text(json.dumps(report,indent=2)+'\n');print('HOOD_CONSTRUCTION_VERIFIED',report['sewnNecklineEdgeCount'],report['newHoodOnlyOwners'],flush=True)
