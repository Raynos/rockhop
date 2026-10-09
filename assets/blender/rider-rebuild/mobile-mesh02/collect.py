"""Preserve compact component receipts and complete compressed witness records."""
from pathlib import Path
import json,gzip,shutil,sys
component=sys.argv[1];assert component in ('boot-R','glove-L','glove-R')
root=Path(__file__).resolve().parents[4];base=root/'harness/out/rider-rebuild/mobile-mesh02'/component;out=root/'docs/evidence/rider-rebuild/mobile-mesh02'
for kind,stage in [('prepare','prepare01'),('bake','bake01'),('motion','motion01')]:shutil.copy(base/stage/(kind+'.json'),out/(component+'-'+kind+'01.json'))
for stage,label in [('bake01','field'),('audit01','first-ray')]:
 p=base/stage/'field.json';report=json.loads(p.read_text())
 with gzip.open(out/(component+'-'+label+'01-full.json.gz'),'wb') as g:g.write(p.read_bytes())
 report.pop('worstNormalLocations');report.pop('worstAlbedoLocations')
 if 'firstBakeRay' in report:report['firstBakeRay'].pop('worstLocations')
 (out/(component+'-'+label+'01-summary.json')).write_text(json.dumps(report,indent=2)+'\n')
guard=out/(component+'-component01-guard')
for name in ('guard.json','worker.log'):
 p=guard/name
 with gzip.open(str(p)+'.gz','wb') as g:g.write(p.read_bytes())
p=Path('/tmp/rockhop-mobile-mesh02-'+component+'-component01-telemetry.jsonl')
with gzip.open(guard/'admission-telemetry.jsonl.gz','wb') as g:g.write(p.read_bytes())
