"""One parent-authorized extraction, then its independent CPU check; no retry."""
import os
import subprocess

assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID'), 'Original parent guard required'
subprocess.run([
    '/Applications/Blender.app/Contents/MacOS/Blender', '-b', '-t', '2',
    '--python-exit-code', '1', '--python',
    'assets/blender/rider-rebuild/selected-glove-family81/extract.py', '--',
    'harness/out/rider-rebuild/selected-glove-family81/extract01',
], check=True)
subprocess.run([
    '/opt/homebrew/bin/python3',
    'assets/blender/rider-rebuild/selected-glove-family81/check.py',
    'harness/out/rider-rebuild/selected-glove-family81/extract01/extraction.json',
], check=True)
