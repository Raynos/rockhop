"""Isolate affine-envelope blend crossings on fixed prior donor triangles.

Read frozen fields only. Compare vertex-linear patches against a sampled unchanged
branch field with barycentric frozen seam/elbow construction parameters, without modifying the native garment or profiles.
"""
import argparse, gzip, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','field','profiles','recipe','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,field,profiles,recipe,out=[Path(getattr(a,k)).resolve() for k in ['source','field','profiles','recipe','out']]
out.mkdir(parents=True,exist_ok=True);assert not (out/'approximation.json').exists(),'Keep frozen inventories'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,field,profiles,recipe]}
assert pins[str(field)]=='c9d89909d9c41bc3910fec8b822d661c4346c7972387546d98d266bcce186012'
f=np.load(field);p=f['previousNativeXYZ'];final=f['finalNativeXYZ'];tri=f['triangles'];alpha=f['armSeamWeight'];fore=f['forearmBlendWeight'];previous={tuple(sorted(t)) for t in f['previousTriangles']}
tri=f['previousTriangles'];pairs=[tuple(map(int,pair)) for pair in f['fixedTessellationSelfPairs']];ids=sorted({i for pair in pairs for i in pair});assert len(pairs)==80
profileRows=json.loads(gzip.decompress(profiles.read_bytes()));bpy.ops.wm.open_mainfile(filepath=str(source));rig=bpy.data.objects['Independent anatomical foundation rig'];branches={};reports={}
definition=recipe.read_text();definition=definition[definition.index("for part in sorted({r['part'] for r in profileRows}):"):definition.index('rows=[]')];exec(compile(definition,str(recipe),'exec'))
def actual(v,a,w,side):
    torso=branch('torso',v);upper=branch('upperArm.'+side,v);fr=branch('forearm.'+side,v)
    return v+(1-a)*torso+a*((1-w)*upper+w*fr)
closure=max(float(np.linalg.norm(actual(p[v],alpha[v],fore[v],'R' if f['sourceDisplayXYZ'][v,0]>=0 else 'L')-final[v])) for i in ids for v in tri[i]);assert closure<1e-7
results=[];archives={}
for subdivisions in [1,32]:
    points=[];triangles=[];parents=[];baryArchive=[];errors=[]
    for ti in ids:
        vertexIDs=tri[ti];vertices=p[vertexIDs];a=alpha[vertexIDs];w=fore[vertexIDs];side='R' if f['sourceDisplayXYZ'][vertexIDs,0].mean()>=0 else 'L';assert all((f['sourceDisplayXYZ'][v,0]>=0)==(side=='R') for v in vertexIDs);mapped=np.array([actual(v,aa,ww,side) for v,aa,ww in zip(vertices,a,w)]);lookup={}
        for i in range(subdivisions+1):
            for j in range(subdivisions+1-i):
                bary=np.array([1-(i+j)/subdivisions,i/subdivisions,j/subdivisions]);v=bary@vertices;q=actual(v,float(bary@a),float(bary@w),side);lookup[(i,j)]=len(points);points.append(q);baryArchive.append(bary.tolist());errors.append(float(np.linalg.norm(q-bary@mapped)))
        for i in range(subdivisions):
            for j in range(subdivisions-i):
                triangles.append([lookup[(i,j)],lookup[(i+1,j)],lookup[(i,j+1)]]);parents.append(ti)
                if i+j<subdivisions-1:triangles.append([lookup[(i+1,j)],lookup[(i+1,j+1)],lookup[(i,j+1)]]);parents.append(ti)
    tree=BVHTree.FromPolygons([Vector(v) for v in points],triangles,all_triangles=True);overlap=sorted((i,j) for i,j in tree.overlap(tree) if i<j and parents[i]!=parents[j] and not set(tri[parents[i]])&set(tri[parents[j]]));parentPairs=sorted({tuple(sorted([parents[i],parents[j]])) for i,j in overlap})
    results.append({'subdivisionsPerEdge':subdivisions,'sampledVertices':len(points),'sampledTriangles':len(triangles),'nonAdjacentCrossParentSubtrianglePairs':len(overlap),'originalParentPairs':parentPairs,'maximumActualFieldVsVertexLinearChordErrorM':max(errors)})
    archives['points'+str(subdivisions)]=np.array(points);archives['triangles'+str(subdivisions)]=np.array(triangles);archives['parentTriangleIDs'+str(subdivisions)]=np.array(parents);archives['barycentric'+str(subdivisions)]=np.array(baryArchive)
np.savez_compressed(out/'sampled-patches.npz',**archives)
report={'status':'UNACCEPTED read-only affine branch blend approximation diagnostic','pins':pins,'recipeSHA256':sha(__file__),'fixedPreviousTessellationSource21Pairs':pairs,'uniqueTriangleIDs':ids,'source21VertexClosureResidualM':closure,'results':results,'archiveSHA256':sha(out/'sampled-patches.npz'),
        'parameterExtension':'All five branch maps unchanged. Frozen construction alpha/fore weights interpolated barycentrically inside each original triangle; exact at existing vertices and shared edges. This is an explicit diagnostic extension, not independent garment rig weights or proof that every full-field volume point is injective.',
        'limits':['One versus fixed32 edge subdivisions compare geometric approximation with no radius/profile/capture change. Only contact-parent patches are sampled; no native/model save.','Finite sampled patches and barycentric construction-parameter extension do not prove whole-mesh clearance, unseen pair absence, complete field injectivity, anatomical ports or mobile triangle budget.','Actual native21 remains459body/79self failed; fixed previous tessellation459body/80self. Original UV/PBR/body/head/51bind and controls immutable. All art/wearing/rig/mobile/M0-M5 gates open, no inference/worker/Library/player promotion.']}
assert pins=={p:sha(p) for p in pins};(out/'approximation.json').write_text(json.dumps(report,indent=2)+'\n');print('AFFINE_BLEND_PATCH_DIAGNOSTIC_READY',json.dumps(results),flush=True)
