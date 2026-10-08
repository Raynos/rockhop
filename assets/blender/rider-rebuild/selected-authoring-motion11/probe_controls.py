"""One neutral diagnostic of failed native01; no save, action, or angle search."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Matrix

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(HERE))
from controls import install
from build import sha


def rows(matrix): return [list(r) for r in matrix]


def main():
    args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
    source,out=map(Path,args);config=json.loads(source.read_text());contract=json.loads((ROOT/config['contract']['path']).read_text())
    for pin in (config['native'],config['contract']):assert sha(ROOT/pin['path'])==pin['sha256']
    assert hashlib.sha256((HERE/'controls.py').read_bytes()).hexdigest()=='721cff518ced2012aabb4f7f3a7b53d33f290470832962c992141b10829ed7b1'
    assert not out.exists() and out.resolve().is_relative_to(ROOT/'docs/evidence/rider-rebuild/selected-authoring-motion11')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(ROOT/config['native']['path']),link=False) as (_,data):data.objects=['RiderSkeleton']
    rig=data.objects[0];bpy.context.scene.collection.objects.link(rig)
    failure=None
    try:install(rig,contract)
    except AssertionError as error:failure=str(error)
    expected={b['name']:Matrix(b['matrix']) for b in contract['nativeRest']['bones']};result=[]
    for b in rig.pose.bones:
        original=b.name
        if original.startswith('CTRL-'):
            original=original.replace('CTRL-','DEF-',1)
            if original.startswith('DEF-palm.'):original=original.replace('DEF-palm.','PalmSocket.')
            if original.startswith('DEF-sole.'):original=original.replace('DEF-sole.','SoleSocket.')
        if original.startswith('MCH-target-'):original=original[len('MCH-target-'):]
        elif original.startswith('MCH-'):original=original[len('MCH-'):]
        target=expected.get(original)
        result.append({'name':b.name,'referenceName':original if target else None,
                       'parent':b.parent.name if b.parent else None,'head':list(b.head),'tail':list(b.tail),
                       'restHead':list(b.bone.head_local),'restTail':list(b.bone.tail_local),
                       'restMatrix':rows(b.bone.matrix_local),'poseMatrix':rows(b.matrix),'basis':rows(b.matrix_basis),
                       'restMatrixError':max(abs(b.bone.matrix_local[i][j]-target[i][j]) for i in range(4) for j in range(4)) if target else None,
                       'poseHeadErrorM':(b.matrix.translation-target.translation).length if target else None,
                       'constraints':[{'type':c.type,'subtarget':getattr(c,'subtarget',None),
                                       'poleSubtarget':getattr(c,'pole_subtarget',None),
                                       'errorLocation':c.error_location,'errorRotation':c.error_rotation}
                                      for c in b.constraints]})
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'accepted':False,'failure':failure,'bones':result},indent=2)+'\n')
    print(json.dumps({'failure':failure,'largestRestErrors':sorted([{'name':r['name'],'rest':r['restMatrixError'],'head':r['poseHeadErrorM']} for r in result if r['restMatrixError'] is not None],key=lambda r:r['rest'],reverse=True)[:12],
                      'largestHeadErrors':sorted([{'name':r['name'],'head':r['poseHeadErrorM']} for r in result if r['poseHeadErrorM'] is not None],key=lambda r:r['head'],reverse=True)[:12]}),flush=True)


if __name__=='__main__':main()
