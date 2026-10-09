"""Pin real qualified results; this does not create placeholder receipts."""
import json
import sys
from pathlib import Path
import lineage as h

assert len(sys.argv) == 8, ('freeze-integration.py TARGET_RECEIPT TARGET_INPUT TARGET_RECIPE '
                           'SLEEVE_RECEIPT SLEEVE_INPUT DENSE_SUMMARY FRESH_INPUT')
target_receipt, target_input, target_recipe, sleeve_receipt, sleeve_input, dense, output = [
    Path(arg).resolve() for arg in sys.argv[1:]]
assert output.is_relative_to(h.HERE) and not output.exists()
target = json.loads(target_receipt.read_text()); sleeve = json.loads(sleeve_receipt.read_text())
paths = {'targetReceipt': target_receipt, 'targetNative': h.ROOT/target['native']['path'],
         'targetInput': target_input, 'targetRecipe': target_recipe, 'sleeveReceipt': sleeve_receipt,
         'sleeveNative': h.ROOT/sleeve['native']['path'], 'sleeveInput': sleeve_input,
         'sleeveRecipe': h.HERE/'sleeve38.py', 'denseSummary': dense,
         'integrationRecipe': h.HERE/'integrate.py', 'lineageHelper': h.HERE/'lineage.py',
         'checkpointHelper': h.HERE/'sleeve_checkpoint.py'}
config = {'acceptedArt': False, 'pins': {name: h.pin(path) for name, path in paths.items()}}
# Run pure result gates before writing. read_input is repeated by the Blender
# worker and independently checks every actual input byte pin before mutation.
h.target_gate(target, config['pins'])
sleeve_config = json.loads(sleeve_input.read_text())
glove = json.loads(h.checked(sleeve_config['pins']['gloveReceipt']).read_text())
summary = json.loads(dense.read_text())
relations = {name: json.loads(h.checked(row).read_text()) for name, row in summary['relations'].items()}
h.sleeve_gate(sleeve, glove, summary, relations, sleeve_config, config['pins'])
output.write_text(json.dumps(config, indent=2)+'\n')
try: h.read_input(output)
except BaseException:
    output.unlink()
    raise
print(json.dumps({'acceptedArt': False, 'status': 'INPUTS_FROZEN_NATIVE_INTEGRATION_NOT_RUN', 'input': h.pin(output)}))
