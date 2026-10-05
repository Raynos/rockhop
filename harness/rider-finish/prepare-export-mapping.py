"""Prepare exact-coordinate correspondence for legacy cheek without identity attrs.

No nearest match/tolerance. All native cheek points must be distinct; exported
position bytes must exactly match converted native Float32 coordinates. Verify
all semantic four-field weights. Body/head/boxer use their serialized NativeIDs.
"""
import argparse, gzip, hashlib, json, struct
from pathlib import Path
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('glb'); p.add_argument('native_dir'); p.add_argument('out'); p.add_argument('--contract')
a = p.parse_args(); glb, native_dir, out = Path(a.glb), Path(a.native_dir), Path(a.out)
assert not out.exists()
sha = lambda b: hashlib.sha256(b).hexdigest()
raw = glb.read_bytes(); size = struct.unpack_from('<I', raw, 12)[0]; d = json.loads(raw[20:20+size]); binary = raw[28+size:]
r = json.loads((native_dir/'report.json').read_text()); rest_bytes = (native_dir/r['rest']['path']).read_bytes(); assert sha(rest_bytes) == r['rest']['sha256']; rest = json.loads(gzip.decompress(rest_bytes))
assert len(d['skins']) == 1
names = [d['nodes'][i]['name'] for i in d['skins'][0]['joints']]
assert sorted(names) == sorted(rest['jointOrder'])
def accessor(index):
    x = d['accessors'][index]; view = d['bufferViews'][x['bufferView']]
    formats = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}
    widths = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}; fmt = '<'+formats[x['componentType']]*widths[x['type']]
    start = view.get('byteOffset', 0)+x.get('byteOffset', 0); stride = view.get('byteStride', struct.calcsize(fmt))
    return [struct.unpack_from(fmt, binary, start+i*stride) for i in range(x['count'])]
regions = {}
for region, node_name in [('body', 'Finish body FOUR'), ('head', 'Finish head FOUR'), ('boxer', 'Finish boxer FOUR'), ('cheek', 'Finish coherent cheek')]:
    node = next(n for n in d['nodes'] if n.get('name') == node_name)
    primitives = d['meshes'][node['mesh']]['primitives']; assert len(primitives) == 1
    attrs = primitives[0]['attributes']; row = {'exportName': node_name}
    if '_NATIVE_ID' not in attrs:
        xyz = rest['parts'][region]['xyz']; world = rest['parts'][region]['objectWorld']
        f32 = lambda x: struct.unpack('<f', struct.pack('<f', x))[0]
        def exported_position(point):
            q = [sum(row[k]*point[k] for k in range(3))+row[3] for row in world[:3]]
            return tuple(f32(x) for x in (q[0], q[2], -q[1]))
        lookup = {exported_position(point): i for i, point in enumerate(xyz)}
        assert len(lookup) == len(xyz), 'Ambiguous native coordinate aliases, no correspondence inferred'
        positions = accessor(attrs['POSITION']); assert all(v in lookup for v in positions), 'Exact-coordinate source mapping failed'
        ids = [lookup[v] for v in positions]; joints, weights = accessor(attrs['JOINTS_0']), accessor(attrs['WEIGHTS_0'])
        maximum = 0
        for vertex, js, ws in zip(ids, joints, weights):
            fields = dict(zip(names, [0.]*len(names)))
            for j, w in zip(js, ws): fields[names[j]] += w
            expected = dict(zip(rest['jointOrder'], rest['parts'][region]['fourWeights'][vertex]))
            maximum = max(maximum, max(abs(fields[n]-expected[n]) for n in names))
        assert maximum < 2e-7, 'Source four-slot semantic field differs from export'
        row.update({'nativeVertexIDs': ids, 'correspondence': {'method': 'Exact Float32 native objectWorld then [x,z,-y] coordinates, no tolerance/nearest mapping; unique native coordinate classes independently established', 'nativeVertices': len(xyz), 'exportRows': len(ids), 'coveredNativeVertices': len(set(ids)), 'maximumNamedFourWeightDifference': maximum, 'normalCornerIdentity': 'Unmeasured; absence of corner IDs remains explicit'}})
    if region == 'head' and a.contract:
        contract = json.loads(Path(a.contract).read_text())
        row['protectedNativeVertexIDs'] = contract['scope']['headProtectedCompleteAliasIDs']
        assert all(0 <= i < len(rest['parts'][region]['xyz']) for i in row['protectedNativeVertexIDs'])
        row['protectedMaskContractSHA256'] = sha(Path(a.contract).read_bytes())
        row['protectedMaskAuthority'] = 'Original head native identities preserved by separately pinned reopen preservation report; derived appended IDs excluded.'
    regions[region] = row
output = {'status': 'UNACCEPTED_SAME_NATIVE_EXPORT_CORRESPONDENCE', 'glbSHA256': sha(raw), 'nativeSourceSHA256': list(r['sourcePins'].values())[0], 'nativeReportSHA256': sha((native_dir/'report.json').read_bytes()), 'regions': regions}
out.write_text(json.dumps(output, indent=2)+'\n')
print(json.dumps({'glbSHA256': output['glbSHA256'], 'cheek': regions['cheek']['correspondence']}))
