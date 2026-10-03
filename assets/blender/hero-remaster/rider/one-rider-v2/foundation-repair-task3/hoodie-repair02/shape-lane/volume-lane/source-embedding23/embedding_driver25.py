"""Public source embedding API; frozen24 transfer math remains unchanged."""
import numpy as np
from embedding_driver24 import SourceEmbeddedSleeve as Transfer24
from chart_labels import MORPH
class SourceEmbeddedSleeve(Transfer24):
 def __init__(self,path=None):
  super().__init__(path);f=self.f;self.changedPhysicalAliases=np.r_[f['embedSourceAliasesL'],f['embedSourceAliasesR']];self.embeddingAlpha=[np.zeros(len(f[f'p{i}']))for i in range(5)]
  for side in ['L','R']:
   _,_,lookup=self.mapping[side]
   for pi in range(5):
    rows=lookup[f[f'physicalWeld{pi}']];selected=rows>=0;self.embeddingAlpha[pi][selected]=f['embedAlpha'+side][rows[selected]]
  self.lastPlain=None
 def plain_source(self,D,closed=False):
  f=self.f;return [np.einsum('vb,bjk,vk->vj',f[f'W{i}'],D,np.c_[f[f'p{i}']+(MORPH[i]if closed else 0),np.ones(len(f[f'p{i}']))])[:,:3]for i in range(5)]
 def deform(self,D,closed=False):
  q=super().deform(D,closed);self.lastPlain=self.plain_source(D,closed);return q
