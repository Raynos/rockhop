"""Measure body versus actual registered donor lumen clearance profiles.

Keep source18 immutable. Use oriented contour geometry and retained ambiguous
sections instead of nominal bone-centred radius ratios. No mesh fit or capture.
"""
import argparse, collections, gzip, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','section-recipe','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,recipe,out=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','section-recipe','out']]
out.mkdir(parents=True,exist_ok=True);assert not (out/'envelopes.json').exists(),'Keep frozen inventories'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,recipe]}
assert pins[str(source)]=='d97e5cb3e31110d1e6aa104032ab818094a170bc46cf9e0a612f4dd9ec8c680a'
assert pins[str(recipe)]=='ce72004823b6319719362defba4da3274c349e4615a181113805df4024b0bfdd'
bpy.ops.wm.open_mainfile(filepath=str(source));g=bpy.data.objects['Actual selected donor, measured lumen registration, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
def arrays(obj):
    obj.data.calc_loop_triangles();return np.array([v.co[:] for v in obj.data.vertices]),np.array([t.vertices[:] for t in obj.data.loop_triangles])
gp,gt=arrays(g);bp,bt=arrays(body)
definition=recipe.read_text();definition=definition[definition.index('def section('):definition.index('rows=[]')];exec(compile(definition,str(recipe),'exec'))
def frame(normal):
    guide=np.array([0,1,0]) if abs(normal[1])<.9 else np.array([1,0,0]);u=np.cross(normal,guide);u/=np.linalg.norm(u);return u,np.cross(normal,u)
def radial(contour,normal):
    center=np.array(contour['centroidXYZ']);points=np.array(contour['XYZ']);u,v=frame(normal);p=np.column_stack([(points-center)@u,(points-center)@v]);q=np.roll(p,-1,axis=0);delta=q-p;values=[];counts=[]
    for angle in np.linspace(0,2*np.pi,64,endpoint=False):
        d=np.array([np.cos(angle),np.sin(angle)]);den=d[0]*delta[:,1]-d[1]*delta[:,0];valid=np.abs(den)>1e-12;safe=np.where(valid,den,1)
        t=(p[:,0]*delta[:,1]-p[:,1]*delta[:,0])/safe;s=(p[:,0]*d[1]-p[:,1]*d[0])/safe
        hits=sorted(t[valid&(t>=0)&(s>=0)&(s<1)].tolist());values.append(hits[0] if hits else None);counts.append(len(hits))
    # Independently confirm the area centroid is inside the chosen contour.
    inside=False
    for x,y in zip(p,q):
        if (x[1]>0)!=(y[1]>0) and 0<(y[0]-x[0])*(-x[1])/(y[1]-x[1])+x[0]:inside=not inside
    return {'centroidInsideContour':inside,'firstRadiusM':values,'positiveBoundaryHitCounts':counts,'basisU':u.tolist(),'basisV':v.tolist()}
rows=[]
def measure(part,station,center,normal):
    gr=section(gp,gt,center,normal);br=section(bp,bt,center,normal)
    air=[(i,c) for i,c in enumerate(gr['contours']) if c.get('orientation')=='airCavity'];outer=[(i,c) for i,c in enumerate(br['contours']) if c.get('orientation')=='materialOuter']
    row={'part':part,'station':float(station),'planeCenterM':center.tolist(),'planeNormal':normal.tolist(),'garmentSection':gr,'bodySection':br}
    if air and outer:
        bi,b=min(outer,key=lambda x:x[1]['centroidOffsetFromReference']);gi,c=min(air,key=lambda x:np.linalg.norm(np.array(x[1]['centroidXYZ'])-np.array(b['centroidXYZ'])))
        cr=radial(c,normal);brr=radial(b,normal);row.update({'selectedGarmentContourIndex':gi,'selectedBodyContourIndex':bi,'sourceAirCentroidM':c['centroidXYZ'],'bodyOuterCentroidM':b['centroidXYZ'],'bodyMinusAirCentroidM':(np.array(b['centroidXYZ'])-np.array(c['centroidXYZ'])).tolist(),'sourceAirRays':cr,'bodyOuterRays':brr})
        local=bool(c['centroidOffsetFromReference']<=.10 and b['centroidOffsetFromReference']<=.05)
        usable=local and cr['centroidInsideContour'] and brr['centroidInsideContour'] and all(x is not None and x>1e-5 for x in cr['firstRadiusM']+brr['firstRadiusM'])
        row['localContourPair']=local;row['usableCenteredRadialPair']=usable
        if usable:
            rr=np.array(brr['firstRadiusM']);ar=np.array(cr['firstRadiusM']);row['bodyRadiusPlus4mmOverAirRadius']=(rr+.004)/ar;row['bodyRadiusPlus4mmOverAirRadius']=row['bodyRadiusPlus4mmOverAirRadius'].tolist();row['maximumRequiredUniformCrossSectionScale']=float(np.max((rr+.004)/ar))
            row['unscaledBodyRadiusMinusAirRadiusMPercentiles']=np.percentile(rr-ar,[0,50,95,100]).tolist()
    rows.append(row)
for side in ['R','L']:
    for name in ['upperArm.','forearm.']:
        b=rig.data.bones[name+side];h=np.array(b.head_local);t=np.array(b.tail_local);n=t-h;n/=np.linalg.norm(n)
        for station in np.linspace(.05,.95,16):measure(name+side,station,h+(t-h)*station,n)
for z in np.linspace(1.04,1.49,32):measure('torso',z,np.array([.015,0,z]),np.array([0.,0.,1.]))
summary={}
for part in sorted({r['part'] for r in rows}):
    records=[r for r in rows if r['part']==part];usable=[r for r in records if r.get('usableCenteredRadialPair')]
    summary[part]={'sections':len(records),'pairedContours':sum('selectedGarmentContourIndex' in r for r in records),'usableLocalCenteredPairs':len(usable),'scalePercentiles':np.percentile([r['maximumRequiredUniformCrossSectionScale'] for r in usable],[0,50,95,100]).tolist() if usable else [],'centroidGapMPercentiles':np.percentile([np.linalg.norm(r['bodyMinusAirCentroidM']) for r in usable],[0,50,95,100]).tolist() if usable else []}
archive=out/'sections.json.gz';archive.write_bytes(gzip.compress(json.dumps(rows,separators=(',',':')).encode(),mtime=0));assert len(json.loads(gzip.decompress(archive.read_bytes())))==96
report={'status':'UNACCEPTED registered actual-donor clearance envelope inventory','pins':pins,'recipeSHA256':sha(__file__),'sections':len(rows),'summary':summary,'archiveSHA256':sha(archive),'radialSamplesPerPair':64,'proposedClearanceM':.004,
        'limits':['No source/native mesh mutation, fit or capture. Original donor UV/PBR and immutable body/head/51bind retained.','Uniform radial scale is a measured cross-section proposal around separate air/body area centroids, not a complete cage deformation, minimum-clearance proof or visual acceptance. Plane sections are native metres.','Open/ambiguous/nonlocal/missing cavities remain archived and excluded from fit proposals, not silently filled. Ports, donor folded walls, torso/arm blends and unsupported end regions still need anatomical construction.','All M0-M5, art/wearing/rig/moving/mobile remain open. No inference, worker, Library or player promotion; parent alone judges.']}
assert pins=={p:sha(p) for p in pins};(out/'envelopes.json').write_text(json.dumps(report,indent=2)+'\n');print('REGISTERED_LUMEN_ENVELOPES_READY',json.dumps(summary),flush=True)
