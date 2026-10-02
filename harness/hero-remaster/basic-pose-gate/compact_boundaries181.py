"""Store full immutable boundary IDs privately and compact tracked summaries."""
from pathlib import Path
import hashlib,json
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/source-boundaries181'
M=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/source-boundaries181');raw=M/'raw-report181.json'
if not raw.exists():raw.write_bytes((E/'report.json').read_bytes())
d=json.loads(raw.read_text())
for item in d['interfaces']:
    for group in ['pairedBoundaryComponents','allSharedEdgeComponents']:
        for component in item[group]:
            component.pop('orderedCyclePhysicalIDs',None);component.pop('physicalIDs',None)
for component in d['allHoodPhysicalOpenBoundaryComponents']:
    component.pop('orderedCyclePhysicalIDs',None);component.pop('physicalIDs',None)
proposal=d['hemExistingQA']['existingIntrinsicGeometryProposal']
d['hemExistingQA']['existingIntrinsicGeometryProposal']={k:v for k,v in proposal.items()if k in ['status','sourceSHA256','source_sha256','limits','verdict','conclusion']}
hem=d['hemExistingQA']['rawReport']
if 'witnesses'in hem:
    witnesses=hem.pop('witnesses');hem['originalWitnessCount']=len(witnesses);hem['firstThreeWitnesses']=witnesses[:3]
d['immutableFullReport']={'path':str(raw),'SHA256':hashlib.sha256(raw.read_bytes()).hexdigest(),'bytes':raw.stat().st_size,'reproduction':'Run source audit.py then compact_boundaries181.py; raw ordered IDs/complete original proposal remain immutable private evidence.'}
(E/'report.json').write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({'trackedBytes':(E/'report.json').stat().st_size,'immutableRawBytes':raw.stat().st_size}))
