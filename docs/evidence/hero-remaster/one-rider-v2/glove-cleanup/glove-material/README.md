# First glove material bake — setup rejected

Native hand UV copying and isolated seam-band layout have zero strict interior
overlap pixels. The first bake nevertheless targeted **both body and glove
materials into the same image**. Body UV coverage was not isolated and may
contaminate glove texels. This is a bake-selection setup failure, not an
anatomy, native UV or generator failure. The bodyPBR master/GLB and three maps
in this runtime namespace are **unaccepted failed bake evidence**.

The exact recipe/output hashes are frozen in failed-bake-selection01.json.
Source clean master, canonical native source, body geometry, original UVs and
native weights remain unchanged. The specific proposed correction is a copied
glove+seam-only bake helper with the same native UVs and geometry, followed by
binding its actual maps to the untouched full body. No corrected bake is
started before the parent checkpoint decision.
