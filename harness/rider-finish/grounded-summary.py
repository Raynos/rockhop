"""Compact, reproducible readback of the every-frame grounded pilot."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--input', required=True)
p.add_argument('--out', required=True)
a = p.parse_args()
source, out = Path(a.input), Path(a.out)
assert not out.exists()
r = json.loads(source.read_text())
summary = {k: r[k] for k in ['status', 'source', 'sourceSHA256', 'driverSHA256',
                           'readerSHA256', 'blender', 'hz', 'locomotionParameters',
                           'originalRestBindsUnchanged', 'limits']}
summary['inputPin'] = {'path': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                       'bytes': source.stat().st_size}
summary['summaryRecipeSHA256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
summary['sourceSHAStillExact'] = hashlib.sha256(Path(r['source']).read_bytes()).hexdigest() == r['sourceSHA256']
summary['soleProbeCount'] = {s: len(ids) for s, ids in r['soleProbeNativeVertexIDs'].items()}
summary['totalSamples'] = len(r['records'])
summary['clips'] = {}
for clip, clock in r['clips'].items():
    rows = [x for x in r['records'] if x['clip'] == clip]
    forward = [x for x in rows if x['direction'] == 'forward']
    limbs = [v for x in rows for v in x['limbResiduals'].values()]
    soles = [v for x in rows for v in x['soles'].values()]
    supported = [v for v in soles if v['declaredSupported']]
    steps = [v['maximumHorizontalStepDuringSupportM'] for v in supported
             if v['maximumHorizontalStepDuringSupportM'] is not None]
    summary['clips'][clip] = {**clock, 'forwardSamples': len(forward),
        'forwardReverseSamples': len(rows),
        'forwardSupportPhases': dict(Counter(x['supportPhase'] for x in forward)),
        'maximumLimbEndResidualM': max(v['endResidualM'] for v in limbs),
        'clampedLimbTargets': sum(v['targetClampedM'] > 0 for v in limbs),
        'maximumTargetClampM': max(v['targetClampedM'] for v in limbs),
        'supportedSoleObservations': len(supported),
        'minimumSupportedSoleZWorldM': min(v['minimumZWorldM'] for v in supported),
        'maximumSupportedSoleZWorldM': max(v['maximumZWorldM'] for v in supported),
        'minimumSupportedProbeCountWithin5mm': min(v['within5mmFloorPoints'] for v in supported),
        'supportedObservationsWithPenetrationBeyond1mm': sum(v['belowFloorBeyond1mmPoints'] > 0 for v in supported),
        'allObservationsWithPenetrationBeyond1mm': sum(v['belowFloorBeyond1mmPoints'] > 0 for v in soles),
        'maximumHorizontalStepDuringSupportM': max(steps, default=0),
        'rootOffsetAtFirstForwardM': forward[0]['rootOffsetNativeM'],
        'rootOffsetAtLastForwardM': forward[-1]['rootOffsetNativeM']}
summary['geometryQualification'] = 'Body04d control has known failed head/body/self contacts and unstable evaluated body tessellation. Motion metrics confer no geometry acceptance.'
out.write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
print(json.dumps(summary['clips'], indent=2))
