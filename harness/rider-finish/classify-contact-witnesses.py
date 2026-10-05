"""Annotate proper-contact witnesses with pinned rest geometry and source ancestry.

Only witnessed pairs are classified; no whole-contact anatomy claim is inferred
from the capped witness list. Boxer source IDs are explicitly rejected.
"""
import argparse, gzip, hashlib, json
from pathlib import Path
import numpy as np
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('native_dir'); p.add_argument('contacts'); p.add_argument('fields'); p.add_argument('source_fields'); p.add_argument('source_contacts'); p.add_argument('out')
a = p.parse_args(); out = Path(a.out); assert not out.exists()
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
r = json.loads((Path(a.native_dir)/'report.json').read_text()); rest_path = Path(a.native_dir)/r['rest']['path']; assert sha(rest_path) == r['rest']['sha256']
rest = json.loads(gzip.decompress(rest_path.read_bytes())); contacts = json.loads(Path(a.contacts).read_text()); assert contacts['nativeReportSHA256'] == sha(Path(a.native_dir)/'report.json')
fields = np.load(a.fields); source = np.load(a.source_fields); protected = set(map(int, source['headProtectedIDs'])); records = []
cached_xyz = {region: np.asarray(part['xyz']) for region, part in rest['parts'].items()}
cached_weights = {region: np.asarray(part['fourWeights']) for region, part in rest['parts'].items()}
for record in contacts['records']:
    if record['index'] not in [0,157,419,443]: continue
    annotated = {'index':record['index'], 'case':record['case'], 'fields':{}}
    for kind, pairs in record['fields'].items():
        annotated['fields'][kind] = {}
        for pair, check in pairs.items():
            if not check['properCrossings']: continue
            regions = pair.split('/'); witnesses = []
            for witness in check['properWitnesses']:
                sides = []
                for region, suffix in zip(regions, ['A','B']):
                    ids = witness['nativeVertexIDs'+suffix]; part = rest['parts'][region]
                    xyz = cached_xyz[region][ids]; weights = cached_weights[region][ids]
                    dominant = [rest['jointOrder'][i] for i in np.argmax(weights, axis=1)]
                    side = {'region':region, 'nativeDerivativeVertexIDs':ids, 'triangle':witness['triangle'+suffix], 'restLocalXYZ':xyz.tolist(), 'witnessWorldXYZ':witness['xyzWorld'+suffix], 'dominantFourJointNames':dominant}
                    if region in ['head','body']:
                        ancestry = fields[region+'AttributeEdgeSources'][ids]; side['sourceVertexEdgeAncestry'] = ancestry.tolist(); side['sourcePolygonID'] = int(fields[region+'TriangleSourcePolygonIDs'][witness['triangle'+suffix]])
                        side['sourceIdentity'] = [int(x[0]) if x[0] == x[1] and x[0] >= 0 else -1 for x in ancestry]
                        if region == 'head':
                            side['protectedSourceEndpointIDs'] = [[int(x) for x in edge[:2] if int(x) in protected] for edge in ancestry]
                            side['hasProtectedSourceEndpoint'] = any(side['protectedSourceEndpointIDs'])
                            side['newCapTriangle'] = side['sourcePolygonID'] < 0
                    else:
                        side['sourceIdentity'] = 'UNMEASURED: boxer _SOURCE_ID incorrectly derivative row IDs; cheek has no ancestry attributes'
                    sides.append(side)
                witnesses.append({'sides':sides})
            annotated['fields'][kind][pair] = {'properCrossings':check['properCrossings'], 'classifiedWitnesses':witnesses, 'witnessLimit':16}
    records.append(annotated)
original = json.loads(Path(a.source_contacts).read_text())
box = np.asarray(rest['parts']['boxer']['fourWeights']); names = rest['jointOrder']; hand = [i for i,n in enumerate(names) if any(x in n for x in ['hand.','index_','middle_','pinky_','ring_','thumb_'])]
result = {'status':'UNACCEPTED_REST_ANCESTRY_AND_SEMANTIC_WITNESS_CLASSIFICATION', 'inputPins':{str(Path(x)):sha(x) for x in [a.contacts,a.fields,a.source_fields,a.source_contacts,str(rest_path)]}, 'recipeSHA256':sha(__file__), 'originalSourceRest':{k:{'properCrossings':v['properCrossings'],'finiteContacts':v['finiteContacts']} for k,v in original['records'].items()}, 'boxerHandFieldVertices':int(np.sum(box[:,hand].sum(1)>0)), 'boxerTotalVertices':len(box), 'boxerLocalBounds':[np.asarray(rest['parts']['boxer']['xyz']).min(0).tolist(),np.asarray(rest['parts']['boxer']['xyz']).max(0).tolist()], 'records':records, 'limits':['Classification applies to capped proper witnesses only; no whole-contact anatomy histogram.', 'No signed volume or capsule depth certificate; native semantic skin fields are witnesses, not collision controls.', 'Body/head and head-self remaining proper crossings are failures even if neighboring aliases legitimately touch.', 'Boxer source provenance is unresolved and cannot be inferred from row order; hand/finger membership is measured on the exact derivative fields.']}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'boxerHandFieldVertices':result['boxerHandFieldVertices'],'boxerTotalVertices':len(box),'originalSourceRest':result['originalSourceRest']}))
