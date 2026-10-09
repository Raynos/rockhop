"""One owned component stage; execute inside original bounded96 guard."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[4]
recipe=Path(__file__).resolve().parent
mode,component,stage=sys.argv[1:]
assert component in ('boot-L','boot-R','glove-L','glove-R')
base=root/'harness/out/rider-rebuild/mobile-mesh02'/component
if mode=='prepare':
 intake=base/'intake01';out=base/stage
 assert not out.exists() and not intake.exists()
 index=('boot-L','boot-R','glove-L','glove-R').index(component)
 subprocess.run(['node',str(recipe/'extract.mjs'),str(root/'harness/out/rider-rebuild/selected-ankle-field42/runtime02/rider.glb'),str(intake),str(index)],check=True)
elif mode=='bake':intake=base/'prepare01';out=base/stage
else:raise ValueError(mode)
subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','--threads','2','--python',str(recipe/'rebuild.py'),'--',mode,str(intake),str(out)],check=True)
