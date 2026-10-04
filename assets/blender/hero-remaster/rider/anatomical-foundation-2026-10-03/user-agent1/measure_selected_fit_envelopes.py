"""Read anatomical radial envelopes before authoring actual donor cage fit.

Record body/garment entries and exits along identical rays, including
missing/ambiguous starts. No mesh movement, fit claim, or clearance waiver.
"""
import argparse, gzip, hashlib, json, math, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,out=[Path(getattr(a,k)).resolve() for k in ['source','out']]
out.mkdir(parents=True,exist_ok=True);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pin=sha(source)
assert pin=='989855995983079d3207960f5e36feb734fe0e02987961d8f652c8cd26c3ae3f'
bpy.ops.wm.open_mainfile(filepath=str(source));g=bpy.data.objects['Actual selected donor, continuous elbow registration, unaccepted'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
def tree(obj):
    obj.data.calc_loop_triangles();return BVHTree.FromPolygons([v.co.copy() for v in obj.data.vertices],[tuple(t.vertices) for t in obj.data.loop_triangles],all_triangles=True)
bt=tree(body);gt=tree(g)
def exit(tree,center,direction):
    hits=[];origin=Vector(center);travel=0.;direction=Vector(direction)
    for step in range(12):
        q,n,t,d=tree.ray_cast(origin,direction,1.-travel)
        if q is None:break
        travel+=float(d);hits.append({'triangle':int(t),'nativePointM':list(q),'normalDotRay':float(n.dot(direction)),'radiusM':travel,'outward':bool(n.dot(direction)>0)})
        origin=q+direction*1e-5;travel+=1e-5
        if travel>=1.:break
    if not hits:return {'missing':True,'hits':[]}
    return {'missing':False,**{k:v for k,v in hits[0].items() if k!='outward'},'outwardFirstHit':hits[0]['outward'],'hits':hits}
rows=[]
def record(part,station,angle,center,direction):
    b=exit(bt,center,direction);cloth=exit(gt,center,direction)
    row={'part':part,'station':float(station),'angleRadians':float(angle),'centerNativeM':list(map(float,center)),'directionNative':list(map(float,direction)),'body':b,'garment':cloth}
    if not b['missing'] and not cloth['missing'] and b['outwardFirstHit']:
        row['firstGarmentHitOrientation']='outward' if cloth['outwardFirstHit'] else 'inward'
        row['prospectiveFirstHitEaseM']=max(0.,b['radiusM']+.002-cloth['radiusM']);row['prospectiveFirstHitRadiusRatio']=max(1.,(b['radiusM']+.002)/max(cloth['radiusM'],1e-12))
    rows.append(row)
for z in np.linspace(1.025,1.49,32):
    for angle in np.linspace(0,2*math.pi,64,endpoint=False):record('torso',z,angle,[.015,0,z],[math.cos(angle),math.sin(angle),0])
for side in ['R','L']:
    for segment in ['upperArm.','forearm.']:
        b=rig.data.bones[segment+side];head=np.array(list(b.head_local));tail=np.array(list(b.tail_local));axis=tail-head;axis/=np.linalg.norm(axis)
        guide=np.array([0,0,1]) if abs(axis[2])<.9 else np.array([1,0,0]);u=np.cross(axis,guide);u/=np.linalg.norm(u);v=np.cross(axis,u)
        for station in np.linspace(.05,.95,16):
            center=head+(tail-head)*station
            for angle in np.linspace(0,2*math.pi,48,endpoint=False):record(segment+side,station,angle,center,u*math.cos(angle)+v*math.sin(angle))
summary={}
for part in sorted({r['part'] for r in rows}):
    records=[r for r in rows if r['part']==part];valid=[r for r in records if 'prospectiveFirstHitEaseM' in r];ease=np.array([r['prospectiveFirstHitEaseM'] for r in valid]);ratio=np.array([r['prospectiveFirstHitRadiusRatio'] for r in valid])
    wall=np.array([r['garment']['hits'][1]['radiusM']-r['garment']['hits'][0]['radiusM'] for r in records if len(r['garment']['hits'])>=2 and not r['garment']['hits'][0]['outward'] and r['garment']['hits'][1]['outward']])
    summary[part]={'rays':len(records),'pairedBodyOutwardFirstHits':len(valid),'pairedGarmentOutwardFirstHits':sum(r['garment']['outwardFirstHit'] for r in valid),'pairedGarmentInwardFirstHits':sum(not r['garment']['outwardFirstHit'] for r in valid),'bodyMissing':sum(r['body']['missing'] for r in records),'garmentMissing':sum(r['garment']['missing'] for r in records),
                   'bodyInwardFirstHits':sum(not r['body']['missing'] and not r['body']['outwardFirstHit'] for r in records),'garmentInwardFirstHits':sum(not r['garment']['missing'] and not r['garment']['outwardFirstHit'] for r in records),
                   'positiveProspectiveEaseCount':int((ease>0).sum()),'prospectiveFirstHitEaseMPercentiles':np.percentile(ease,[0,50,95,100]).tolist() if len(ease) else [],'prospectiveFirstHitRadiusRatioPercentiles':np.percentile(ratio,[0,50,95,100]).tolist() if len(ratio) else [],
                   'garmentRaysWithAtLeastTwoHits':sum(len(r['garment']['hits'])>=2 for r in records),'garmentInwardThenOutwardFirstTwoHits':sum(len(r['garment']['hits'])>=2 and not r['garment']['hits'][0]['outward'] and r['garment']['hits'][1]['outward'] for r in records),
                   'firstEntryExitSpacingMPercentiles':np.percentile(wall,[0,50,95,100]).tolist() if len(wall) else [],'garmentRayHitLimitCount':sum(len(r['garment']['hits'])==12 for r in records)}
bodyDominant=[]
for vertex in body.data.vertices:
    weights=[(float(w.weight),body.vertex_groups[w.group].name) for w in vertex.groups if body.vertex_groups[w.group].name in rig.data.bones and rig.data.bones[body.vertex_groups[w.group].name].use_deform]
    bodyDominant.append(max(weights)[1] if weights else 'unweighted')
g.data.calc_loop_triangles();body.data.calc_loop_triangles();contacts=gt.overlap(bt);contactSamples=[]
for i,j in contacts[:128]:
    cloth=np.array([g.data.vertices[v].co[:] for v in g.data.loop_triangles[i].vertices]);bp=np.array([body.data.vertices[v].co[:] for v in body.data.loop_triangles[j].vertices]);contactSamples.append({'garmentTriangle':i,'bodyTriangle':j,'bodyDominantVertexBones':[bodyDominant[v] for v in body.data.loop_triangles[j].vertices],'garmentNativeXYZ':cloth.tolist(),'bodyNativeXYZ':bp.tolist()})
archive=out/'radial-rays.json.gz';archive.write_bytes(gzip.compress(json.dumps(rows,separators=(',',':')).encode(),mtime=0))
report={'status':'UNACCEPTED readonly anatomical radial fit-envelope inventory','sourceSHA256':pin,'recipeSHA256':sha(__file__),'clearanceProxyM':.002,'summary':summary,'rayCount':len(rows),'rayArchiveSHA256':sha(archive),'rayArchive':str(archive),'restBodyTrianglePairs':len(contacts),'bodyWitnesses':contactSamples,
        'limits':['Ray hits are capped12 surfaces within1m; local samples, not global signed-distance, all-triangle clearance or complete coverage. Missing and all first-hit orientations remain explicit.','First garment inward hit can be normal entry from air into a finite cloth wall; it must not be rejected merely because the body begins inside its own solid. Neither sign proves that a nominal skeletal center is inside the intended garment lumen.','Multiple entry/exit hits can be folded or inner walls. These records do not authorize global inward-face deletion.','Body ray can pass through a connected torso/arm region; large radius/ratio must not be used blindly as garment fit.','Ratios are prospective diagnostics, no geometry moved, no body vertex snaps, global sweep, rig or skin authoring.','Native17/PBR and failedcontrols remain frozen. Ten openings/2552body/1self still fail; no capture/inference/worker/player promotion, allM0-M5/mobile open/root sole judge.']}
assert pin==sha(source);(out/'envelopes.json').write_text(json.dumps(report,indent=2)+'\n');print('BODY_DONOR_ENVELOPES_READY',json.dumps(summary),flush=True)
