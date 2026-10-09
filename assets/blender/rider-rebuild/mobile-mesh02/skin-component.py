"""One skin-preserving selected component and independent interior measurements."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[4];recipe=Path(__file__).resolve().parent
component=sys.argv[1];namespace=sys.argv[2] if len(sys.argv)>2 else 'skin02';assert namespace in ('skin02','skin03');assert component in ('glove-L','glove-R')
base=root/'harness/out/rider-rebuild/mobile-mesh02'/component;stage=base/namespace;intake=base/'intake01';reduced=stage/('simplify03' if namespace=='skin03' else 'simplify02')
if not intake.exists():subprocess.run(['node',str(recipe/'extract.mjs'),str(root/'harness/out/rider-rebuild/selected-ankle-field42/runtime02/rider.glb'),str(intake),str(('glove-L','glove-R').index(component)+2)],check=True)
calibration=stage/'calibration.json'
if namespace=='skin03' and not calibration.exists():subprocess.run(['node',str(recipe/'calibrate-skin.mjs'),str(intake),str(calibration)],check=True)
if not reduced.exists():subprocess.run(['node',str(recipe/'simplify-skin.mjs'),str(intake),str(reduced),*([str(calibration)] if namespace=='skin03' else [])],check=True)
blender=['/Applications/Blender.app/Contents/MacOS/Blender','-b','--threads','2','--python-exit-code','1','--python']
for mode,inp,out in [('prepare',intake,stage/'prepare01'),('bake',stage/'prepare01',stage/'bake01')]:
 assert not out.exists(),'Fresh stage output required'
 subprocess.run([*blender,str(recipe/'rebuild-skin.py'),'--',mode,str(inp),str(out),str(reduced)],check=True)
subprocess.run([*blender,str(recipe/'audit-first-ray.py'),'--','audit',str(stage/'prepare01'),str(stage/'audit01'),str(stage/'bake01')],check=True)
subprocess.run(['/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13',str(recipe/'motion.py'),str(intake),str(stage/'bake01'),str(stage/'motion01')],check=True)
subprocess.run([*blender,str(recipe/'interior.py'),'--',str(intake),str(stage/'bake01'),str(stage/'interior01')],check=True)
