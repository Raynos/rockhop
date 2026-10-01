"""Actual reimport views of frozen failed mask; not a reconstructed garment."""
from pathlib import Path
p=Path(__file__).with_name('render_trial01.py')
code=p.read_text().replace('/trial01','/trial03').replace("R/'character.glb'","R/'failed-mask-witness.glb'").replace('UNACCEPTED C garment-pattern actual GLB evidence','FAILED C modular source-mask witness actual GLB; no authored cloth constructed').replace('2026,10,1,2,17','2026,10,1,2,26')
exec(compile(code,str(p),'exec'))
