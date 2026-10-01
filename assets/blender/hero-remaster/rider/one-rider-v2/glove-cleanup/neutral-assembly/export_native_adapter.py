"""Read-only actual native source-to-body matrices for later rig adaptation."""
import hashlib,json
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
ROOT=Path('/Users/raynos/projects/games/rockhop')
OUT=ROOT/'docs/evidence/hero-remaster/one-rider-v2/glove-cleanup/neutral-assembly'
FRESH=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2/fresh-anatomical-source.blend')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(FRESH);build=json.loads((OUT/'report.json').read_text())
neutral=json.loads((OUT.parent/'mpfb-trial2/neutral-anatomy/report.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(FRESH))
base=next(o for o in bpy.context.scene.objects if o.type=='MESH')
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
rows=[]
def asrows(m):return [list(row) for row in m]
for patch in build['patches']:
    side=patch['nativeSide'];frame=next(r['nativeFrame'] for r in neutral['hands'] if r['side']==side)
    axes=Matrix((frame['width'],frame['normal'],frame['length']))
    signs=Matrix.Diagonal(Vector((1 if side=='R' else -1,-1,-1)))
    rotation=Matrix(patch['rigidAlignmentMatrix']);linear=rotation@signs@axes
    transform=linear.to_4x4();transform.translation=Vector(patch['translation'])-linear@Vector(frame['wrist'])
    armToBody=transform@base.matrix_world.inverted()@arm.matrix_world
    bones={}
    for b in arm.data.bones:
        if b.name==f'wrist.{side}' or ((b.name.startswith('finger') or b.name.startswith('metacarpal') or b.name.startswith('lowerarm')) and b.name.endswith('.'+side)):
            bones[b.name]={'sourceHeadLocal':list(b.head_local),'sourceTailLocal':list(b.tail_local),'bodyHead':list(armToBody@b.head_local),'bodyTail':list(armToBody@b.tail_local),'nativeBoneBindToBodyMatrix':asrows(armToBody@b.matrix_local)}
    rows.append({'side':side,'sourceMeshLocalToBodyMatrix':asrows(transform),'bodyToSourceMeshLocalMatrix':asrows(transform.inverted()),'sourceArmatureLocalToBodyMatrix':asrows(armToBody),'nativeBones':bones})
assert before==sha(FRESH)
(OUT/'native-rig-adapter-matrices.json').write_text(json.dumps({'status':'Actual neutral authoring-frame matrices only; no final19bone adapter or accepted grip pose','nativeSource':str(FRESH),'nativeSourceSHA256Before':before,'nativeSourceSHA256After':sha(FRESH),'nativeMeshMatrixWorld':asrows(base.matrix_world),'nativeArmatureMatrixWorld':asrows(arm.matrix_world),'bodyCanonicalFrame':'BlenderZ-up native assembly; finalgameY-up/X-forward/socket mapping still required','hands':rows,'limits':['Finger and metacarpal nativeweights are retained in cleanmaster.','Derived nativebind matrices preserve anatomicalrestframe; do not replace existingphysics COM/IK/socket contract.','No nativebones added to runtime.'],'recipeSHA256':sha(Path(__file__))},indent=2)+'\n')
print('ACTUAL_NATIVE_TO_BODY_ADAPTER_MATRICES_FROZEN')
