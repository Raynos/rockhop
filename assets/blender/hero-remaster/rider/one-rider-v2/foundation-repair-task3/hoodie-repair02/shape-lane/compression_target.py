"""Integration hook for frozen local garment compression candidate.
Use CompressionTarget().target(matrices, posed=None).
`posed` may be root's exact same-source same-weight closed-hand skin arrays; only
computed local cage displacement is added before literal triangle correction.
Do NOT apply to different geometry/topology/weights or arbitrary world transforms.
"""
from pathlib import Path
import hashlib,numpy as np
from differential_cage import Cage,deform
from local_triangle_corrective import LocalTriangleCorrective
class CompressionTarget:
 def __init__(self):
  self.cage=Cage();self.contact=LocalTriangleCorrective()
  assert hashlib.sha256(self.cage.weightsFile.read_bytes()).hexdigest()=='a0dae08af07de02eedc05fc97bbcb76697cd86cf15ebfe61cbd09133024925b5','Frozen input weights changed; refreeze and requalify explicitly.'
  assert hashlib.sha256((Path(__file__).parent/'shape-retop-uvsafe.npz').read_bytes()).hexdigest()=='d0b765260a688beb9d474e23cdca3b602ce8497fbc0ff9e765f86d0c92fe7d77','Frozen topology/geometry changed; refreeze and requalify.'
 def target(self,matrices,posed=None):
  cage,cm=self.cage.target(matrices)
  if posed is not None:
   skin=deform(self.cage.pos,self.cage.w,matrices)
   assert all(x.shape==y.shape for x,y in zip(posed,skin)),'Primitive vertex order/count mismatch.'
   cage=[posed[i]+(cage[i]-skin[i])for i in range(5)]
  out,lm=self.contact.target(cage)
  return out,{'cage':cm,'localTriangleCorrective':lm,'qualifiedScope':'Eight initial upperclothprobes + six independent angles, all finite0cross. Tstilllargeedge strain. Fullcanonical/wholebody/continuousstockruntimepending.','clothingTopology':'shape-retop-uvsafe','headHandsHeldExactAgainstInput':all(np.array_equal(out[i],(posed if posed is not None else cage)[i])for i in [1,3,4])}
