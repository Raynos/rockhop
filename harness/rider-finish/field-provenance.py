"""Compare independently sampled actual native FULL body fields outside a declared seam."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
p = argparse.ArgumentParser(description=__doc__)
for key in ['control', 'candidate', 'fields', 'out']:
    p.add_argument('--'+key, required=True)
p.add_argument('--original-rows', type=int, required=True)
p.add_argument('--expected-seam-rows', type=int, required=True)
a = p.parse_args()
control, candidate, fields_path, out = [Path(getattr(a,key)).resolve() for key in ['control','candidate','fields','out']]
assert not out.exists()
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(directory):
    report = json.loads((directory/'report.json').read_text())
    path = directory/report['rest']['path']
    assert sha(path) == report['rest']['sha256']
    return report, json.loads(gzip.decompress(path.read_bytes()))
ar, old = load(control)
br, new = load(candidate)
fields = np.load(fields_path)
n = a.original_rows
seam = fields['bodySeamPhysicalIDs'][:n] >= 0
assert int(seam.sum()) == a.expected_seam_rows
assert np.array_equal(fields['bodyAttributeEdgeSources'][:n,:2], np.repeat(np.arange(n)[:,None],2,axis=1))
o = np.array(old['parts']['body']['fullRawWeights'])
f = np.array(new['parts']['body']['fullRawWeights'])
four = np.array(new['parts']['body']['fourRawWeights'])
delta = np.abs(f[:n][~seam]-o[:n][~seam])
xyz_old = np.array(old['parts']['body']['xyz'])
xyz_new = np.array(new['parts']['body']['xyz'])
result = {'status':'UNACCEPTED_READBACK_FULL_CONTROL_PROVENANCE', 'recipeSHA256':sha(__file__),
    'controlNativeReportSHA256':sha(control/'report.json'), 'candidateNativeReportSHA256':sha(candidate/'report.json'),
    'controlRestSHA256':sha(control/ar['rest']['path']), 'candidateRestSHA256':sha(candidate/br['rest']['path']),
    'constructionFieldsSHA256':sha(fields_path), 'sourcePins':{'control':ar['sourcePins'],'candidate':br['sourcePins']},
    'jointOrdersExact':old['jointOrder']==new['jointOrder'], 'originalBodyRows':n,
    'excludedAuthoredOriginalSeamRows':int(seam.sum()), 'bodyOriginalIdentityAncestryExact':True,
    'outsideSeamActualFullRawWeightsExact':bool(np.array_equal(f[:n][~seam],o[:n][~seam])),
    'outsideSeamActualFullRawMaximumDelta':float(delta.max()),
    'outsideSeamRestXYZExact':bool(np.array_equal(xyz_old[:n][~seam],xyz_new[:n][~seam])),
    'bodyActualFullFourDifferentRows':int(np.any(f!=four,axis=1).sum()),
    'bodyFullRawSumRange':new['parts']['body']['fullRawSumRange'],
    'bodyFourRawSumRange':new['parts']['body']['fourRawSumRange'],
    'newHeadActualFullFourRawWeightsExact':bool(np.array_equal(new['parts']['head']['fullRawWeights'],new['parts']['head']['fourRawWeights'])),
    'limits':['Independent actual native group readbacks compared; conditioned F0 canonical weights never substitute for FULL control.',
              'Explicit original source identity rows outside the admitted seam only; new derivative rows remain separate. No geometry/contact/coverage/art acceptance.']}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2)+'\n')
print('NATIVE_FULL_CONTROL_OUTSIDE_SEAM',result['outsideSeamActualFullRawWeightsExact'],result['outsideSeamActualFullRawMaximumDelta'])
