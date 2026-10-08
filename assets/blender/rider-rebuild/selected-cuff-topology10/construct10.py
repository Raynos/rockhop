"""One parent-guarded original-source cuff construction with proven floor IDs.

Reuse the unchanged09 construction/contact/sleeve/dense-gate engine. Its output
namespace remains astra-cuff-bearing18; use a fresh authored10 directory there.
Only the pinned local reconstruction helper changes. No export or art claim.
"""
import hashlib
import gzip
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
ENGINE=ROOT/'assets/blender/rider-rebuild/astra-cuff-bearing18/construct09.py'
assert hashlib.sha256(ENGINE.read_bytes()).hexdigest()=='141e434136726814a69ff616fbb7de730750cb6680ee99b6879db7d0c6517e06'
PROOF=ROOT/'docs/evidence/rider-rebuild/selected-cuff-topology10/identity02/native-identity-probe02.json.gz'
proof_bytes=gzip.decompress(PROOF.read_bytes())
assert hashlib.sha256(proof_bytes).hexdigest()=='51546e07f98823331bc9c374dff6f3c4a7eabbf250c5ad61f09bb00403833358'
proof=json.loads(proof_bytes)
assert all(h['returnTopologyCompleted'] and h['noUnownedFinalExteriorEdges'] for h in proof['hands'].values())
spec=importlib.util.spec_from_file_location('proven_cuff10_engine',ENGINE)
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.HERE=HERE
engine.__file__=__file__
if __name__=='__main__':engine.main()
