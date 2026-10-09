"""Parent-guarded read-only RIGHT intake for the unchanged67 construction math.

--python census.py -- REVIEWED_RIGHT_REPAIR_SHA NEW_RIGHT_CENSUS_OUTPUT
No native save, optimizer, shape edit, bone remap, bake or scene acceptance.
"""
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prepare as p

REPAIR=p.ROOT/'docs/evidence/rider-rebuild/selected-boot-family75/right-repair.json'
REOPEN=p.ROOT/'harness/out/rider-rebuild/selected-boot-native70/reopen01/reopen.json'
REOPEN_SHA='db3f0dbe7a3d610da1d2df8123220a5bc7ebf95d4d3f87157defaf3604c9c3fa'
QUALIFY=p.ROOT/'assets/blender/rider-rebuild/selected-boot-native70/reopen/qualify.py'
QUALIFY_SHA='65d4e0fc435df1ed332b847522de085caaceae9fd94f1fe14ed0f064fb766212'


def read_array(collection,attribute,width,dtype):
    result=np.empty((len(collection),width),dtype);collection.foreach_get(attribute,result.ravel());return result


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    out=Path(args[1]).resolve();assert out.is_relative_to(p.ROOT/'harness/out/rider-rebuild/selected-boot-family75') and not out.exists()
    out.mkdir(parents=True)
    report={'status':'PARTIAL_RIGHT_NATIVE_SOURCE_INTAKE','acceptedArt':False,'sourceObject':'ActualSelectedBoot.R',
        'recipeSHA256':p.intake.sha(__file__),'limits':'Actual right source census only; no candidate, pair, bake, budget, contact or art acceptance.'}
    def write():(out/'census.json').write_text(json.dumps(report,indent=2)+'\n')
    write()
    try:
        report['rightRepair']=p.intake.pin(REPAIR,args[0]);finding=json.loads(REPAIR.read_text())
        assert finding['status']=='COMPLETE_RIGHT_LOCAL_REPAIR_SEED_NATIVE_SOURCE_CENSUS_REQUIRED'
        report['qualifiedLeftReopen']=p.intake.pin(REOPEN,REOPEN_SHA);reopen=json.loads(REOPEN.read_text())
        assert reopen['status']=='SAVED_NATIVE70_REST_READBACK_PASSED_UNACCEPTED' and reopen['savedNativeBytesUnchanged'] and reopen['sourceMasterBytesUnchanged']
        p.intake.pin(QUALIFY,QUALIFY_SHA);q=p.intake.load(QUALIFY,'family75_qualified70_readback');_,whole=q.dependencies()
        production=json.loads(q.PRODUCTION.read_text());q.metadata(production,q.PRODUCTION_SHA)
        report['native70']=p.intake.pin(p.NATIVE,p.NATIVE_SHA);report['production70']=p.intake.pin(p.PRODUCTION,p.PRODUCTION_SHA)
        report['prepareRecipe']=p.intake.pin(Path(p.__file__),p.intake.sha(p.__file__))
        p.intake.pin(p.ROOT/finding['recipe']['path'],finding['recipe']['sha256'])
        p.intake.pin(p.ROOT/finding['preflight']['path'],finding['preflight']['sha256'])
        preflight=json.loads((p.ROOT/finding['preflight']['path']).read_text())
        p.intake.pin(p.ROOT/preflight['recipe']['path'],preflight['recipe']['sha256'])
        p.intake.pin(p.ROOT/preflight['source']['path'],preflight['source']['sha256'])
        source_json=json.loads((p.ROOT/preflight['source']['path']).read_text())
        for item in [source_json['recipe'],source_json['arrays']]:p.intake.pin(p.ROOT/item['path'],item['sha256'])
        cpu=p.intake.arrays(source_json['arrays'])
        import bpy
        engine=p.intake.load(q.ENGINE,'family75_source_engine25');witness=p.intake.load(q.WITNESS,'family75_source_witness31')
        bpy.ops.wm.open_mainfile(filepath=str(p.NATIVE),use_scripts=False)
        rig=bpy.data.objects['RiderSkeleton'];sources={name:bpy.data.objects[name] for name in production['sourceWitness']['sources']}
        before=witness.retained(sources,rig);diff,actual,expected=whole.comparison(before,production['sourceWitness'])
        file=out/'source-witness.json';file.write_text(json.dumps({'actual':actual,'expected':expected,'diff':diff},indent=2)+'\n')
        report['wholeSourceWitness']=p.intake.pin(file,p.intake.sha(file));write();assert diff['equal'] and len(rig.data.bones)==75
        source=sources['ActualSelectedBoot.R'];positions=engine.points(source).astype('<f4');triangles=engine.triangles(source)
        assert np.array_equal(positions.ravel(),cpu['RPositions']) and np.array_equal(triangles.ravel(),cpu['RTriangles'])
        names=[g.name for g in source.vertex_groups];assert names==['DEF-foot.R','DEF-toe.R','DEF-shin.R.001']
        assert all(name in rig.data.bones for name in names)
        arrays={'positions':positions,'triangles':triangles,'triangleLoopIds':read_array(source.data.loop_triangles,'loops',3,np.int32),
            'vertexNormals':read_array(source.data.vertices,'normal',3,np.float32),
            'cornerNormals':read_array(source.data.corner_normals,'vector',3,np.float32),
            'namedWeights':engine.skin_rows(source,names).astype('<f4'),
            'faceMaterialIds':np.array([tri.material_index for tri in source.data.loop_triangles],'<i4')}
        for i,layer in enumerate(source.data.uv_layers):arrays['uvLayer'+str(i)]=read_array(layer.data,'uv',2,np.float32)
        report['sourceArrayPackage']=dict(p.package(out/'exact-right-source-arrays.bin',arrays),groupNames=names,
            uvLayerNames=[layer.name for layer in source.data.uv_layers],coordinateFrame='Exact original right mesh local meters; source native75 bind unchanged.')
        report.update(sourceVertices=len(positions),sourceTriangles=len(triangles),sourceWitnessExact=True,
            sourceMatchesActualPreflightGeometry=True,sourceNormals='Native vertex normals read from pinned native70; no CPU proxy substitution.')
        write();assert before==witness.retained(sources,rig)
        p.intake.pin(p.NATIVE,p.NATIVE_SHA);p.intake.pin(p.PRODUCTION,p.PRODUCTION_SHA)
        report.update(status='ACTUAL_RIGHT_NATIVE_SOURCE_CENSUS_COMPLETE_UNACCEPTED',sourceInputBytesUnchanged=True);write()
    except Exception as error:
        report.update(status='REJECTED_RIGHT_NATIVE_SOURCE_CENSUS',failure=repr(error));write();raise


if __name__=='__main__':main()
