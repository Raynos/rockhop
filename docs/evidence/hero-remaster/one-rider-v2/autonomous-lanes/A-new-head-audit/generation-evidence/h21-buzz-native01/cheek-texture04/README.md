# Correct color transport proven by actual CPU bake

The original sRGB image shader bakes the sampled texel to RGB200/135/110.
Using that encoded value directly as linear shader color instead produces
RGB229/192/175. Decoding sRGB before assigning linear color reproduces the
original shader PNG byte-for-byte. Three actual16x16 Cycles CPU emission
bakes establish this; source image and model remain unchanged.

The preceding cheek geometry remains usable: one physical component, zero
boundary edges and positive cap separation. Its pale PBR result stays
rejected. Next apply the proven conversion and isolate inner/exterior UV
islands, preserving every repaired position/normal/index and original
source buffer outside the local patch. This proof does not accept a face.
