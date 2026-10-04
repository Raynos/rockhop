"""Measure oriented source lumen sections and canonical body sections.

Analyze an uncut direct simplification of the exact donor in memory. Positive
oriented contours bound material outside; negative contours bound air cavities.
No global radial-normal face deletion, source rewrite or acceptance claim.
"""
import argparse, collections, gzip, hashlib, json, math, sys
from pathlib import Path
import bpy, bmesh, numpy as np
from mathutils import Vector
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','setup-recipe','registration-recipe','continuous-recipe','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,setup,recipe,continuous,out=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','setup-recipe','registration-recipe','continuous-recipe','out']]
out.mkdir(parents=True,exist_ok=True);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,setup,recipe,continuous]}
assert pins[str(source)]=='989855995983079d3207960f5e36feb734fe0e02987961d8f652c8cd26c3ae3f'
bpy.ops.wm.open_mainfile(filepath=str(source));high=bpy.data.objects['Exact selected Hunyuan high-poly PBR donor, display frame only'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
fragment=setup.read_text();fragment=fragment[fragment.index('g=high.copy()'):fragment.index('definition=recipe.read_text()')];exec(compile(fragment,str(setup),'exec'))
g.data.calc_loop_triangles();sourceTri=np.array([t.vertices[:] for t in g.data.loop_triangles]);body.data.calc_loop_triangles();bodyXYZ=np.array([v.co[:] for v in body.data.vertices]);bodyTri=np.array([t.vertices[:] for t in body.data.loop_triangles])
definition=recipe.read_text();definition=definition[definition.index('height=.472'):definition.index('lineage=[]')];exec(compile(definition,str(recipe),'exec'))
definition=continuous.read_text();definition=definition[definition.index('width=.12'):definition.index('oldMapped=np.array')];exec(compile(definition,str(continuous),'exec'))
def section(points,tri,center,normal):
    normal=np.asarray(normal,dtype=np.float64)
    guide=np.array([0,1,0]) if abs(normal[1])<.9 else np.array([1,0,0]);u=np.cross(normal,guide);u/=np.linalg.norm(u);v=np.cross(normal,u)
    distance=(points-center)@normal;cut=np.flatnonzero((distance[tri].min(1)<=0)&(distance[tri].max(1)>=0));nodes={};edges=[];ambiguous=0;epsilon=1e-10
    for t in cut:
        ids=tri[t];keys=[]
        for i,j in zip(ids,np.roll(ids,-1)):
            di,dj=distance[i],distance[j]
            if abs(di)<=epsilon:
                key=('v',int(i));nodes[key]=points[i];keys.append(key)
            if di*dj<0 and abs(di)>epsilon and abs(dj)>epsilon:
                i,j=sorted([int(i),int(j)]);key=('e',i,j);q=points[i]+(points[j]-points[i])*distance[i]/(distance[i]-distance[j]);nodes[key]=q;keys.append(key)
        keys=list(dict.fromkeys(keys))
        if len(keys)!=2:ambiguous+=1;continue
        n=np.cross(points[ids[1]]-points[ids[0]],points[ids[2]]-points[ids[0]])
        if (nodes[keys[1]]-nodes[keys[0]])@np.cross(normal,n)<0:keys.reverse()
        edges.append(tuple(keys))
    adjacent=collections.defaultdict(set);incoming=collections.defaultdict(list);outgoing=collections.defaultdict(list)
    for i,j in edges:adjacent[i].add(j);adjacent[j].add(i);outgoing[i].append(j);incoming[j].append(i)
    remaining=set(adjacent);contours=[]
    while remaining:
        start=remaining.pop();found={start};stack=[start]
        while stack:
            for other in adjacent[stack.pop()]:
                if other in remaining:remaining.remove(other);found.add(other);stack.append(other)
        closed=all(len(incoming[x])==len(outgoing[x])==1 for x in found)
        row={'nodes':len(found),'orientedClosedCycle':closed}
        if closed:
            ordered=[min(found)];nextNode=outgoing[ordered[0]][0]
            while nextNode!=ordered[0] and len(ordered)<=len(found):ordered.append(nextNode);nextNode=outgoing[nextNode][0]
            assert len(ordered)==len(found)
            p=np.array([nodes[x] for x in ordered]);local=np.column_stack([(p-center)@u,(p-center)@v]);q=np.roll(local,-1,axis=0);cross=local[:,0]*q[:,1]-q[:,0]*local[:,1];area=float(cross.sum()/2)
            if abs(area)>1e-12:
                centroid=(cross[:,None]*(local+q)).sum(0)/(6*area);world=center+centroid[0]*u+centroid[1]*v
                contains=False
                for x,y in zip(local,q):
                    if (x[1]>0)!=(y[1]>0) and 0<(y[0]-x[0])*(-x[1])/(y[1]-x[1])+x[0]:contains=not contains
                row.update({'signedPlaneArea':area,'orientation':'materialOuter' if area>0 else 'airCavity','centroidXYZ':world.tolist(),'centroidOffsetFromReference':float(np.linalg.norm(world-center)),'containsReferenceAxisPoint':contains,'maximumContourRadiusFromCentroid':float(np.linalg.norm(p-world,axis=1).max()),'XYZ':p.tolist()})
        contours.append(row)
    return {'ambiguousIntersectedTriangles':ambiguous,'contours':contours}
rows=[]
for side in ['R','L']:
    for segmentIndex,name in [(0,'upperArm.'),(1,'forearm.')]:
        bone=rig.data.bones[name+side];bh=np.array(list(bone.head_local));bt=np.array(list(bone.tail_local));bn=bt-bh;bn/=np.linalg.norm(bn);s=source_anchors[side];sn=s[segmentIndex+1]-s[segmentIndex];sn/=np.linalg.norm(sn)
        for station in np.linspace(.05,.95,16):
            sc=s[segmentIndex]+(s[segmentIndex+1]-s[segmentIndex])*station;bc=bh+(bt-bh)*station
            sr=section(display,sourceTri,sc,sn);br=section(bodyXYZ,bodyTri,bc,bn)
            air=[c for c in sr['contours'] if c.get('orientation')=='airCavity'];outer=[c for c in br['contours'] if c.get('orientation')=='materialOuter'];row={'part':name+side,'station':float(station),'sourceAxisPoint':sc.tolist(),'bodyAxisPointM':bc.tolist(),'sourceSection':sr,'bodySection':br}
            if air and outer:
                selectedAir=min(air,key=lambda c:c['centroidOffsetFromReference']);selectedBody=min(outer,key=lambda c:c['centroidOffsetFromReference']);mapped=connected(np.array(selectedAir['centroidXYZ']))[0]
                row['nearestSourceAirContour']={k:v for k,v in selectedAir.items() if k!='XYZ'};row['nearestBodyOuterContour']={k:v for k,v in selectedBody.items() if k!='XYZ'}
                row['mappedSourceLumenCentroidNativeM']=mapped.tolist();row['mappedLumenCentroidVsBodySectionCentroidM']=float(np.linalg.norm(mapped-np.array(selectedBody['centroidXYZ'])))
                row['nonlocalSourceContourDiagnostic']=bool(selectedAir['centroidOffsetFromReference']>.2)
            rows.append(row)
torso=[]
for z in np.linspace(1.04,1.49,32):
    sz=(z-up)/height;sc=np.array([0,0,sz]);bc=np.array([.015,0,z]);sn=np.array([0,0,1]);sr=section(display,sourceTri,sc,sn);br=section(bodyXYZ,bodyTri,bc,sn)
    air=[c for c in sr['contours'] if c.get('orientation')=='airCavity' and c['containsReferenceAxisPoint']];outer=[c for c in br['contours'] if c.get('orientation')=='materialOuter' and c['containsReferenceAxisPoint']]
    row={'nativeHeightM':float(z),'sourceHeightOriginalUnits':float(sz),'sourceSection':sr,'bodySection':br}
    if air and outer:
        sa=max(air,key=lambda c:abs(c['signedPlaneArea']));bo=max(outer,key=lambda c:abs(c['signedPlaneArea']));mapped=connected(np.array(sa['centroidXYZ']))[0]
        row['sourceAirContour']={k:v for k,v in sa.items() if k!='XYZ'};row['bodyOuterContour']={k:v for k,v in bo.items() if k!='XYZ'};row['mappedSourceAirCentroidNativeM']=mapped.tolist();row['bodyMinusMappedSourceCentroidNativeM']=(np.array(bo['centroidXYZ'])-mapped).tolist()
    torso.append(row)
summary={}
for part in sorted({r['part'] for r in rows}):
    records=[r for r in rows if r['part']==part];matched=[r for r in records if 'nearestSourceAirContour' in r]
    summary[part]={'sections':len(records),'sectionsWithSourceAirAndBodyOuterContour':len(matched),'sourceReferenceInsideNearestAirContour':sum(r['nearestSourceAirContour']['containsReferenceAxisPoint'] for r in matched),'nonlocalNearestSourceContours':sum(r['nonlocalSourceContourDiagnostic'] for r in matched),
                   'sourceAirContourCentroidOffsetOriginalUnitsPercentiles':np.percentile([r['nearestSourceAirContour']['centroidOffsetFromReference'] for r in matched],[0,50,95,100]).tolist() if matched else [],
                   'mappedSourceLumenVsBodyCentroidMPercentiles':np.percentile([r['mappedLumenCentroidVsBodySectionCentroidM'] for r in matched],[0,50,95,100]).tolist() if matched else []}
archive=out/'sections.json.gz';archive.write_bytes(gzip.compress(json.dumps({'sleeves':rows,'torso':torso},separators=(',',':')).encode(),mtime=0))
torsoPairs=[r for r in torso if 'bodyMinusMappedSourceCentroidNativeM' in r]
torsoSummary={'sections':len(torso),'containingSourceAirAndBodyOuterPairs':len(torsoPairs),'bodyMinusMappedSourceCentroidMPercentiles':np.percentile([r['bodyMinusMappedSourceCentroidNativeM'] for r in torsoPairs],[0,50,95,100],axis=0).tolist() if torsoPairs else []}
report={'status':'UNACCEPTED actual uncut donor lumen/body contour inventory','pins':pins,'recipeSHA256':sha(__file__),'sleeveSectionPairs':len(rows),'summary':summary,'torsoSummary':torsoSummary,'sectionArchiveSHA256':sha(archive),'sectionArchive':str(archive),
        'analyzedDonor':{'vertices':len(display),'triangles':len(sourceTri),'sourceFrame':'Original donor units before any wearer cuts, in-memory direct simplification only','material':'Original selected donor UV/PBR retained, no new texture or native save'},
        'limits':['Oriented negative closed contours identify air-cavity sections, not a complete end-to-end wearer-port or capsule-clearance proof.','Nearest contour may belong to a connected torso/shoulder region; all components and ambiguous intersections are retained. No automatic fit or deletion.','Mapped contour centroid is a parameter witness under nonlinear construction mapping, not an exact mapped-polygon area centroid. Source units are uncalibrated; body/native distances are metres.','Temporary analysis clone only, no saved source17 or original data change, newcapture/rig/motion/inference/worker/player promotion. AllM0-M5/mobile/root played art remain open.']}
assert pins=={p:sha(p) for p in pins};(out/'contours.json').write_text(json.dumps(report,indent=2)+'\n');print('UNCUT_DONOR_CONTOURS_READY',json.dumps(summary),flush=True)
