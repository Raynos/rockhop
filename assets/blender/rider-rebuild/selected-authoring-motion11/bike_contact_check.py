"""Independent native full-wearer finite contact witnesses, never art acceptance.

Parent guard: blender -b -t 2 --python-exit-code 1 --python bike_contact_check.py
 -- INPUT.json ACTUAL_BIKE_PACKAGE EXACT_BIKE_SURFACES.json FRESH_OUTPUT.json
Loads the complete selected weight02 native. Evaluates actual original meshes
and the hidden full anatomical reference with each object's own named field.
"""
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE))
from build import sha
from controls import rest_rows


def clip(poly,value):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        x,y=value(a),value(b)
        if x>=0:out.append(a)
        if (x<0)!=(y<0):out.append(a+(b-a)*(x/(x-y)))
    return out


def area_center(poly):
    if len(poly)<3:return 0.,Vector((0.,0.))
    total=0.;center=Vector((0.,0.));a=poly[0]
    for i in range(1,len(poly)-1):
        b,c=poly[i:i+2];area=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2
        total+=area;center+=(a+b+c)*(area/3)
    return total,center/total if total else center


def finite_gap(surface,rigid):
    """Exact finite projected intersections and extrema of affine triangle gaps."""
    compared=0;area_sum=0.;band_sum=0.;weighted_gap=0.;footprint=0.;low=None;high=None;witness=None
    for source in surface:
        normal=(source[1]-source[0]).cross(source[2]-source[0]);projected=abs(normal.y)/2
        if projected<1e-12:continue
        footprint+=projected
        if normal.y>=0:continue
        p=[Vector((v.x,v.z)) for v in source]
        def sy(v):return source[0].y-(normal.x*(v.x-source[0].x)+normal.z*(v.y-source[0].z))/normal.y
        for target in rigid:
            n=(target[1]-target[0]).cross(target[2]-target[0])
            if n.y<=1e-12:continue
            q=[Vector((v.x,v.z)) for v in target]
            if max(v.x for v in p)<min(v.x for v in q) or max(v.x for v in q)<min(v.x for v in p):continue
            if max(v.y for v in p)<min(v.y for v in q) or max(v.y for v in q)<min(v.y for v in p):continue
            orientation=1 if (q[1].x-q[0].x)*(q[2].y-q[0].y)-(q[1].y-q[0].y)*(q[2].x-q[0].x)>0 else -1
            polygon=p[:]
            for a,b in zip(q,q[1:]+q[:1]):
                polygon=clip(polygon,lambda v:orientation*((b.x-a.x)*(v.y-a.y)-(b.y-a.y)*(v.x-a.x)))
                if not polygon:break
            area,center=area_center(polygon)
            if area<1e-12:continue
            def gap(v):return sy(v)-(target[0].y-(n.x*(v.x-target[0].x)+n.z*(v.y-target[0].z))/n.y)
            values=[gap(v) for v in polygon];minimum=min(values);maximum=max(values)
            if low is None or minimum<low:low=minimum;witness={'riderTriangle':[list(v) for v in source],'bikeTriangle':[list(v) for v in target]}
            high=maximum if high is None else max(high,maximum);area_sum+=area;weighted_gap+=gap(center)*area;compared+=1
            band=clip(clip(polygon,lambda v:gap(v)+.001),lambda v:.001-gap(v))
            band_sum+=area_center(band)[0]
    return {'riderProjectedAreaM2':footprint,'positiveOverlapAreaM2':area_sum,'areaWithin1mmBandM2':band_sum,
            'coreOverlapFraction':area_sum/footprint if footprint else 0.,'overlapInBandFraction':band_sum/area_sum if area_sum else 0.,
            'areaWeightedSignedGapM':weighted_gap/area_sum if area_sum else None,'minimumSignedGapM':low,'maximumSignedGapM':high,
            'comparedFiniteTrianglePairs':compared,'minimumWitness':witness,'contactAccepted':False}


def triangles_bvh(triangles):
    vertices=[v for triangle in triangles for v in triangle]
    return BVHTree.FromPolygons(vertices,[(i,i+1,i+2) for i in range(0,len(vertices),3)],all_triangles=True) if vertices else None


def near_triangles(positions,indices,target,padding=.02):
    points=np.array([list(p) for triangle in target for p in triangle]);lo=points.min(0)-padding;hi=points.max(0)+padding
    triangles=positions[indices];rows=np.flatnonzero(np.all(triangles.max(1)>=lo,axis=1)&np.all(triangles.min(1)<=hi,axis=1))
    return [[Vector(p) for p in triangles[i]] for i in rows],rows


def evaluated(obj,to_bike,depsgraph):
    obj.hide_viewport=False;obj.hide_set(False)
    for modifier in obj.modifiers:
        if modifier.type=='ARMATURE':modifier.show_viewport=True
    bpy.context.view_layer.update()
    value=obj.evaluated_get(depsgraph);mesh=value.to_mesh(preserve_all_data_layers=True,depsgraph=depsgraph)
    try:
        assert len(mesh.vertices)==len(obj.data.vertices),('Source topology changed',obj.name)
        positions=np.empty((len(mesh.vertices),3),np.float64);mesh.vertices.foreach_get('co',positions.ravel())
        transform=np.asarray(to_bike@obj.matrix_world);positions=positions@transform[:3,:3].T+transform[:3,3]
        mesh.calc_loop_triangles();indices=np.empty((len(mesh.loop_triangles),3),np.int32);mesh.loop_triangles.foreach_get('vertices',indices.ravel())
        native=mesh.attributes.get('_NATIVE_ID');ids={int(v.value):i for i,v in enumerate(native.data)} if native else {i:i for i in range(len(mesh.vertices))}
        return positions,indices,ids
    finally:value.to_mesh_clear()


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==4
    config_path,package,surface_path,out=map(lambda p:Path(p).resolve(),args)
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-authoring-motion11')
    config=json.loads(config_path.read_text());receipt_path=package/'receipt.json';receipt=json.loads(receipt_path.read_text())
    assert receipt['status']=='NATIVE_BIKE_ACTIONS_UNACCEPTED' and receipt['source']==config
    for p in config['pins'].values():assert sha(ROOT/p['path'])==p['sha256'],p
    for p in (receipt['bakedNative'],receipt['nativeMatrices']):assert sha(ROOT/p['path'])==p['sha256'],p
    surfaces=json.loads(surface_path.read_text());assert surfaces['context']==config['pins']['bikeContext']
    assert surfaces['recipeSHA256']==config['pins']['surfaceRecipe']['sha256']
    assert surfaces['gripSelection']==config['pins']['gripSelection']
    assert [b['bike'] for b in surfaces['bikes']]==[r['bike'] for r in receipt['actions']]
    contract=json.loads((ROOT/config['pins']['contract']['path']).read_text());patches=json.loads((ROOT/config['pins']['patches']['path']).read_text())
    document=json.loads((ROOT/config['pins']['bikeContext']['path']).read_text());to_bike=Matrix(document['nativeToBike'])
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/config['pins']['native']['path']),use_scripts=False)
    rig=bpy.data.objects['RiderSkeleton'];assert rest_rows(rig)==contract['nativeRest']['bones'] and rig.matrix_world.is_identity
    rig.animation_data_clear();rig.animation_data_create()
    for b in rig.pose.bones:b.rotation_mode='QUATERNION'
    wanted=[r['name'] for r in receipt['actions']]
    with bpy.data.libraries.load(str(ROOT/receipt['bakedNative']['path']),link=False) as (_,data):data.actions=wanted
    actions=data.actions;objects=[*contract['specification']['meshNames'].values(),'RiderBody__FullAnatomyReference']
    assert all(n in bpy.data.objects for n in objects)
    assert all(not bpy.data.objects[n].data.shape_keys for n in objects), 'Weight02 Basis only; an old corrective cannot become this posture'
    report={'accepted':False,'completed':False,'expectedSamples':8,'status':'NATIVE_BIKE_FINITE_CONTACT_WITNESSES_UNACCEPTED','input':config,
            'packageReceipt':{'path':str(receipt_path.relative_to(ROOT)),'sha256':sha(receipt_path)},
            'bikeSurfaces':{'path':str(surface_path.relative_to(ROOT)),'sha256':sha(surface_path)},'samples':[],
            'limits':['Separate evaluated full anatomy and all dressed layers use their own original fields. No hidden reference is presumed equal to rendered FOUR.',
                'Finite triangle gap areas and actual triangle intersections are recorded. Centroid support and socket errors cannot certify them.',
                'Grip clearance samples use finite actual triangles; nearest distances alone do not qualify articulated finger wrap.',
                'Four key poses per bike do not establish continuous contact, CCD, GPU parity or played art acceptance. Dense runtime review remains required.']}
    for record,action in zip(receipt['actions'],actions):
        bike=next(b for b in surfaces['bikes'] if b['bike']==record['bike']);rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
        targets={'saddle':[[Vector(p) for p in t['pointsBike']] for t in bike['saddle']],
                 'pegs':[[Vector(p) for p in t['pointsBike']] for t in bike['pegs']]}
        for side in ('left','right'):targets['grip-'+side]=[[Vector(p) for p in t['pointsBike']] for t in bike['grips'][side]]
        target_bvh={k:triangles_bvh(t) for k,t in targets.items()}
        for frame in record['surfaceWitnessFrames']:
            bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();depsgraph=bpy.context.evaluated_depsgraph_get();sample={'action':record['name'],'frame':frame,'objects':{}};saddle_bvh={}
            for name in objects:
                if name=='RiderHoodie':continue # Upper garment is played; this witness concerns the actual bearing/contact regions.
                assert any(m.type=='ARMATURE' and m.object==rig for m in bpy.data.objects[name].modifiers), ('Own source skin must be evaluated',name)
                positions,indices,ids=evaluated(bpy.data.objects[name],to_bike,depsgraph);rows={}
                relevant=['saddle','pegs','grip-left','grip-right'] if 'Body' in name else ['saddle'] if name=='RiderJeans' else ['pegs'] if 'Boot' in name else ['grip-left' if name.endswith('.L') else 'grip-right']
                for kind in relevant:
                    local,source_rows=near_triangles(positions,indices,targets[kind]);bvh=triangles_bvh(local)
                    if kind=='saddle' and bvh:saddle_bvh[name]=bvh
                    crossings=bvh.overlap(target_bvh[kind]) if bvh else []
                    row={'nativeTrianglesInFiniteRegion':len(local),'triangleCrossingPairs':len(crossings),
                         'firstCrossingNativeTriangles':[int(source_rows[a]) for a,_ in crossings[:16]]}
                    if kind in ('saddle','pegs'):row['finiteGap']=finite_gap(local,targets[kind])
                    elif bvh:
                        distances=[]
                        for triangle in targets[kind]:
                            point=sum(triangle,Vector())/3;hit=bvh.find_nearest(point)
                            if hit[0] is not None:distances.append(hit[3])
                        row['finiteGripCentroidDistanceM']={'minimum':min(distances),'maximum':max(distances),'samples':len(distances)} if distances else None
                    rows[kind]=row
                if name=='RiderJeans':
                    rows['fixedUndersideCores']={s:finite_gap([[Vector(positions[ids[i]]) for i in r['nativeVertexIDs']] for r in patches['patches'][s]['core']['triangles']],targets['saddle']) for s in ('left','right')}
                if name=='RiderBody__FullAnatomyReference':
                    rows['fullOwnNamedField']=True;rows['fullOriginalVertexCount']=len(positions);rows['fullOriginalTriangleCount']=len(indices)
                sample['objects'][name]=rows
            sample['pelvicBodyJeansTriangleCrossings']={name:len(tree.overlap(saddle_bvh['RiderJeans']))
                for name,tree in saddle_bvh.items() if 'Body' in name and 'RiderJeans' in saddle_bvh}
            report['samples'].append(sample);out.write_text(json.dumps(report,indent=2)+'\n')
    report['nativeRestExactlyPreserved']=rest_rows(rig)==contract['nativeRest']['bones'];assert report['nativeRestExactlyPreserved']
    assert len(report['samples'])==report['expectedSamples'];report['completed']=True
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'output':str(out),'samples':len(report['samples']),'accepted':False}),flush=True)


if __name__=='__main__':main()
