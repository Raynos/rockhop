"""Exact47 field/PBR/action witness, collected during already necessary opens."""
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
c = runpy.run_path(str(HERE/'component.py'))
MERGE47 = {'path':'assets/blender/rider-rebuild/selected-sleeve-component47/merge47.py',
           'sha256':'e3d0c477977d96e1bb2adad5cca997f9b33897f8d7aa7fbde8c6f83953588d73'}


def capture_source():
    source = c['checked'](MERGE47).read_text()
    start = source.index("    helper = module(target['sourcePins']['inspectionHelper'],'merge47_inspection')")
    end = source.index("    write(pending_path.parent/(mode+'-witness.json')",start)
    body = source[start:end]
    opening = "    assert bpy.ops.wm.open_mainfile(filepath=str(checked(native)),use_scripts=False) == {'FINISHED'}\n"
    assert body.count(opening) == 1
    body = body.replace(opening,'')
    return 'def capture(mode,target,contract,bpy):\n'+body+(
        "    return {'parts':parts,'actions':actions,'rig':rig_state,'visibleMeshes':visible,\n"
        "            'referenceHidden':True,'maskReference':mask}\n")


def capture(mode,target,contract,bpy,methods):
    assert mode in ('source','target')
    scope = dict(methods)
    exec(compile(capture_source(),__file__,'exec'),scope)
    return scope['capture'](mode,target,contract,bpy)
