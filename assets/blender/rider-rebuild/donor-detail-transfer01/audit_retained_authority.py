"""Light preflight: glove prototype atlas risk and existing hoodie bake authority."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
PREP = ROOT/'assets/blender/hero-remaster/rider/finish-2026-10-05/wardrobe/data'
source = Path(__file__).resolve().parent.parent/'donor-appearance-audit01/measure-uv-transfer.py'
spec = importlib.util.spec_from_file_location('read_only_uv_chart_measurement', source)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
output = Path(sys.argv[1]).resolve(); assert not output.exists()
dense_path = PREP/'prep02/gloves/cleaned-donor.npz'; proto_path = PREP/'prep02/gloves/retopology-prototype.npz'
cavity_path = PREP/'glove-cavity08/open-glove-source.npz'
dense, proto, cavity = [dict(np.load(p)) for p in (dense_path, proto_path, cavity_path)]
chart, atlas = module.uv_charts(dense['faces'], dense['originalCornerUV'])
lookup = {int(value): i for i, value in enumerate(dense['originalTriangleRows'])}
point_rows = np.asarray([lookup[int(row)] for row in proto['originalTriangleRows']])
points_chart = chart[point_rows]
counts = {}
for name, faces in [('closedPrototype', proto['faces']), ('actualOpenCavity08Source', cavity['faces'])]:
    corners = points_chart[faces]
    counts[name] = {'triangles': len(faces), 'mixedOriginalUVChartTriangles': int(np.any(corners != corners[:, :1], axis=1).sum())}
boot_lineage = ROOT/'harness/out/rider-rebuild/selected-boot04/executed-input-uv-lineage-R.npz'
boot_check = {'executedMappingMeasured': False}
if boot_lineage.exists():
    boot = dict(np.load(boot_lineage)); boot_dense_path = PREP/'prep02/boots/cleaned-donor.npz'
    boot_dense = dict(np.load(boot_dense_path)); boot_charts, boot_atlas = module.uv_charts(boot_dense['faces'], boot_dense['originalCornerUV'])
    ids = boot['cornerDenseTriangleRows']
    assert np.array_equal(boot_dense['faces'][ids], boot['cornerDenseOriginalFaces'])
    assert np.array_equal(boot_dense['originalCornerUV'][ids], boot['cornerDenseOriginalUV'])
    reconstructed = np.sum(boot['cornerDenseOriginalUV']*boot['cornerDenseBarycentrics'][:, :, :, None], axis=2)
    error = float(np.max(abs(reconstructed-boot['actualCornerUV'])))
    charts = boot_charts[ids]
    boot_check = {'executedMappingMeasured': True, 'side': 'R', 'corners': int(ids.size),
        'mixedOriginalUVChartTriangles': int(np.any(charts != charts[:, :1], axis=1).sum()),
        'originalCornerLineageUVMaximumReconstructionError': error, 'barycentricLineageAdmissible': bool(error < 1e-7),
        'storedBarycentricMinimum': float(boot['cornerDenseBarycentrics'].min()),
        'storedBarycentricMaximum': float(boot['cornerDenseBarycentrics'].max()),
        'storedBarycentricMaximumSumError': float(np.max(abs(boot['cornerDenseBarycentrics'].sum(2)-1))),
        'denseAtlas': boot_atlas,
        'pins': {str(p): sha(p) for p in (boot_lineage, boot_dense_path)},
        'geometryScope': 'Executed inherited boot02 corner mapping captured before rejected boot04 shape fit; no rejected geometry bake/acceptance.'}
hoodie_root = ROOT/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1'
hoodie_recipe = hoodie_root/'convert_selected_hoodie.py'
hoodie_native = hoodie_root/'selected-hoodie25/crease-normal-candidate.blend'
hoodie_evidence = ROOT/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie25/FINDING.md'
hoodie_uv_evidence = ROOT/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie24/CONSTRUCTION.md'
assert sha(hoodie_native) == 'c732d98076f6b9b1a209a45e8a0cddf793484807ea8b3ae9011fa4f82c151df0'
result = {'accepted': False, 'kind': 'Light source atlas/bake-authority preflight',
          'recipeSHA256': sha(__file__), 'glove': {'denseAtlas': atlas, 'compactSourceRisk': counts,
            'scope': 'Original compact point ancestry; not an executed final glove appearance bake',
            'sources': {str(p): sha(p) for p in (dense_path, proto_path, cavity_path)}},
          'bootExecutedUV': boot_check,
          'hoodie': {'existingAuthority': 'Native25 inherits preserved source24/source10 UV/materials; historical convert_selected_hoodie.py deliberately unwraps compact mesh and emits dense selected-source colour/roughness/metallic maps at2048.',
            'nativeAndEvidencePins': {str(p): sha(p) for p in (hoodie_native, hoodie_recipe, hoodie_evidence, hoodie_uv_evidence)},
            'limits': 'Code/evidence lineage only; no fresh native image/UV readback, global source-ray support proof or moving appearance acceptance.'},
          'limits': ['Glove exterior geometry can be useful while inherited compact point UV is unsuitable; coherent unwrap/dense bake is still needed.',
                     'No native/browser bake or model/source mutation.']}
output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))
