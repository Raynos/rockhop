"""Keep immutable raw topology reports private; track compact receipts instead."""
from pathlib import Path
import hashlib,json
R=Path('/Users/raynos/projects/games/rockhop')
E=R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/drafted-raglan'
M=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/drafted-raglan')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=M/'builder-manifest178.json'
if not frozen.exists():frozen.write_bytes((E/'manifest.json').read_bytes())
manifest=json.loads(frozen.read_text())
for name,key in [('inventory.json','vertexIDs'),('assembly.json','sourcePrimitive0RetainedTriangleIDs')]:
    source=E/name;raw=M/('raw-'+name)
    if not raw.exists():raw.write_bytes(source.read_bytes())
    recorded=manifest['files'][str(source)]
    assert sha(raw)==recorded['sha256'] and raw.stat().st_size==recorded['bytes']
    d=json.loads(raw.read_text())
    if name=='inventory.json':
        for ob in d['objects']:
            for component in ob['components']:component.pop(key)
            components=ob.pop('components')
            ob['componentCount']=len(components)
            ob['sixteenLargestComponents']=sorted(components,key=lambda c:c['vertices'],reverse=True)[:16]
            ob['componentLimits']='Raw component membership retained in private report; UV-split components are not physical garment segmentation.'
    else:d.pop(key)
    d['immutableRawReport']={'path':str(raw),**recorded}
    d['integrationCompaction']='Only raw vertex/triangle ID lists moved to private master; source geometry and measured results unchanged. Reproduce builder recipes then run compact_shell178.py.'
    source.write_text(json.dumps(d,indent=2)+'\n')
    manifest['files'][str(raw)]=recorded
    manifest['files'][str(source)]={'bytes':source.stat().st_size,'sha256':sha(source)}
manifest['originalBuilderManifest']={'path':str(frozen),'sha256':sha(frozen),'bytes':frozen.stat().st_size}
manifest['integrationCompaction']='Original builder manifest/raw reports immutable in private masters; recipes and mesh hashes unchanged.'
(E/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'retainedRawReports':2,'rawManifestSHA256':sha(frozen),'trackedReportsBytes':sum((E/n).stat().st_size for n in ['inventory.json','assembly.json'])}))
