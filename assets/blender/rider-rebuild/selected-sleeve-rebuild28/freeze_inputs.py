"""Freeze actual parent-produced checkpoints; no Blender or model operation."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def pin(path):
    path = Path(path).resolve(); assert path.is_file() and path.is_relative_to(ROOT)
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1048576): h.update(block)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest()}


def main():
    assert len(sys.argv) == 4, 'freeze_inputs.py GLOVE_RECEIPT FULL_REFERENCE_SAMPLES OUTPUT_JSON'
    glove_path, samples, output = [Path(a).resolve() for a in sys.argv[1:]]
    assert not output.exists() and output.is_relative_to(HERE)
    glove = json.loads(glove_path.read_text())
    assert glove['status'] == 'UNACCEPTED_GLOVES_CONSTRUCTED_SLEEVE_NOT_AUTHORED'
    assert glove['originalHoodieUnchangedBeforeSave'] and glove['exact75RestUnchanged']
    assert pin(ROOT/glove['native']['path']) == glove['native']
    paths = {'gloveReceipt': glove_path, 'gloveNative': ROOT/glove['native']['path'],
             'referenceSamples': samples, 'fieldHelper': HERE/'field.py',
             'priorInputs': ROOT/'assets/blender/rider-rebuild/glove-over-sleeve08/input.json',
             'cuffInput': ROOT/'assets/blender/rider-rebuild/selected-cuff-topology10/input09.json',
             'cuffEngine': ROOT/'assets/blender/rider-rebuild/astra-cuff-bearing18/construct09.py',
             'bridgeHelper': ROOT/'assets/blender/rider-rebuild/selected-sleeve-tailoring27/bridge3d.py'}
    pins = {name: pin(path) for name, path in paths.items()}
    expected = {'priorInputs': '912e724a6d296709c92a4c48704f5be490e7f228cdfe55b84814e76c85224eed',
                'cuffInput': '076ce70b228895af9cd75ea9148abca85c57996938c19691fb6d3bdc9049d0f4',
                'cuffEngine': '141e434136726814a69ff616fbb7de730750cb6680ee99b6879db7d0c6517e06',
                'bridgeHelper': '13f05ed010994687d3333b166a8ee4265c78671d6570a55995e74ff573b7eaf2'}
    for name, value in expected.items(): assert pins[name]['sha256'] == value, name
    prior = json.loads(paths['priorInputs'].read_text()); assert prior['master'] == glove['sourceMaster']
    config = {'acceptedArt': False, 'pins': pins, 'constructionBudgetSeconds': 540,
              'field': {'fieldCellM': .04, 'clothClearanceM': .0025, 'contactSolveMarginM': .0001,
                        'contactReserveM': .003, 'contactPasses': 8, 'projectionIterations': 256,
                        'numericalContactToleranceM': .00002, 'maximumDerivativeBound': .85,
                        'maximumDisplacementM': .045},
              'limits': ['One bounded construction candidate; no field-cell/ease/radius/station sweep.',
                         '540-second internal construction deadline requests a parent600-second CPU2 guard.',
                         'Actual first runtime is unmeasured. Dense qualifiers run separately so failures retain a real unaccepted native checkpoint.',
                         '8 contact linearizations exchange complete dense constraints; they do not change geometric targets.',
                         'Original outward detail, UV/PBR and original named skin fields are retained; generic/bike pose enclosure remains required.']}
    output.write_text(json.dumps(config, indent=2)+'\n'); print(json.dumps(pin(output)))


if __name__ == '__main__': main()
