"""One coherent component construction and measurements, under original guard."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[4];recipe=Path(__file__).resolve().parent
component=sys.argv[1];assert component in ('boot-R','glove-L','glove-R')
base=root/'harness/out/rider-rebuild/mobile-mesh02'/component
assert not base.exists(),'Fresh component output required'
blender=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--threads','2','--python-exit-code','1','--python']
subprocess.run([sys.executable,str(recipe/'worker.py'),'prepare',component,'prepare01'],check=True)
subprocess.run([sys.executable,str(recipe/'worker.py'),'bake',component,'bake01'],check=True)
subprocess.run([*blender,str(recipe/'audit-first-ray.py'),'--','audit',str(base/'prepare01'),str(base/'audit01'),str(base/'bake01')],check=True)
subprocess.run(['/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13',str(recipe/'motion.py'),str(base/'intake01'),str(base/'bake01'),str(base/'motion01')],check=True)
