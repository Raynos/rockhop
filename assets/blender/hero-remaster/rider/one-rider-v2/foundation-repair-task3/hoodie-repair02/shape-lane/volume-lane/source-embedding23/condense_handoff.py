from pathlib import Path
import json,numpy as np,hashlib
p=Path('continuous-shell-handoff.json');r=json.loads(p.read_text());a={}
for row in r['protectedIdentity']['cuffs']:
 s=row['side'];a['cuffAliases'+s]=np.array(row.pop('exactPhysicalAliasIDs'),int);a['cuffPositions'+s]=np.array(row.pop('positionsM'));row['exactAliasCount']=len(a['cuffAliases'+s]);row['mappingFile']='continuous-shell-source-maps.npz'
 for part in row['primitiveRows']:
  i=part['primitive'];a[f'cuffVertices{s}{i}']=np.array(part.pop('sourceVertexIDs'),int);part['rows']=len(a[f'cuffVertices{s}{i}'])
for s,row in r['oldGarmentSeams']['failedTubeBoundaryReference'].items():
 for key in ['oldRingSourceUniqueEdges','oldRingEdgeBarycentric','oldRingPositionsM']:a[key+s]=np.array(row.pop(key))
 row['mapFile']='continuous-shell-source-maps.npz';row['ringNodes']=len(a['oldRingPositionsM'+s])
np.savez_compressed('continuous-shell-source-maps.npz',**a);r['sourceMapsSHA256']=hashlib.sha256(Path('continuous-shell-source-maps.npz').read_bytes()).hexdigest();r['status']='HANDOFF ONLY: original clean_shell_draft178 is the sole shell builder. This lane now owns read-only diagnosis and QA/export contracts.'
r['source']['coordinates']='Meters; Y points up. Transverse anatomy follows Z; estimated anterior direction is +X. Exact pose transforms come from authoritative D. Chart coordinates are not measured anatomy.'
r['source']['identityEvidence']='Root verified all five preferred body11 POSITION/NORMAL/UV values equal C19. This geometry identity does not imply skeleton or weight identity.'
r['gateBeforeBroaderMotion']='One agreed continuous-shell builder. First compare preferred standing front/side/back in PBR and gray, all rest triangles, declared identity and weld contracts. Then test actual authoritative frame 304 with matched D and gloves, literal crossings, collapse, strain and appearance. Broader game combinations, continuous interpolation and support gates follow material improvement. No tube or chart salvage in this lane.'
r['failureAttribution']['worstEdge']['cause']='Adjacent source vertices bind to disconnected cap/tube neighborhoods. Footpoint motions differ 137 mm in X; frame-offset differential is about 2.5 mm. This is an attachment failure; normal or UV changes and boundary-alpha tuning cannot fix it.'
p.write_text(json.dumps(r,indent=2));print('contract SHA',hashlib.sha256(p.read_bytes()).hexdigest(),'bytes',p.stat().st_size,'maps SHA',r['sourceMapsSHA256'])
