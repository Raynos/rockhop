"""Isolate profile-field chord crossings on five pure right-upper triangles.

Read frozen fields only. Compare vertex-linear patches against sampled actual
positive radial field, without modifying the native garment or profiles.
"""
import argparse, gzip, hashlib, json, sys
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['field','profiles','recipe','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);field,profiles,recipe,out=[Path(getattr(a,k)).resolve() for k in ['field','profiles','recipe','out']]
out.mkdir(parents=True,exist_ok=True);assert not (out/'approximation.json').exists(),'Keep frozen inventories'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [field,profiles,recipe]}
assert pins[str(field)]=='4885dc1f16cc7873d0b44ed69e79658c042adb43f33d4e97ce9c92ad6b8badf0'
f=np.load(field);p=f['previousNativeXYZ'];final=f['finalNativeXYZ'];tri=f['triangles'];alpha=f['armSeamWeight'];fore=f['forearmBlendWeight'];previous={tuple(sorted(t)) for t in f['previousTriangles']}
pairs=[(int(i),int(j)) for i,j in f['finalSelfPairs'] if all(alpha[v]==1 and fore[v]==0 and f['sourceDisplayXYZ'][v,0]>0 for v in np.r_[tri[i],tri[j]])]
ids=sorted({i for pair in pairs for i in pair});assert len(pairs)==6 and len(ids)==5
assert all(tuple(sorted(tri[i])) in previous for i in ids),'Changed native tessellation cannot isolate field chord error'
rows=sorted([r for r in json.loads(gzip.decompress(profiles.read_bytes())) if r['part']=='upperArm.R' and r.get('usableCenteredRadialPair')],key=lambda r:r['station']);s=np.array([r['station'] for r in rows]);centers=np.array([r['planeCenterM'] for r in rows]);vector=(centers[1]-centers[0])/(s[1]-s[0]);length=np.linalg.norm(vector);axis=vector/length;head=centers[0]-s[0]*vector
branches={'upperArm.R':{'station':s,'air':np.array([r['sourceAirCentroidM'] for r in rows]),'body':np.array([r['bodyOuterCentroidM'] for r in rows]),'scale':np.maximum(1,np.array([r['maximumRequiredUniformCrossSectionScale'] for r in rows])),'head':head,'axis':axis,'length':length,'fadeWidth':float(np.median(np.diff(s)))}}
definition=recipe.read_text();definition=definition[definition.index('def branch('):definition.index('rows=[]')];exec(compile(definition,str(recipe),'exec'))
def actual(v):return v+branch('upperArm.R',v)[0]
closure=max(float(np.linalg.norm(actual(p[v])-final[v])) for i in ids for v in tri[i]);assert closure<1e-7
results=[];archives={}
for subdivisions in [1,32]:
    points=[];triangles=[];parents=[];baryArchive=[];errors=[];stationErrors=[]
    for ti in ids:
        vertices=p[tri[ti]];mapped=np.array([actual(v) for v in vertices]);lookup={}
        for i in range(subdivisions+1):
            for j in range(subdivisions+1-i):
                bary=np.array([1-(i+j)/subdivisions,i/subdivisions,j/subdivisions]);v=bary@vertices;q=actual(v);lookup[(i,j)]=len(points);points.append(q);baryArchive.append(bary.tolist());errors.append(float(np.linalg.norm(q-bary@mapped)));stationErrors.append(abs(float((q-v)@axis)))
        for i in range(subdivisions):
            for j in range(subdivisions-i):
                triangles.append([lookup[(i,j)],lookup[(i+1,j)],lookup[(i,j+1)]]);parents.append(ti)
                if i+j<subdivisions-1:triangles.append([lookup[(i+1,j)],lookup[(i+1,j+1)],lookup[(i,j+1)]]);parents.append(ti)
    tree=BVHTree.FromPolygons([Vector(v) for v in points],triangles,all_triangles=True);overlap=sorted((i,j) for i,j in tree.overlap(tree) if i<j and parents[i]!=parents[j] and not set(tri[parents[i]])&set(tri[parents[j]]));parentPairs=sorted({tuple(sorted([parents[i],parents[j]])) for i,j in overlap})
    results.append({'subdivisionsPerEdge':subdivisions,'sampledVertices':len(points),'sampledTriangles':len(triangles),'nonAdjacentCrossParentSubtrianglePairs':len(overlap),'originalParentPairs':parentPairs,'maximumActualFieldVsVertexLinearChordErrorM':max(errors),'maximumAxialDisplacementM':max(stationErrors)})
    archives['points'+str(subdivisions)]=np.array(points);archives['triangles'+str(subdivisions)]=np.array(triangles);archives['parentTriangleIDs'+str(subdivisions)]=np.array(parents);archives['barycentric'+str(subdivisions)]=np.array(baryArchive)
np.savez_compressed(out/'sampled-patches.npz',**archives)
report={'status':'UNACCEPTED read-only pure-branch profile triangle-approximation isolation','pins':pins,'recipeSHA256':sha(__file__),'pureRightUpperSource19Pairs':pairs,'uniqueTriangleIDs':ids,'allFiveTrianglesHaveSamePreviousTessellation':True,'source19VertexClosureResidualM':closure,'results':results,'archiveSHA256':sha(out/'sampled-patches.npz'),
        'injectivityScope':{'branch':'upperArm.R','allPatchVerticesSeamWeight':1,'allPatchVerticesForearmWeight':0,'minimumRadialScale':float(branches['upperArm.R']['scale'].min()),'maximumRadialScale':float(branches['upperArm.R']['scale'].max()),'bodyMinusAirCenterMaximumAxialComponentM':float(np.abs((branches['upperArm.R']['body']-branches['upperArm.R']['air'])@axis).max()),'meaning':'Pure branch preserves axial station; at each station its transverse map has positive uniform radial scale, hence the continuous mathematical map is injective. This argument is scoped to constant seam1/fore0 patches, not the full blended source field.'},
        'limits':['32 subdivisions are a fixed diagnostic sampling resolution, not a garment radius/iteration sweep or full-mesh construction. No native/model save or capture.','Finite sampled patches are not exact curved-surface distance proof; observed pair disappearance identifies approximation sensitivity, not full blended-field injectivity or all35 crossing repair.','493 body/35 self contacts remain the frozen source19 failure; original donor UV/PBR, body/head/51bind and controls immutable. No art/wearing/rig/mobile/M0-M5 acceptance, inference, worker, Library or player promotion.']}
assert pins=={p:sha(p) for p in pins};(out/'approximation.json').write_text(json.dumps(report,indent=2)+'\n');print('PURE_BRANCH_CHORD_ISOLATION_READY',json.dumps(results),flush=True)
