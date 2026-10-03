"""Regenerate pre-cancellation construction in memory, without source/file writes."""
from pathlib import Path
import json,numpy as np
HERE=Path(__file__).resolve().parent
s=(HERE/'build_rest_tube02.py').read_text();s=s[:s.index('# Original source normal rows')]
s=s.replace('cancel.extend(records)', '''cancel.extend(records)
 cancellationWitness.append({'physicalWeldSet':list(key),'faces':[{'primitive':int(pi),'preCancelFaceIndex':int(fi),'faceKind':kind[pi][fi],'sourceFaceAncestry':int(faceParents[pi][fi]),'vertexIDs':[int(v)for v in tr[pi][fi]],'physicalWeldOrder':[int(weld[pi][v])for v in tr[pi][fi]],'restPositions':[p[pi][v]for v in tr[pi][fi]]}for pi,fi in records]})''').replace('cancel=[]','cancel=[];cancellationWitness=[]')
ns={'__file__':str(HERE/'build_rest_tube02.py'),'__name__':'_memory_witness'};exec(compile(s,'<memory-only pre-cancellation regeneration>','exec'),ns);r={'frozenGeometrySHA256':'3126e186d4fdfdddcc2db0bc1c1c0009d14c46cc2225dcfd75c9fbfc9ca1ff2c','method':'Regenerate exact build recipe in memory up to face cancellation; no candidate rewrite. Each stored pair has identical authoritative physical weld set, opposite directed winding and source/cap full coordinates. Both faces canceled; source vertex prefixes untouched.','pairs':ns['cancellationWitness']};(HERE/'opposite-face-cancellation-witness.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
