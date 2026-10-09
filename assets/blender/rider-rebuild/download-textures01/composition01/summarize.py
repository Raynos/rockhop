#!/usr/bin/env python3
"""Summarize pinned composition streams and independently measured texture proof."""
import argparse, hashlib, json, struct
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('directory', type=Path)
parser.add_argument('report', type=Path)
args = parser.parse_args()
base = args.directory
atlas = base.parent / 'atlas01'
def read_json(path):
    return json.loads(path.read_text())
def glb_json(path):
    with path.open('rb') as f:
        header = f.read(20)
        assert header[:4] == b'glTF'
        return json.loads(f.read(struct.unpack_from('<I', header, 12)[0]))
def streams(doc):
    rows = []
    views = set()
    for mi, mesh in enumerate(doc['meshes']):
        for pi, primitive in enumerate(mesh['primitives']):
            fields = {}
            for key, index in {**primitive['attributes'], 'indices': primitive['indices']}.items():
                accessor = doc['accessors'][index]
                view = doc['bufferViews'][accessor['bufferView']]
                views.add(accessor['bufferView'])
                fields[key] = {'count': accessor['count'], 'componentType': accessor['componentType'],
                               'type': accessor['type'], 'normalized': accessor.get('normalized', False),
                               'decodedBufferViewBytes': view['byteLength'],
                               'byteStride': view.get('byteStride')}
            rows.append({'mesh': mi, 'primitive': pi, 'fields': fields})
    return {'primitives': rows, 'totalPrimitiveVertices': sum(r['fields']['POSITION']['count'] for r in rows),
            'totalIndices': sum(r['fields']['indices']['count'] for r in rows),
            'uniqueGeometryViews': len(views),
            'decodedGeometryStreamBytesIncludingPadding': sum(doc['bufferViews'][v]['byteLength'] for v in views),
            'scope': 'Unique decoded vertex/index buffer-view streams, including stride padding; excludes textures, animation, bind matrices, renderer allocations and staging copies'}
inventory = read_json(atlas / 'inventory.json')
encoded = read_json(atlas / 'uastc-rdo05-encode.json')
runtime = read_json(atlas / 'uastc-rdo05-runtime-transcode.json')
proof = read_json(atlas / 'uastc-rdo05-astc-proof.json')
metrics = read_json(atlas / 'uastc-rdo05-astc-decoded-difference.json')
assert len(encoded) == len(runtime) == len(proof) == len(metrics) == 13
assert all(f['allLevelsSucceeded'] for row in runtime for f in row['formats'])
assert all(row['astcSoftwareDecodedRGBAIdenticalToRuntimeRGBA'] and all(x['nativeBlocksByteIdentical'] for x in row['levels']) for row in proof)
candidate = read_json(base / 'ktx-repack.json')
candidate_path = Path(candidate['output'])
h = hashlib.sha256()
with candidate_path.open('rb') as f:
    while chunk := f.read(1024 * 1024):
        h.update(chunk)
assert h.hexdigest() == candidate['sha256']
graft = glb_json(Path(inventory['source']))
doc = glb_json(candidate_path)
texture_gpu = {f['name']: sum(next(x['totalMipBytes'] for x in row['formats'] if x['name'] == f['name']) for row in runtime) for f in runtime[0]['formats']}
geometry = streams(doc)
result = {'accepted': False, 'candidate': candidate, 'sourceGraft': {k: inventory[k] for k in ['source', 'sourceBytes', 'sourceSha256']},
          'texturePNGBytes': inventory['originalTextureBytes'], 'textureKTX2Bytes': sum(r['bytes'] for r in encoded),
          'maps': len(runtime), 'mipLevels': sum(r['levels'] for r in runtime),
          'successfulPinnedWASMTranscodes': sum(r['levels'] * len(r['formats']) for r in runtime),
          'textureGPUBytesFullMip': texture_gpu, 'sourceLevel0RGBAPixels': sum(r['width'] * r['height'] for r in metrics),
          'level0AlphaChangedPixels': sum(r['alpha']['changedPixels'] for r in metrics),
          'nativeASTCBlocksMatchPinnedRuntimeEveryMip': True, 'nativeASTCLinearPixelsMatchRuntimeRGBAEveryMap': True,
          'sourceGraftArrays': streams(graft), 'candidateDecodedGeometry': geometry,
          'combinedTextureAndGeometryStreamBytes': {k: v + geometry['decodedGeometryStreamBytesIncludingPadding'] for k, v in texture_gpu.items()},
          'nativeJoints': sum(len(s['joints']) for s in doc['skins']), 'nativeAnimationChannels': sum(len(a['channels']) for a in doc['animations']),
          'hoodieNewMapMetrics': [r for r in metrics if r['image'] in [7, 8, 12]],
          'hoodieNormalOutliers': read_json(atlas / 'normal-outliers.json'),
          'limits': ['Texture errors compare to the atlas PNG graft, not original dense hoodie.',
                     'Software ASTC linear profile cannot prove sRGB GPU filtering or moving appearance; BC7 decoded pixels not measured.',
                     'Atlas native transfer max9.713mm at hem; nearest-corner field outliers38.304mm remain independent unaccepted limits.',
                     'Geometry04 checkpoint is unaccepted art; protected byte parity proves storage preservation only.',
                     'Stream totals exclude animation/bind buffers, upload copies, decoded staging, driver alignment and other assets; actual device memory remains unmeasured.']}
args.report.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['accepted', 'textureKTX2Bytes', 'textureGPUBytesFullMip', 'combinedTextureAndGeometryStreamBytes', 'nativeJoints', 'nativeAnimationChannels']}))
