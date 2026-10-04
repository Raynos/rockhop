"""Read frozen source14 membership/rest fields without editing its native file."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source', required=True)
p.add_argument('--out', required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, out = Path(a.source).resolve(), Path(a.out).resolve()
sha = lambda x: hashlib.sha256(Path(x).read_bytes()).hexdigest()
expected = 'd3f05ff00755c0fb9e4245465092333ace538098e86eb44e4ad057e4c68d8996'
assert sha(source) == expected and not out.exists()
bpy.ops.wm.open_mainfile(filepath=str(source))
g = bpy.data.objects['Selected Hunyuan authored skin wearable, unaccepted']
rig = bpy.data.objects['Independent anatomical foundation rig']
assert len(g.data.vertices) == 6046 and len(rig.data.bones) == 51
g.data.calc_loop_triangles()
vertices = []
for v in g.data.vertices:
    fields = sorted([(g.vertex_groups[w.group].name, w.weight) for w in v.groups if w.weight > 0])
    assert all(name in rig.data.bones for name, _ in fields)
    vertices.append({'id': v.index, 'objectM': list(v.co),
                     'worldM': list(g.matrix_world @ v.co), 'weights': fields})
report = {'status': 'UNACCEPTED_SOURCE14_READ_ONLY_NATIVE_FIELDS',
          'sourceSHA256': expected, 'recipeSHA256': sha(__file__),
          'vertices': vertices,
          'triangles': [list(t.vertices) for t in g.data.loop_triangles],
          'garmentMatrixWorld': [list(row) for row in g.matrix_world],
          'rigMatrixWorld': [list(row) for row in rig.matrix_world],
          'bones': [{'name': b.name, 'parent': b.parent.name if b.parent else None,
                     'restMatrix': [list(row) for row in b.matrix_local]}
                    for b in rig.data.bones],
          'modifiers': [{'name': m.name, 'type': m.type,
                         'armature': m.object.name if m.type == 'ARMATURE' else None,
                         'preserveVolume': m.use_deform_preserve_volume if m.type == 'ARMATURE' else None}
                        for m in g.modifiers],
          'limits': ['Read membership, topology and rest transforms only; no source save, fit or weight edit.',
                     'Native moving failures remain independently declared by construction owner.']}
assert sha(source) == expected
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, separators=(',', ':')) + '\n')
print(json.dumps({'nativeVertices': len(vertices), 'triangles': len(report['triangles']),
                  'maximumInfluences': max(len(v['weights']) for v in vertices)}), flush=True)
