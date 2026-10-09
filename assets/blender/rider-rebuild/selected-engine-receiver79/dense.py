"""Exact dense28 full triangles on an actual separately reopened compact77."""
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
h = runpy.run_path(str(HERE/'component.py'))
ORIGINAL = {'path':'assets/blender/rider-rebuild/selected-sleeve-rebuild28/qualify.py',
            'sha256':'d4e261170c8d754ca97eec329d2958ad88e059a5f87903fc862207d87087710c'}


def transformed_source():
    source = h['checked'](ORIGINAL).read_text()
    changes = {"ROOT/'harness/out/rider-rebuild/selected-sleeve-rebuild28'":
                   "ROOT/'harness/out/rider-rebuild/selected-engine-receiver79'",
               "'recipeSHA256': sha(__file__),":
                   "'recipeSHA256': sha(WRAPPER), 'originalQualifier': ORIGINAL,"}
    for old,new in changes.items():
        assert source.count(old) == 1
        source = source.replace(old,new)
    anchor = "    row = {'acceptedArt': False"
    source = source.replace(anchor,"    contact = runpy.run_path(str(CONTACT))\n"
        "    contact_inputs = contact['capture'](bpy,np,helper)\n"+anchor)
    source = source.replace("'fullTrianglesNoRadialCrop': True, 'result': result,",
        "'fullTrianglesNoRadialCrop': True, 'result': result,\n"
        "           'contactRecipe': {'path':str(CONTACT.relative_to(ROOT)), 'sha256':sha(CONTACT)}, 'contactInputs':contact_inputs,")
    return source


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    report = json.loads(Path(args[0]).read_text())
    h['native_gate'](report,h['read'](report['input']))
    namespace = {'__name__':'receiver79_exact_dense28','__file__':str(h['checked'](ORIGINAL)),
                 'WRAPPER':__file__,'ORIGINAL':ORIGINAL,'CONTACT':HERE/'contact.py'}
    exec(compile(transformed_source(),namespace['__file__'],'exec'),namespace)
    namespace['main']()
