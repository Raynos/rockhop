"""Compose one selected candidate and measure actual encoded native weights."""
import subprocess,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[4];recipe=Path(__file__).resolve().parent
out=Path(sys.argv[1]);assert not out.exists(),'Fresh output required';out.mkdir(parents=True)
source=root/'harness/out/rider-rebuild/download-opt01/textures01/composition01/rider.glb';parts=root/'harness/out/rider-rebuild/mobile-mesh02'
subprocess.run(['node',str(recipe/'graft.mjs'),str(source),str(parts),str(out/'rider.glb'),str(out/'graft.json')],check=True)
subprocess.run(['node',str(recipe/'extract-packed.mjs'),str(out/'rider.glb'),str(out/'graft.json'),str(parts),str(out/'packed')],check=True)
python='/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13'
measure=[]
for part in ('boot-L','boot-R','glove-L','glove-R'):
 atlas=parts/part/('skin03' if part.startswith('glove') else '')/'bake01'
 target=out/('motion-'+part)
 subprocess.run([python,str(recipe/'motion-packed.py'),str(parts/part/'intake01'),str(atlas),str(target),str(out/'packed'/(part+'-weights.u16'))],check=True)
 measure.append({'part':part,'result':json.loads((target/'motion.json').read_text())})
(out/'qualification.json').write_text(json.dumps({'accepted':False,'method':'Four distinct original selected components, skin03 native-knot gloves, direct packed Uint16 field readback under original482played poses. Parent actual moving/phone and corrected grip gates remain open.','parts':measure},indent=2)+'\n')
