"""Save the completed actual gloves before any sleeve operation may fail."""
import hashlib
import json
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[4]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1048576):h.update(block)
    return h.hexdigest()


def save(out,source_master,source_recipe):
    out=Path(out).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild') and out.is_dir()
    native=out/'UNACCEPTED-gloves-only-checkpoint.blend'
    assert not native.exists()
    ancestry={}
    for side in ('L','R'):
        name='ActualSelectedGlove.'+side
        obj=bpy.data.objects[name]
        assert obj.type=='MESH' and obj.vertex_groups
        path=out/(name+'-ancestry.npz');assert path.is_file()
        ancestry[name]={'path':str(path.relative_to(ROOT)),'sha256':sha(path),
                        'vertices':len(obj.data.vertices),'polygons':len(obj.data.polygons)}
    # The caller must invoke this immediately after both Surgery.finish calls,
    # before moving or replacing any hoodie data. Saving preserves actual mesh,
    # corner UVs, materials, named weights, rig and packed maps, unlike ancestry.
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    report={'status':'UNACCEPTED_GLOVES_CONSTRUCTED_SLEEVE_NOT_AUTHORED',
            'acceptedArt':False,'geometryGatesPassed':False,'movingReviewPassed':False,
            'sourceMaster':source_master,'sourceRecipe':source_recipe,
            'gloveObjects':ancestry,'native':{'path':str(native.relative_to(ROOT)),'sha256':sha(native)}}
    (out/'gloves-only-checkpoint.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
