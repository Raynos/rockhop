"""Strengthen the parent proof: source roots and ribbon exclusion are explicit."""
from pathlib import Path
import json,hashlib
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');E=R/'docs/evidence/hero-remaster/one-rider-v2/source-seam191'
contract=json.loads((B/'source-seam191/next-construction-contract.json').read_text());proof=json.loads((B/'source-seam191/endpoint-fan-contract.json').read_text());source=json.loads((B/'source-seam191/literal-inventory.json').read_text());section=json.loads((B/'source-axilla189/section-fixed-03.json').read_text());scope=set(source['scopeSourceFaces']);ribbon=set(contract['prospectiveBridgeRibbonOriginalFaceIDs']);assert len(ribbon)==69
roots={l['geometricClass']:{i for s in l['segments']for ep in s['endpoints']for i in ep.get('sourcePhysicalEdge',[])}for l in section['loops']}
checked=0
for path in proof['rootedBelowTargetPaths']:
 assert path['physicalIDs'][-1]in roots[path['rootClass']]
 retained=set(contract['retainedGeometricPanelFanFaceIDs'][path['rootClass']]);assert not retained&ribbon
 for edge in path['edges']:
  fs=set(edge['sourceFaces']);assert fs and not fs&ribbon and all(f not in scope or f in retained for f in fs);checked+=1
out=E/'parent-ribbon-proof.json';assert not out.exists()
x={'status':'SOURCE_ROOT_MEMBERSHIP_AND_RETAINED_PATHS_EXCLUDING_ALL_69_RIBBON_FACES_VERIFIED','paths':2,'literalEdges':checked,'ribbonFaces':69,'rootMembership':'Exact saved1.13m central/lateral contour edge endpoints','limits':'Assumes these registered source panel continuations are retained; geometric heuristic does not establish every possible garment cut infeasible. No asset or moving art acceptance.'};out.write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
