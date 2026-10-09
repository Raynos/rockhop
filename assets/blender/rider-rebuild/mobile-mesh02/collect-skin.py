"""Preserve native-knot derivative receipts without dropping full witnesses."""
from pathlib import Path
import json,gzip,shutil,sys
component=sys.argv[1];assert component in ('glove-L','glove-R')
root=Path(__file__).resolve().parents[4];base=root/'harness/out/rider-rebuild/mobile-mesh02'/component/'skin02';out=root/'docs/evidence/rider-rebuild/mobile-mesh02';prefix=component+'-skin02-'
for kind,stage in [('simplify','simplify02'),('prepare','prepare01'),('bake','bake01'),('motion','motion01')]:shutil.copy(base/stage/(kind+'.json'),out/(prefix+kind+'.json'))
for stage,label in [('bake01','field'),('audit01','first-ray')]:
 p=base/stage/'field.json';report=json.loads(p.read_text())
 with gzip.open(out/(prefix+label+'-full.json.gz'),'wb') as g:g.write(p.read_bytes())
 report.pop('worstNormalLocations');report.pop('worstAlbedoLocations')
 if 'firstBakeRay' in report:report['firstBakeRay'].pop('worstLocations')
 (out/(prefix+label+'-summary.json')).write_text(json.dumps(report,indent=2)+'\n')
interior=base/('interior02' if (base/'interior02/interior.json').exists() else 'interior01')/'interior.json';shutil.copy(interior,out/(prefix+'interior.json'))
for stage in ['skin02']+(['interior02'] if component=='glove-L' else []):
 guard=out/(component+'-'+stage+'-guard')
 for name in ('guard.json','worker.log'):
  p=guard/name
  with gzip.open(str(p)+'.gz','wb') as g:g.write(p.read_bytes())
 p=Path('/tmp/rockhop-mobile-mesh02-'+component+'-'+stage+'-telemetry.jsonl')
 with gzip.open(guard/'admission-telemetry.jsonl.gz','wb') as g:g.write(p.read_bytes())
