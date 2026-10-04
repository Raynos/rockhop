"""Restore one anatomically fixed right cuff after coherent donor flow."""
import argparse, collections, hashlib, json, sys
from pathlib import Path
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','localization','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field,localization,out,evidence=[Path(getattr(a,k)).resolve() for k in ['source','field','localization','out','evidence']];out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True);assert not (out/'wrist-cuff.blend').exists(),'Frozen native output'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field,localization]};assert pins[str(source)]=='c50417a78f90b1e7376ff6166275b92379bd23e7146832ebf34ebb5bfa50f3cc';f=np.load(field);lr=json.loads(localization.read_text());assert lr['bodyContactPairs']==46
bpy.ops.wm.open_mainfile(filepath=str(source));old=bpy.data.objects['Actual selected donor, ambient measured-lumen flow, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig'];g=old.copy();g.data=old.data.copy();bpy.context.collection.objects.link(g);g.name='Actual selected donor, actual wrist cuff recut, unaccepted';native=np.array([v.co[:] for v in old.data.vertices]);assert np.array_equal(native,f['finalNativeXYZ']);bone=rig.data.bones['forearm.R'];axis=np.array(bone.tail_local)-np.array(bone.head_local);axis/=np.linalg.norm(axis);plane=np.array(bone.tail_local)-.005*axis;d=(native-plane)@axis
outside=np.where(d>1e-8)[0];assert len(outside)>0;display=np.array([x.vector[:] for x in old.data.attributes['actual_donor_display_xyz'].data]);assert np.all(native[outside,1]>.3) and np.all(display[outside,0]>.43),'Cut would touch non-right-sleeve donor'
uv=old.data.uv_layers.active
# Compare retained polygon corner positions/UVs independently of index rotation.
def canonical(rows):return min(tuple(rows[i:]+rows[:i]) for i in range(len(rows)))
oldSignatures={poly.index:canonical([tuple(native[old.data.loops[loop].vertex_index])+tuple(uv.data[loop].uv) for loop in poly.loop_indices]) for poly in old.data.polygons if np.all(d[list(poly.vertices)]< -1e-8)}
bm=bmesh.new();bm.from_mesh(g.data);bm.faces.ensure_lookup_table();parent=bm.faces.layers.int.new('source22_polygon_id')
for i,face in enumerate(bm.faces):face[parent]=i
beforeV=len(bm.verts);beforeF=len(bm.faces);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-8,plane_co=Vector(plane),plane_no=Vector(axis),clear_outer=True,clear_inner=False)
loose=[v for v in bm.verts if not v.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
bm.to_mesh(g.data);bm.free();g.data.update();g.data.calc_loop_triangles();p=np.array([v.co[:] for v in g.data.vertices]);tri=np.array([t.vertices[:] for t in g.data.loop_triangles]);pd=(p-plane)@axis;assert pd.max()<1e-6
uv=g.data.uv_layers.active;retained=0
for poly in g.data.polygons:
    parentID=g.data.attributes['source22_polygon_id'].data[poly.index].value
    if parentID in oldSignatures:
        signature=canonical([tuple(p[g.data.loops[loop].vertex_index])+tuple(uv.data[loop].uv) for loop in poly.loop_indices]);assert signature==oldSignatures[parentID],parentID;retained+=1
assert retained==len(oldSignatures);assert g.data.materials[0] is old.data.materials[0]
body.data.calc_loop_triangles();bp=np.array([v.co[:] for v in body.data.vertices]);bt=np.array([t.vertices[:] for t in body.data.loop_triangles]);gt=BVHTree.FromPolygons([Vector(v) for v in p],tri.tolist(),all_triangles=True);bvh=BVHTree.FromPolygons([Vector(v) for v in bp],bt.tolist(),all_triangles=True);contacts=sorted(gt.overlap(bvh));selfpairs=sorted((i,j) for i,j in gt.overlap(gt) if i<j and not set(tri[i])&set(tri[j]));counts=collections.Counter();witnesses=[]
for i,j in contacts:
    weights=collections.Counter()
    for v in bt[j]:
        for group in body.data.vertices[int(v)].groups:
            name=body.vertex_groups[group.group].name
            if name in rig.data.bones:weights[name]+=group.weight/3
    name=max(weights,key=weights.get);counts[name]+=1;witnesses.append({'garmentTriangle':i,'bodyTriangle':j,'dominantRawBone':name,'garmentXYZ':p[tri[i]].tolist(),'bodyXYZ':bp[bt[j]].tolist()})
# Original interior witnesses must remain byte-identical coordinate triangles.
def geometrykey(q):return tuple(sorted(tuple(row) for row in q))
expected={(x['bodyTriangle'],geometrykey(native[f['triangles'][x['garmentTriangle']]])) for x in lr['allContactWitnesses'] if x['dominantRawBone']!='hand.R'};actual={(j,geometrykey(p[tri[i]])) for i,j in contacts};assert actual==expected,'Recut changed interior contact set'
edges=collections.Counter(tuple(sorted((ids[k],ids[(k+1)%len(ids)]))) for poly in g.data.polygons for ids in [list(poly.vertices)] for k in range(len(ids)));free=[e for e,n in edges.items() if n==1];degree=collections.Counter(v for e in free for v in e);assert all(n==2 for n in degree.values());assert not any(n>2 for n in edges.values())
old.hide_set(True);old.hide_render=True;g.hide_set(False);g.hide_render=False;g['accepted']=False;g['constructionStage']='Actual right-wrist minus5mm recut after ambient flow; interior wearing contacts unresolved';bpy.ops.wm.save_as_mainfile(filepath=str(out/'wrist-cuff.blend'),compress=True);np.savez_compressed(out/'wrist-cuff.npz',nativeXYZ=p,triangles=tri,bodyTrianglePairs=np.array(contacts),selfTrianglePairs=np.array(selfpairs),sourceDisplayXYZ=np.array([v.vector[:] for v in g.data.attributes['actual_donor_display_xyz'].data]))
report={'status':'UNACCEPTED actual donor anatomical right-cuff recut','pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'wrist-cuff.blend'),'fieldSHA256':sha(out/'wrist-cuff.npz'),'planePointM':plane.tolist(),'planeNormal':axis.tolist(),'cutMarginBeforeWristM':.005,'preCutPositiveVertexCount':len(outside),'preCutPositiveVertexSourceXRange':np.percentile(display[outside,0],[0,100]).tolist(),'beforeVertices':beforeV,'beforePolygons':beforeF,'vertices':len(p),'polygons':len(g.data.polygons),'triangles':len(tri),'unchangedRetainedPolygonsUVAndPositionsExact':retained,'exactOriginalMaterial':True,'maximumPlaneOvershootM':float(pd.max()),'bodyPairs':len(contacts),'selfPairs':len(selfpairs),'bodyRawBoneClasses':dict(counts),'original31InteriorContactsCoordinateExact':True,'boundaryEdges':len(free),'allBoundaryVerticesDegree2':True,'otherNonManifoldEdges':sum(n>2 for n in edges.values()),'allBodyWitnesses':witnesses,'method':'One original anatomical wrist-minus5mm halfspace restored after ambient flow; positive geometry independently constrained to right sleeve. Standard BMesh plane splitting interpolates donor UV/ancestry; unchanged retained polygon corners verified exact. No wall deletion beyond this wearer cut.','limits':['No local radial fit or repair of31remaining interior sleeve contacts. No actual air-port containment proof, rig/motion/capture, body/head/51bind mutation, inference/worker/Library/player promotion or M0-M5/mobile/played art acceptance.','UV interpolation at new cut corners is Blender bisect behavior; unchanged polygons tested exactly, original donor PBR retained. Original protected data needs separate scoped preservation audit.']}
assert pins=={x:sha(x) for x in pins};(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print('WRIST_CUFF_RECUT','body',len(contacts),'self',len(selfpairs),'classes',dict(counts),'unchangedPolygons',retained,flush=True)
