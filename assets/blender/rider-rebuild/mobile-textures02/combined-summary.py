#!/usr/bin/env python3
"""Summarize one verified final composition; no quality or device judgment."""
import argparse, hashlib, json, struct
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('directory', type=Path)
p.add_argument('report', type=Path)
args = p.parse_args()
base = args.directory
def read(name):
    return json.loads((base / name).read_text())
composition = read('composition.json')
proof = read('decoded-parity.json')
loader = read('loader-probe.json')
runtime = read('uastc-rdo05-runtime-transcode.json')
native_runtime = read('native-runtime-reuse.json')
assert proof['pass'] and loader['pass']
assert native_runtime['pass'] and native_runtime['candidate']['sha256'] == composition['candidate']['sha256']
assert proof['candidate']['sha256'] == composition['candidate']['sha256'] == loader['candidateSha256']
path = Path(composition['candidate']['path'])
with path.open('rb') as f:
    header = f.read(20)
    doc = json.loads(f.read(struct.unpack_from('<I', header, 12)[0]))
with path.open('rb') as f:
    h = hashlib.sha256()
    while data := f.read(1024 * 1024):
        h.update(data)
assert h.hexdigest() == composition['candidate']['sha256']
assert len(runtime) == len(composition['maps']) == len(doc['images'])
assert all(f['allLevelsSucceeded'] for row in runtime for f in row['formats'])
# A shared image with a different sampler may need a separate GPU allocation.
samplers = {}
for texture in doc['textures']:
    samplers.setdefault(texture['extensions']['KHR_texture_basisu']['source'], set()).add(texture.get('sampler'))
assert all(len(s) == 1 for s in samplers.values()), 'Count separate sampler allocations explicitly'
gpu = {f['name']: sum(next(x['totalMipBytes'] for x in row['formats'] if x['name'] == f['name']) for row in runtime) for f in runtime[0]['formats']}
geometry = proof['geometry']
assert sum(m['vertices'] for m in loader['meshes']) == geometry['vertices']
assert sum(m['triangles'] for m in loader['meshes']) == geometry['triangles']
components = []
for name in ['boot-L', 'boot-R', 'glove-L', 'glove-R']:
    src = Path('docs/evidence/rider-rebuild/mobile-textures02/components01') / name / 'summary.json'
    row = json.loads(src.read_text())
    assert row['nativeASTCAndPinnedRuntimeBlockPixelProof']
    components.append({'component': name, 'summary': str(src), 'sourceBakerCheckpoint': row['sourceBakerCheckpoint'],
                       'sourceBakeMetadataSHA256': row['sourceBakeMetadataSHA256'], 'normalAngularDegrees': row['normalAngularDegrees'],
                       'normalOutlierCountsAboveDegrees': row['normalOutliers']['countsAboveDegrees'], 'alphaChangedPixels': row['alphaChangedPixels']})
selected_geometry = 101132532
selected_texture_wire = 54967384
selected_gpu = 226580144
field_path = Path('docs/evidence/rider-rebuild/mobile-mesh02/composition01-qualification.json')
field = json.loads(field_path.read_text())
packed_fields = [{'component': row['part'], 'vertices': row['result']['vertices'],
                  'recordedPoses': sum(b['recordedPoses'] for b in row['result']['bikes']),
                  'packedWeightSHA256': row['result']['packedWeights']['sha256'],
                  'allIntegerSums65535': row['result']['packedWeights']['allIntegerSums65535'],
                  'allPoseVertexErrorMeters': row['result']['allPoseVertexErrorMeters'],
                  'limitations': row['result']['limitations']} for row in field['parts']]
source_field_limits = []
for name in ['boot-L', 'boot-R', 'glove-L', 'glove-R']:
    suffix = '-skin03-first-ray-summary.json' if name.startswith('glove') else '-first-ray01-summary.json'
    src = Path('docs/evidence/rider-rebuild/mobile-mesh02') / (name + suffix)
    row = json.loads(src.read_text())
    source_field_limits.append({'component':name, 'path':str(src), 'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
                                'samples':row['samples'], 'nearestSourceErrors':row['errors'],
                                'firstBakeRay':row['firstBakeRay']})
orm_path = Path('docs/evidence/rider-rebuild/mobile-textures02/orm2k02/measurements.json')
orm_trial = json.loads(orm_path.read_text())
jeans_alpha = [row for row in orm_trial['ORMResolutionComparisons'] if row['image'] == 11]
assert len(jeans_alpha) == 1
result = {'accepted': False, 'candidate': composition['candidate'], 'sourceGraft': composition['sourceGraft'],
          'selectedSourceSHA256': composition['selectedSourceSHA256'], 'originalMasterSHA256': composition['originalMasterSHA256'],
          'metadataHashScope': composition['hashScope'], 'metadataHashes': {k:composition[k] for k in ['sourceFullMetadataCanonicalJSON_SHA256','candidateFullMetadataCanonicalJSON_SHA256','sourceRawJSONChunkSHA256','candidateRawJSONChunkSHA256']},
          'uniqueMaps': len(runtime), 'mipLevels': sum(r['levels'] for r in runtime),
          'successfulPinnedWASMTranscodes': sum(r['levels'] * len(r['formats']) for r in runtime),
          'everyMipASTCBlocksExactToNativeVerifiedSources': native_runtime['nativeVerifiedASTCBlocksExactEveryMip'],
          'everyMapBasePixelsExactToNativeASTCLinearDecode': native_runtime['nativeASTCLinearPixelsMatchPinnedRuntimeEveryMap'],
          'textureWireBytes': composition['textureBytes'], 'exactImageDedupWireSavedBytes': composition['identicalKTXDedupBytesSaved'],
          'textureGPUBytesFullMip': gpu, 'decodedGeometry': geometry,
          'combinedTextureAndGeometryStreamBytes': {name: size + geometry['decodedBytes'] for name,size in gpu.items()},
          'selectedCheckpointReferenceStreams': {'textureWireBytes': selected_texture_wire, 'ASTCMipBytes': selected_gpu, 'decodedGeometryBytes': selected_geometry},
          'reductionsVsSelectedCheckpoint': {'GLBWireBytes': 101885432-composition['candidate']['bytes'],
                                             'textureWireBytes': selected_texture_wire-composition['textureBytes'],
                                             'ASTCMipBytes': selected_gpu-gpu['ASTC4x4'], 'decodedGeometryBytes': selected_geometry-geometry['decodedBytes']},
          'nativeJoints': proof['nativeJoints'], 'nativeAnimationChannels': proof['nativeAnimationChannels'],
          'nativeJSONAndDecodedStreamsExactToGraft': True, 'protectedStreamsExactToSelectedCheckpoint': True,
          'allDeliveryMaterialTextureImageRecordsReferenced': proof['allMaterialTextureImageRecordsReferenced'],
          'componentIndependentCompressionProofs': components,
          'componentNewLevel0AlphaChangedPixels': sum(row['alphaChangedPixels'] for row in components),
          'jeansORMResolutionErrorAndAlphaProxy': {'evidence':str(orm_path), 'measurement':jeans_alpha[0]},
          'packedNativeFieldQualification': {'path':str(field_path), 'sha256':hashlib.sha256(field_path.read_bytes()).hexdigest(),
                                             'method':field['method'], 'parts':packed_fields, 'accepted':False},
          'independentSourceFieldBakeLimits':source_field_limits,
          'pinnedRuntimeTargetMeaning': {'ASTC4x4':{'basisTranscoderFormat':10,'blockPixels':[4,4],'bytesPerBlock':16},
                                        'BC7':{'basisTranscoderFormat':7,'blockPixels':[4,4],'bytesPerBlock':16},
                                        'RGBA32':{'basisTranscoderFormat':13,'bytesPerPixel':4}},
          'hoodieAndIdentityMaps': 'Source KTX bytes unchanged; hoodie albedo/ORM/normal remain4K. Jeans ORM is the independently measured2K resolution trial.',
          'hoodiePriorNormalCompressionLimit': {'meanDegrees': .299269, 'p99Degrees': 2.11, 'maxDegrees': 98.92657, 'pixelsAbove30Degrees': 46},
          'limits': ['Components remain unaccepted builder checkpoints; compare played final candidate before judging art.',
                     'Compression compares new bakedPNG fields, independent of source-field and native posed witness limits.',
                     'All-pixel normal outliers remain included; no UV occupancy exclusions.',
                     'GPU totals assume the pinned ASTC4x4/BC7 transcode path; actual phone support, upload memory and FPS are unmeasured.',
                     'Unique geometry/texture stream totals exclude animation/bind buffers, staging, driver allocations, renderer work and other assets.',
                     'Hoodie atlas prior native transfer maximum9.713mm at hem/nearest-corner38.304mm remains independent.',
                     'Visual/project90% milestone is not a wire-reduction quota. No production pin or deployment.']}
args.report.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k:result[k] for k in ['candidate','textureWireBytes','textureGPUBytesFullMip','combinedTextureAndGeometryStreamBytes','reductionsVsSelectedCheckpoint']}))
