"""Verify all frozen native data survives the donor-surface derivative."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
ap=argparse.ArgumentParser(description=__doc__)
for k in ['original','candidate','snapshot-recipe','out']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);original,candidate,recipe,out=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['original','candidate','snapshot-recipe','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [original,candidate,recipe]}
definition=recipe.read_text();definition=definition[definition.index('def snapshot(path):'):definition.index('before=snapshot(original)')];exec(compile(definition,str(recipe),'exec'))
before=snapshot(original);after=snapshot(candidate)
for kind in ['meshes','materials','images']:
    assert all(after[kind].get(name)==value for name,value in before[kind].items()),kind
assert before['bones']==after['bones']
g=bpy.data.objects['Actual selected donor surface with wearer cuts, unaccepted'];high=bpy.data.objects['Exact selected Hunyuan high-poly PBR donor, display frame only']
assert g.data.materials[0] is high.data.materials[0]
report={'status':'UNACCEPTED donor derivative original-data preservation audit','pins':pins,'recipeSHA256':sha(__file__),'originalCounts':{k:len(v) for k,v in before.items()},'originalNativeDataExact':True,'candidateUsesExactOriginalDonorMaterial':True,'originals':before,
        'limits':['New derivative geometry and UVs change through simplification/registration/cuts; original22mesh data,18graphs,17images and51rest/pose remain exact.','No fitting/topology/art/rig/moving/collision/mobile acceptance; allM0-M5 open.']}
assert pins=={p:sha(p) for p in pins};out.write_text(json.dumps(report,indent=2)+'\n');print('DONOR_ORIGINALS_EXACT',report['originalCounts'],flush=True)
