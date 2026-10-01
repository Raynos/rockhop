"""Original views/target composition for failed source-mask witness only."""
from pathlib import Path
p=Path(__file__).with_name('compose_evidence.py');code=p.read_text().replace('/trial01','/trial03').replace('Actual C trial01','FAILED C mask witness ONLY').replace('actual GLB','FAILED source mask GLB');exec(compile(code,str(p),'exec'))
