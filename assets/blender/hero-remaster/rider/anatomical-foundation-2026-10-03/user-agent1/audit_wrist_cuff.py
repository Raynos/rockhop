"""Verify saved anatomical cuff contacts, ancestry and actual free loops."""
import argparse, collections, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','report','previous-audit','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field,report,previous,out=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','field','report','previous-audit','out']];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field,report,previous]};r=json.loads(report.read_text());prior=json.loads(previous.read_text());assert pins[str(source)]==r['candidateSHA256'] and pins[str(field)]==r['fieldSHA256'];f=np.load(field)
bpy.ops.wm.open_mainfile(filepath=str(source));g=bpy.data.objects['Actual selected donor, actual wrist cuff recut, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];g.data.calc_loop_triangles();body.data.calc_loop_triangles();p=np.array([v.co[:] for v in g.data.vertices]);tri=np.array([t.vertices[:] for t in g.data.loop_triangles]);bp=np.array([v.co[:] for v in body.data.vertices]);bt=np.array([t.vertices[:] for t in body.data.loop_triangles]);assert np.array_equal(p,f['nativeXYZ']) and np.array_equal(tri,f['triangles']);assert np.array_equal(np.array([v.vector[:] for v in g.data.attributes['actual_donor_display_xyz'].data]),f['sourceDisplayXYZ'])
gt=BVHTree.FromPolygons([Vector(v) for v in p],tri.tolist(),all_triangles=True);bvh=BVHTree.FromPolygons([Vector(v) for v in bp],bt.tolist(),all_triangles=True);contacts=sorted(gt.overlap(bvh));sp=sorted((i,j) for i,j in gt.overlap(gt) if i<j and not set(tri[i])&set(tri[j]));assert contacts==sorted(map(tuple,f['bodyTrianglePairs'])) and sp==sorted(map(tuple,f['selfTrianglePairs']));assert len(contacts)==31 and not sp
key=lambda q:tuple(sorted(tuple(row) for row in q));expected={(x['bodyTriangle'],key(x['garmentXYZ'])) for x in prior['allBodyWitnesses'] if x['dominantRawBodyBone']!='hand.R'};actual={(j,key(p[tri[i]])) for i,j in contacts};assert actual==expected
edgeCounts=collections.Counter(tuple(sorted((ids[k],ids[(k+1)%len(ids)]))) for poly in g.data.polygons for ids in [list(poly.vertices)] for k in range(len(ids)));free={e for e,n in edgeCounts.items() if n==1};assert not any(n>2 for n in edgeCounts.values());loops=[];remaining=set(free)
while remaining:
    first=remaining.pop();edges={first};ids=set(first);stack=list(first)
    while stack:
        v=stack.pop()
        for e in list(remaining):
            if v in e:remaining.remove(e);edges.add(e);other=e[0] if e[1]==v else e[1];ids.add(other);stack.append(other)
    q=p[sorted(ids)];degree=collections.Counter(v for e in edges for v in e);assert all(n==2 for n in degree.values());loops.append({'edges':len(edges),'vertexIDs':sorted(ids),'boundsM':[q.min(0).tolist(),q.max(0).tolist()],'allDegree2':True})
plane=np.array(r['planePointM']);axis=np.array(r['planeNormal']);assert ((p-plane)@axis).max()<1e-6
result={'status':'UNACCEPTED saved anatomical wrist-cuff reproduction','pins':pins,'recipeSHA256':sha(__file__),'archiveNativePositionsTrianglesSourceAncestryAndContactArraysExact':True,'previous31InteriorContactCoordinatesExact':True,'bodyPairs':len(contacts),'selfPairs':len(sp),'boundaryEdges':len(free),'boundaryLoops':loops,'otherNonManifoldEdges':0,'maximumPlaneOvershootM':float(((p-plane)@axis).max()),'limits':['31interior body contacts stillfail. Geometric free loops do not prove physical wearer air ports or local/global containment.','No native save, rig/motion/capture/body-head-51bind mutation/Library/player promotion or art/M0-M5/mobile acceptance.']};assert pins=={x:sha(x) for x in pins};out.write_text(json.dumps(result,indent=2)+'\n');print('SAVED_WRIST_CUFF_EXACT','body',len(contacts),'self',len(sp),'loops',len(loops),flush=True)
