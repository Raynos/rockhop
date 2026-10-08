"""Lightweight source/ancestry verification only; never imports Blender or arrays."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block:=handle.read(1024*1024):
            digest.update(block)
    return digest.hexdigest()


def pins(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:
            yield value
        else:
            for child in value.values():
                yield from pins(child)
    elif isinstance(value,list):
        for child in value:
            yield from pins(child)


controls=HERE/'sculpt-inputs.json'
c=json.loads(controls.read_text())
rows=list(pins(c))
for row in rows:
    assert sha(ROOT/row['path'])==row['sha256'], ('Changed input',row['path'])
source=HERE/'sculpt_selected.py'
tree=ast.parse(source.read_text(),filename=str(source))
calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
assert not any(token in call.lower() for call in calls for token in ('render','bake','remesh','shrinkwrap','outer_last'))
assert c['accepted'] is False and c['limits']['noFallback'] and c['limits']['noFullBootRemesh']
assert c['maxGuideVertices']==16000 and c['guideRatio']==.04
assert c['objects']['boots']=={s:'Boots__LocallyRepairedSelectedDenseBoot.'+s for s in ('R','L')}
assert c['innerEaseM']==.004 and c['minimumMeasuredClearanceM']==.0025
assert c['legacyHelpers']['sha256']=='1b307138bbb4314d5e2485f8b60512b5f799bac8eeb4b39eb7364979dbd79689'
assert len(c['handles'])==14 and len({r['name'] for r in c['handles']})==14
report=dict(accepted=False,status='ONE_SELECTED_SURFACE_SCULPT_SOURCE_READY_UNEXECUTED',
    pythonASTPassed=True,explicitInputPinsPassed=len(rows),
    recipeSHA256=sha(source),controlsSHA256=sha(controls),
    noBlenderModelBakeRenderOrDenseArrayJobExecuted=True,
    command=['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','2','--python-exit-code','1',
             '--python',str(source.relative_to(ROOT)),'--','harness/out/rider-rebuild/boot-last-anatomical04/sculpt02'],
    leaseRequirement='Parent original serial CPU2/model/memory guard,180second cap. Source never launches itself.',
    supportedBounds=c['limits'],
    runtimeGates=[
      'Exact actual selected source geometry/UV/PBR state from extraction.',
      'Guide only decimation<=16000 vertices; manifold triangulated source-derived guide.',
      'Guide uses documented original-source affine units, dense selected remains world frame.',
      'No unanchored guide vertex without active cotangent incident triangle.',
      'Finite genuine free-surface movement above float-roundoff scale; anchor residuals report-only.',
      'Freeze actual evaluated moving guide before warning/topology/transfer gates.',
      'Capture C stdout/stderr for modifier bind/evaluation/apply and reject actual warning/error lines.',
      'Dense original sole excluded from deform and byte-exact; exterior faces/original corner UV retained before cavity.',
      'Actual dense transfer saved before sole/UV checks; verified sculpt saved before own-side4mm cavity and UV gates.',
      'Cavity creates continuous derivative topology with one component and no boundary/nonmanifold/zero-area faces.',
      'Foot vertices/triangle-centroid outside-leather parity and>=2.5mm measured nearest clearance.',
      'Surviving selected sculpt corners exact original UV; split faces retain original charts.',
      'New cavity corners explicitly reference actual same-side original inner-quarter source triangles.',
      'Real original protected tread triangles unchanged, whole original wearer/rest75/pose/weights/UV hash unchanged.',
      'Exception receipts persist all completed/partial measurements and fresh native hashes; partial in-memory save separate from last checkpoint.'],
    reviewContract='Matched source/sculpt/cavity original-PBR specs for R/L actual medial, lateral, toe, heel and top. Parent alone judges; cavity emptiness does not prove enclosure or appearance. Full-outfit and played ankle/toe/bike gates remain open.',
    primaryMethods=[
      'https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/laplacian_deform.html',
      'https://docs.blender.org/api/current/bpy.types.LaplacianDeformModifier.html',
      'https://docs.blender.org/api/current/bpy.types.SurfaceDeformModifier.html',
      'https://docs.blender.org/api/current/bpy.ops.object.html#bpy.ops.object.laplaciandeform_bind',
      'https://docs.blender.org/api/current/bpy.ops.object.html#bpy.ops.object.surfacedeform_bind'],
    limitations=['180second cap is a stop limit, no benchmark or runtime claim.',
      'Unexecuted artist handle strengths require actual geometry/PBR review.',
      'Guide is a hidden derivative authoring tool; it never replaces the dense selected exterior.',
      'Inner-quarter chart transfer is honest original PBR ancestry, not a new coherent baked lining.',
      c['motionRequired']])
output=ROOT/'docs/evidence/rider-rebuild/boot-last-anatomical04/sculpt02-source-checkpoint.json'
output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],pins=len(rows),recipeSHA256=report['recipeSHA256'],controlsSHA256=report['controlsSHA256'])))
