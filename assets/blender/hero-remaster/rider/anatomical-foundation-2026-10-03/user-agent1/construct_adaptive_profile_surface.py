"""Represent the unchanged measured donor fit with conforming error refinement.

Refine the actual source18 triangular surface before applying the source70
profile field. Shared edge midpoints prevent T junctions; donor UVs and source
parameters interpolate with exact parent-face barycentric ancestry. Stop on
0.25 mm midpoint/centroid interpolation error, never on contact counts.
"""
import argparse, gzip, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','profiles','recipe','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field,profiles,recipe,out,evidence=[Path(getattr(a,k)).resolve() for k in ['source','field','profiles','recipe','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True);assert not (out/'adaptive-profile.blend').exists(),'Keep frozen controls'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field,profiles,recipe]}
assert pins[str(source)]=='b545229e52c4fc5bcb97b4fbc81ccc3a0e5a2f9c87fe3c7338691317d965e449';assert pins[str(field)]=='4885dc1f16cc7873d0b44ed69e79658c042adb43f33d4e97ce9c92ad6b8badf0'
frozen=np.load(field);profileRows=json.loads(gzip.decompress(profiles.read_bytes()))
bpy.ops.wm.open_mainfile(filepath=str(source));old=bpy.data.objects['Actual selected donor, measured lumen registration, unaccepted'];failed=bpy.data.objects['Actual selected donor, measured clearance profiles, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
native=np.array([v.co[:] for v in old.data.vertices]);assert np.array_equal(native,frozen['previousNativeXYZ']);old.data.calc_loop_triangles();originalTri=np.array([t.vertices[:] for t in old.data.loop_triangles]);assert np.array_equal(originalTri,frozen['previousTriangles'])
originalLoops=np.array([t.loops[:] for t in old.data.loop_triangles]);sourceUV={layer.name:np.array([v.uv[:] for v in layer.data])[originalLoops] for layer in old.data.uv_layers}
originalSmooth=np.array([old.data.polygons[t.polygon_index].use_smooth for t in old.data.loop_triangles]);originalMaterials=np.array([old.data.polygons[t.polygon_index].material_index for t in old.data.loop_triangles])
g=old.copy();g.data=old.data.copy();bpy.context.collection.objects.link(g);g.name='Actual selected donor, adaptive measured profile surface, unaccepted';g.hide_set(False);g.hide_render=False
branches={}
definition=recipe.read_text();definition=definition[definition.index("for part in sorted({r['part'] for r in profileRows}):"):definition.index('rows=[]')];exec(compile(definition,str(recipe),'exec'))
def transform(p,a,w,sourceX):
    side='R' if sourceX>=0 else 'L';torso=branch('torso',p)[0];upper=branch('upperArm.'+side,p)[0];fore=branch('forearm.'+side,p)[0]
    return p+(1-a)*torso+a*((1-w)*upper+w*fore)
base=list(native);sourcePoints=list(frozen['sourceDisplayXYZ']);alpha=list(frozen['armSeamWeight']);foreWeight=list(frozen['forearmBlendWeight']);mapped=[transform(p,a,w,s[0]) for p,a,w,s in zip(base,alpha,foreWeight,sourcePoints)]
faces=[(tuple(map(int,t)),i,np.eye(3)) for i,t in enumerate(originalTri)];tolerance=.00025;edgeCache={};faceCache={};rounds=[]
for refinement in range(9):
    edges={tuple(sorted((ids[i],ids[(i+1)%3]))) for ids,parent,bary in faces for i in range(3)};marked=set();maxEdge=0.;maxFace=0.
    for edge in edges:
        if edge not in edgeCache:
            i,j=edge;p=(base[i]+base[j])/2;s=(sourcePoints[i]+sourcePoints[j])/2;a=(alpha[i]+alpha[j])/2;w=(foreWeight[i]+foreWeight[j])/2;q=transform(p,a,w,s[0]);error=float(np.linalg.norm(q-(mapped[i]+mapped[j])/2));edgeCache[edge]=(p,s,a,w,q,error)
        error=edgeCache[edge][-1];maxEdge=max(maxEdge,error)
        if error>tolerance:marked.add(edge)
    for ids,parent,bary in faces:
        key=tuple(sorted(ids))
        if key not in faceCache:
            p=np.mean([base[i] for i in ids],axis=0);s=np.mean([sourcePoints[i] for i in ids],axis=0);q=transform(p,float(np.mean([alpha[i] for i in ids])),float(np.mean([foreWeight[i] for i in ids])),s[0]);faceCache[key]=float(np.linalg.norm(q-np.mean([mapped[i] for i in ids],axis=0)))
        error=faceCache[key];maxFace=max(maxFace,error)
        if error>tolerance:marked.update(tuple(sorted((ids[i],ids[(i+1)%3]))) for i in range(3))
    rounds.append({'refinement':refinement,'vertices':len(base),'triangles':len(faces),'uniqueEdges':len(edges),'markedEdges':len(marked),'maximumEdgeMidpointErrorM':maxEdge,'maximumFaceCentroidErrorM':maxFace});print('ADAPTIVE_PROFILE_ERROR',json.dumps(rounds[-1]),flush=True)
    if not marked:break
    assert refinement<8,'Error refinement cap reached before tolerance; no native save'
    midpoint={}
    for edge in sorted(marked):
        p,s,a,w,q,error=edgeCache[edge];midpoint[edge]=len(base);base.append(p);sourcePoints.append(s);alpha.append(a);foreWeight.append(w);mapped.append(q)
    newFaces=[]
    for ids,parent,bary in faces:
        corners=[(ids[i],bary[i]) for i in range(3)];flags=[tuple(sorted((ids[i],ids[(i+1)%3]))) in marked for i in range(3)];n=sum(flags)
        if not n:newFaces.append((ids,parent,bary));continue
        def middle(a,b):return(midpoint[tuple(sorted((a[0],b[0])))],(a[1]+b[1])/2)
        if n==1:
            i=flags.index(True);A,B,C=[corners[(i+j)%3] for j in range(3)];AB=middle(A,B);pieces=[(A,AB,C),(AB,B,C)]
        elif n==2:
            i=next(i for i in range(3) if flags[i] and flags[(i+1)%3]);A,B,C=[corners[(i+j)%3] for j in range(3)];AB=middle(A,B);BC=middle(B,C);pieces=[(A,AB,C),(AB,BC,C),(AB,B,BC)]
        else:
            A,B,C=corners;AB=middle(A,B);BC=middle(B,C);CA=middle(C,A);pieces=[(A,AB,CA),(AB,B,BC),(CA,BC,C),(AB,BC,CA)]
        for piece in pieces:newFaces.append((tuple(v[0] for v in piece),parent,np.array([v[1] for v in piece])))
    faces=newFaces
pre=np.array(base);proposed=np.array(mapped);parents=np.array([r[1] for r in faces]);bary=np.array([r[2] for r in faces]);tri=np.array([r[0] for r in faces]);assert np.max(np.abs(bary.sum(2)-1))<1e-14
closure=np.max(np.linalg.norm(pre[tri]-np.einsum('fij,fjk->fik',bary,native[originalTri[parents]]),axis=2));assert closure<1e-12
# Rebuild derivative only; retained original objects and original donor graphs untouched.
g.data.clear_geometry();g.data.from_pydata(proposed.tolist(),[],tri.tolist());g.data.update()
for uvName,original in sourceUV.items():
    uv=np.einsum('fij,fjk->fik',bary,original[parents]);layer=g.data.uv_layers.get(uvName) or g.data.uv_layers.new(name=uvName);layer.data.foreach_set('uv',uv.astype(np.float32).ravel())
for polygon,parent in zip(g.data.polygons,parents):polygon.use_smooth=bool(originalSmooth[parent]);polygon.material_index=int(originalMaterials[parent])
attr=g.data.attributes.get('actual_donor_display_xyz') or g.data.attributes.new('actual_donor_display_xyz',type='FLOAT_VECTOR',domain='POINT');attr.data.foreach_set('vector',np.array(sourcePoints,dtype=np.float32).ravel())
ancestor=g.data.attributes.get('source18_triangle') or g.data.attributes.new('source18_triangle',type='INT',domain='FACE');ancestor.data.foreach_set('value',parents.astype(np.int32))
g.data.update();g.data.calc_loop_triangles();p=np.array([v.co[:] for v in g.data.vertices]);actualTri=np.array([t.vertices[:] for t in g.data.loop_triangles]);assert np.array_equal(tri,actualTri);assert g.data.materials[0] is old.data.materials[0]
counts={}
for ids in tri:
    for i,j in zip(ids,np.roll(ids,-1)):e=tuple(sorted((int(i),int(j))));counts[e]=counts.get(e,0)+1
body.data.calc_loop_triangles();bp=np.array([v.co[:] for v in body.data.vertices]);btri=[tuple(t.vertices) for t in body.data.loop_triangles];gt=BVHTree.FromPolygons([Vector(v) for v in p],tri.tolist(),all_triangles=True);bt=BVHTree.FromPolygons([Vector(v) for v in bp],btri,all_triangles=True)
selfPairs=sorted((i,j) for i,j in gt.overlap(gt) if i<j and not set(tri[i])&set(tri[j]));bodyPairs=sorted(gt.overlap(bt));boundary={e for e,c in counts.items() if c==1};loops=0
while boundary:
    e=boundary.pop();found=set(e);stack=list(e)
    while stack:
        v=stack.pop();touch=[x for x in boundary if v in x]
        for edge in touch:boundary.remove(edge);other=edge[1] if edge[0]==v else edge[0];found.add(other);stack.append(other)
    loops+=1
old.hide_set(True);old.hide_render=True;failed.hide_set(True);failed.hide_render=True;g['accepted']=False;g['constructionStage']='Actual donor conforming error-refined profile surface; unrigged/unqualified'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'adaptive-profile.blend'),compress=True)
np.savez_compressed(out/'adaptive-profile-field.npz',preFieldNativeXYZ=pre,finalNativeXYZ=p,sourceDisplayXYZ=np.array(sourcePoints),armSeamWeight=np.array(alpha),forearmBlendWeight=np.array(foreWeight),triangles=tri,source18TriangleIDs=parents,parentBarycentricCoordinates=bary,bodyTrianglePairs=np.array(bodyPairs),selfTrianglePairs=np.array(selfPairs))
report={'status':'UNACCEPTED conforming representation of unchanged measured profile fit','pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'adaptive-profile.blend'),'fieldSHA256':sha(out/'adaptive-profile-field.npz'),'method':'Conforming shared-edge midpoint/red-green refinement before field; stop when all edge-midpoint and face-centroid field interpolation residuals <=0.25mm. This error allowance is ~1/28 of measured median7mm donor wall spacing, not a collision-count stop. Exact parent-face barycentric source geometry, donor UV and frozen construction parameters; all profile/radius/centre/support parameters unchanged.',
        'refinementHistory':rounds,'interpolationToleranceM':tolerance,'maximumPreFieldParentBarycentricClosureM':float(closure),'vertices':len(p),'triangles':len(tri),'originalVertices':len(native),'originalTriangles':len(originalTri),'originalVertexFieldClosureM':float(np.linalg.norm(p[:len(native)]-frozen['finalNativeXYZ'],axis=1).max()),'boundaryEdgeCount':sum(c==1 for c in counts.values()),'boundaryComponents':loops,'otherNonManifoldEdges':sum(c>2 for c in counts.values()),'bodyPairs':len(bodyPairs),'selfPairs':len(selfPairs),'bodyContactOriginalParentTriangles':len({int(parents[i]) for i,j in bodyPairs}),'selfContactOriginalParentPairs':sorted({tuple(sorted((int(parents[i]),int(parents[j])))) for i,j in selfPairs}),
        'limits':['0.25mm sample-error convergence is not a complete curved-surface distance bound, global field injectivity, body containment or wearer-port proof. Contacts on changed triangle density are not directly comparable to coarse pair counts.','Actual selected source surface is triangulated/refined; original UVs are barycentrically interpolated, not copied with unchanged polygon cycles. Field changes dimensions and wall thickness. No texture replacement/stock-pattern reconstruction/vertex snaps/radius sweep.','No rig/skin/motion/capture/inference/worker/body-head-51bind replacement, Library/player promotion or art/wearing/mobile/M0-M5 acceptance. All prior controls retained; parent alone judges.']}
assert pins=={p:sha(p) for p in pins};(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n');print('ADAPTIVE_DONOR_PROFILE_READY','triangles',len(tri),'body',len(bodyPairs),'self',len(selfPairs),flush=True)
