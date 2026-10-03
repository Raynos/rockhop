"""Create native zero-rest default successor; preserve frozen construction04."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
ap=argparse.ArgumentParser(description=__doc__)
for n in ['source','out','evidence']:ap.add_argument('--'+n,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,out,evidence=[Path(getattr(a,n)).resolve() for n in ['source','out','evidence']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();before=sha(source);out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
if (out/'rider.blend').exists():raise RuntimeError('Frozen zero-rest successor exists')
bpy.ops.wm.open_mainfile(filepath=str(source));hoodie=bpy.data.objects['Sewn clean hoodie with dropped hood'];values=[]
for key in hoodie.data.shape_keys.key_blocks:
 if key.name=='Basis':continue
 values.append({'name':key.name,'before':key.value,'after':0});key.value=0
assert len(values)==3 and all(v['before']==1 for v in values)
root=bpy.data.objects['Foundation file frame, game x0.65'];root['rockhopAppearanceCandidate']='unaccepted appearance05 zero-rest defaults'
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(out/'rider.blend'),compress=True)
assert sha(source)==before
report={'status':'UNACCEPTED native05 resets only visible hoodie key default values; original04 immutable','sourceMasterSHA256':before,'candidateMasterSHA256':sha(out/'rider.blend'),'recipeSHA256':sha(__file__),'values':values,
 'limits':['Shape basis/deltas, UV/weights/topology/materials/51bind unchanged; metadata label identifies successor.',
 'Controlled04 film writes all3 coefficients eachframe, so zero-default05 should be motion-equivalent after injection; this is not a new05 capture claim.']}
(evidence/'native-zero-rest.json').write_text(json.dumps(report,indent=2)+'\n');print('NATIVE_ZERO_REST_READY',report['candidateMasterSHA256'],flush=True)
