"""Archive completed baseline films in a bounded two-thread CPU sequence."""
from pathlib import Path
import subprocess
import sys

base=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-hips11')
recipe=Path(__file__).resolve().with_name('archive.py')
for prefix in ['', 'framed02']:
    for angle in ['side','rear-three-quarter']:
        for surface in ['textured','gray']:
            folder=base/prefix/angle/surface
            if (folder/'frames-archive.json').exists():
                assert not (folder/'frames').exists()
                continue
            subprocess.run([sys.executable,str(recipe),str(folder)],check=True)
