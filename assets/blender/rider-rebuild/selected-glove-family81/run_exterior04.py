"""One bounded Blender build and independent CPU inspection; no retry."""
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID'), 'Original parent guard required'
assert len(sys.argv)==3
result=subprocess.run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','2','--python-exit-code','1',
    '--python',str(HERE/'construct_exterior04.py'),'--',sys.argv[1],sys.argv[2]])
report=Path(sys.argv[2])/'construction.json'
if (Path(sys.argv[2])/'candidate.npz').exists():
    inspected=subprocess.run(['/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13',str(HERE/'inspect_exterior04.py'),str(report)])
    if result.returncode==0: raise SystemExit(inspected.returncode)
raise SystemExit(result.returncode)
