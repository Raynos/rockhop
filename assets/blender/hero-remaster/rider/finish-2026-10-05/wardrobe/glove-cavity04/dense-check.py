"""Read-only axial witnesses on untouched dense donor derivative."""
import argparse
import importlib.util
import json
from pathlib import Path
import numpy as np


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--semantics',required=True);parser.add_argument('--evidence',required=True);args=parser.parse_args()
    recipe=Path(__file__).with_name('probe.py');spec=importlib.util.spec_from_file_location('cuff_probe',recipe);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    data=np.load(args.source);center=np.array(json.loads(Path(args.semantics).read_text())['gloves']['coarsePalmRegistration']['R']['sourceWristCentre']);rays=[]
    for dx,dz in [(0,0),(-.06,0),(.06,0),(0,-.06),(0,.06)]:
        x,z=float(center[0]+dx),float(center[2]+dz);rays.append({'sourceX':x,'sourceZ':z,'hits':module.axial_hits(data['vertices'],data['faces'],x,z)})
    report={'accepted':False,'status':'READ_ONLY_DENSE_DONOR_AXIAL_CUFF_WITNESSES','recipeSHA256':module.sha(__file__),'helperSHA256':module.sha(recipe),'source':{'path':args.source,'sha256':module.sha(args.source),'vertices':len(data['vertices']),'triangles':len(data['faces'])},'axialRays':rays,'limits':'Five source-space rays only; confirms dense donor surface hits along those lines, not global cavity or canonical forearm/hand occupancy. Source and original corner UV/PBR untouched.'}
    Path(args.evidence).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'firstHits':[(r['hits'][0]['sourceY'],r['hits'][0]['normalDotAxis'])for r in rays]}))


if __name__=='__main__':main()
