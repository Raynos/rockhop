"""Parent original guard only: one exact inherited face proof, no mesh edits/save.

blender -b -t2 --python-exit-code 1 --python native-proof.py -- NEW_PROOF_OUT
"""
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
import proof as p

def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==1
    out=Path(args[0]).resolve();assert out.is_relative_to(p.ROOT/'harness/out/rider-rebuild/selected-boot-surface67') and not out.exists()
    out.mkdir(parents=True)
    report={'status':'PARTIAL_NATIVE67_BEFORE_INPUT_PINS','acceptedArt':False,
        'recipeSHA256':p.sha(__file__),'proofRecipeSHA256':p.sha(p.__file__),
        'targetFaceId':p.TARGET,'ownSourceFaceId':p.OWN,'limits':'One inherited bearing proof only. No native policy change, construction, save, bake or qualification.'}
    def write():(out/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
    write()
    try:
        report['production']=p.pin(p.PRODUCTION,p.PRODUCTION_SHA)
        report['native63']=p.pin(p.NATIVE63,p.NATIVE63_SHA);report['source34']=p.pin(p.NATIVE34,p.NATIVE34_SHA)
        p.pin(p.ENGINE,p.ENGINE_SHA);p.pin(p.WITNESS,p.WITNESS_SHA);p.pin(p.ADMISSION63,p.ADMISSION63_SHA)
        admission=p.load(p.ADMISSION63,'proof67_admission63');constructor=json.loads(admission.RECEIPT.read_text());admission.pin(admission.RECEIPT,admission.RECEIPT_SHA)
        dense=admission.array_package(constructor['sourceArrayPackage']);candidate=admission.array_package(constructor['candidate'])
        report['status']='PARTIAL_NATIVE67_BEFORE_NATIVE_READ';write()
        engine=p.load(p.ENGINE,'proof67_engine25');witness=p.load(p.WITNESS,'proof67_witness31')
        bpy.ops.wm.open_mainfile(filepath=str(p.NATIVE63))
        source=bpy.data.objects['ActualSelectedBoot.L'];target=bpy.data.objects['Production.full.ActualSelectedBoot.L'];rig=bpy.data.objects['RiderSkeleton']
        sources={name:bpy.data.objects[name] for name in ['ActualSelectedBoot.L','ActualSelectedBoot.R']}
        before=witness.retained(sources,rig);assert before==json.loads(p.PRODUCTION.read_text())['sourceWitness'];report['sourceWitnessExact']=True
        sp=engine.points(source);sf=engine.triangles(source);tp=engine.points(target);tf=engine.triangles(target)
        assert np.array_equal(sp.ravel(),dense['positions']) and np.array_equal(sf.ravel(),dense['triangles'])
        assert np.array_equal(tp.ravel(),candidate['positions']) and np.array_equal(tf.ravel(),candidate['triangles'])
        attribute=target.data.attributes['ProductionOriginalVertex'];assert attribute.domain=='POINT' and attribute.data_type=='INT'
        original=np.empty(len(tp),np.int32);attribute.data.foreach_get('value',original)
        assert np.array_equal(original,candidate['originalVertexIds'])
        assert np.array_equal(original[tf[p.TARGET]],sf[p.OWN])
        triangle=tp[tf[p.TARGET]];own=sp[sf[p.OWN]];assert np.array_equal(triangle,own)
        centroid=triangle.mean(0);query=Vector(centroid);normal=np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0]);normal/=np.linalg.norm(normal)
        target_material=target.data.polygons[p.TARGET].material_index;source_material=source.data.polygons[p.OWN].material_index
        assert target_material==source_material==int(candidate['faceMaterialIds'][p.TARGET])==int(dense['faceMaterialIds'][p.OWN])
        report.update(targetOriginalVertexIds=original[tf[p.TARGET]].tolist(),ownSourceOriginalVertexIds=sf[p.OWN].tolist(),
            targetPositions=triangle.tolist(),ownSourcePositions=own.tolist(),centroidFloat64=centroid.tolist(),queryFloat32=list(query),
            targetGeometricNormal=normal.tolist(),ownSourceGeometricNormal=normal.tolist(),ownSourceNormalDot=float(normal@normal),
            ownSourceCentroidDistanceM=float(np.linalg.norm(centroid-own.mean(0))),materialsExact=True,materialIndex=target_material,
            status='PARTIAL_NATIVE67_BEFORE_FULL_BVH');write()
        tree=engine.tree(sp,sf);near=tree.find_nearest(query);assert near[0] is not None
        bearing_id=int(near[2]);tri=sp[sf[bearing_id]];bn=np.cross(tri[1]-tri[0],tri[2]-tri[0]);bn/=np.linalg.norm(bn)
        report['fullBVHNearest']={'sourceFaceId':bearing_id,'point':list(near[0]),'distanceM':float(near[3]),
            'originalVertexIds':sf[bearing_id].tolist(),'positions':tri.tolist(),'geometricNormal':bn.tolist(),'normalDot':float(normal@bn)}
        report['status']='PARTIAL_NATIVE67_BEARING_SAVED_BEFORE_OWN_FACE';write()
        own_tree=engine.tree(own,np.array([[0,1,2]],np.int32));own_near=own_tree.find_nearest(query);assert own_near[0] is not None
        report['ownFaceBVHNearest']={'sourceFaceId':p.OWN,'point':list(own_near[0]),'distanceM':float(own_near[3])}
        report['sourceWitnessUnchangedAfterProbe']=before==witness.retained(sources,rig)
        report['raw63BytesUnchanged']=p.sha(p.NATIVE63)==p.NATIVE63_SHA;report['source34BytesUnchanged']=p.sha(p.NATIVE34)==p.NATIVE34_SHA
        report['status']='CONFIRMED_EXACT_INHERITED_FACE_NATIVE_BEARING_UNACCEPTED';p.validate(report);write()
    except Exception as error:
        report.update(status='REJECTED_OR_INCOMPLETE_NATIVE67_PROOF',failure=repr(error));write();raise
if __name__=='__main__':main()
