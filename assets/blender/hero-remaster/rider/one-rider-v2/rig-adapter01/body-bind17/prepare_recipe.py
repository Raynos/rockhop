"""Copy only the proven source-sheet clipper; retired authored rings excluded."""
from pathlib import Path
base=Path(__file__).resolve().parent
source=base.parent/'body-bind13/build_orbits_clearance.py'
prefix=source.read_text().split('bridge=[]')[0]
prefix=prefix.replace("ROOT/'rig-adapter01/body-bind13/construction01/correction02'", "ROOT/'rig-adapter01/body-bind17/construction01'")
prefix=prefix.replace("REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind13/construction01/correction02'", "REPO/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind17/construction01'")
(base/'build_graft.py').write_text(prefix+'\n'+(base/'graft_fragment.py').read_text())
