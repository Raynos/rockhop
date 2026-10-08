"""Standalone lightweight AST/input-pin checker; no Blender/NumPy/model import."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block:=handle.read(1024*1024):digest.update(block)
    return digest.hexdigest()


def pins(value):
    if isinstance(value,dict):
        if 'path' in value and 'sha256' in value:yield value
        else:
            for child in value.values():yield from pins(child)
    elif isinstance(value,list):
        for child in value:yield from pins(child)


controls=HERE/'pair-inputs.json';c=json.loads(controls.read_text());rows=list(pins(c))
for row in rows:assert sha(ROOT/row['path'])==row['sha256'], ('Changed input',row['path'])
source=HERE/'pair_selected_sculpt.py';tree=ast.parse(source.read_text(),filename=str(source))
calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
assert not any(token in call.lower() for call in calls for token in ('render','bake','cavity_last','boolean','outer_last','shrinkwrap'))
assert c['accepted'] is False and c['pairedRSource']=='Boot04SelectedSurfaceSculpt.R'
assert c['retainedNative']['sha256']=='c6d121b3ffb0b64c330f12d161f30567d6da6c4de0457517097a0b2c99fcb4d9'
assert c['sculptHelpers']['sha256']=='93215774cf4b6c0fa62cf40b06b99759bf5640f1928c291913a08a1d81060936'
r=dict(accepted=False,status='SELECTED_WHOLE_PAIR_SCULPT_AND_BINDING_SOURCE_READY_UNEXECUTED',
    pythonASTPassed=True,explicitInputPinsPassed=len(rows),recipeSHA256=sha(source),controlsSHA256=sha(controls),
    noBlenderModelBakeRenderJobExecutedByWorker=True,
    command=['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','2','--python-exit-code','1','--python',
             str(source.relative_to(ROOT)),'--','harness/out/rider-rebuild/boot-last-anatomical04/pair01'],
    lease='Parent original serial CPU2/model/memory guard,180second cap. No runtime prediction.',
    sourceR='Actual sculpt02 selected R exterior before cavity cutting; no additional geometry change.',
    sourceL='Actual own-side selected L source through the same conditioned guide/14anatomical-handle/SurfaceDeform construction; correct opposite medial sign.',
    runtimeGates=['L actual selected source state/UV/maps matches extraction.',
        'Conditioned selected-source guide and actual finite moving solve saved before later gates; native modifier logs checked.',
        'Selected original exterior faces, UV and useful tread retained by the proven L sculpture.',
        'R/L actual selected surfaces share unchanged native75; own-side foot/toe/shin groups normalized,<=3influences.',
        'Binding leaves selected geometry/UV unchanged; actual one-component watertight surface topology.',
        'Full canonical body positions/faces/weights/UV/rest/pose remain hash-identical.',
        'Actual pair saves before review; failure receipts/current native persist. No cavity/parity/mm-clearance preview blocker.'],
    review=c['previewBodyPolicy'],pendingGates=c['pendingGates'],
    matchedActualViews='Original-selected-pair and sculpted-selected-pair: front/rear/left/right/toe-threequarter/top, genuine4K PBR. R/L individual anatomically labeled views also generated.',
    stoppedProposal='Unexecuted millimetre/CSG local-repair proposal removed after parent production mask correction. No such job ran.',
    limitations=['Source-only unaccepted; parent applies covered-body mask then judges actual opaque selected surfaces.',
        'Body masking does not by itself prove anatomy, garment closure or played bike fit.',c['pendingGates']])
output=ROOT/'docs/evidence/rider-rebuild/boot-last-anatomical04/pair-source-checkpoint.json'
output.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(dict(status=r['status'],pins=len(rows),recipeSHA256=r['recipeSHA256'],controlsSHA256=r['controlsSHA256'])))
