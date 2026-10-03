# Candidate05 contact surfaces — proposals awaiting parent review

The map freezes actual current05 GLTFLoader triangles and vertex rows.
Source: appearance05/rider-source-normals.glb,
SHA256 ecc3bb87b2b9ff934c20345e47b422665f676a23f26a84622b6ec42cc0d42181.
The complete binary chunk is identical04, so primitive indices, source IDs,
morph vectors, UVs, skin and bind ancestry are exact04→05. No05 LOD exists.

| Proposed surface | Left triangles | Right triangles |
| --- | ---: | ---: |
| Body palm | 394 | 394 |
| Glove palm | 434 | 566 |
| Body sole | 679 | 679 |
| Boot sole | 389 | 373 |

The jeans posterior seat proposal contains219 triangles. Body and gear
patches remain separate. Automatic orientation/ownership rules and precise
current51 bone frames are recorded in surfaces.json; their anatomical
labels require the parent's played review before acceptance.

Every row identifies the glTF mesh/primitive/node and actual loader name,
triangle ordinal, vertex IDs, source IDs where present, raw/rest local/file
world/runtime centered positions, world/bind matrices and current joint
weights/order. Gear has no source-ID attribute; its actual current exported
rows are frozen directly. No old candidate binding field is borrowed.

The independent raw-accessor check proves exact POSITION, JOINTS_0,
_SOURCE_ID and indices. Loader weights equal float32 L1 normalization of
raw WEIGHTS_0; maximum raw→normalized difference is5.96e-8. Export seam
component counts are explicit, without a closed-volume claim.

Metres; glTF +X forward/+Y up/+Z left. File root +0.65X, runtime centering
−0.65X once. File-world→native-world is [x,−z,y]; native centered coordinates
are [x−0.65,−z,y]. All map contact coordinates are unoffset.

One134-frame6fps silent512×768 movie plays the same67 sampled synthetic
poses in gear and underlying-body views. An orbit camera exposes both sides.
Red/blue identify left/right palms; gold/green identify left/right soles;
magenta identifies the jeans seat. Diagnostic overlays alone move outward
3mm for visibility. The movie is fully decoded, has exact i/6 timestamps,
and keeps the whole rider within frame (minimum normalized border0.06049).
Native full weights can differ from exported four-weight positions; the
film labels actual05 patch streams and does not certify fit.

Agent3 owns actual bike grips/peg/saddle target proposals and independent
runtime binding. This receipt claims no supported seating, penetration,
closed-volume, visual-art, player promotion or device pass. Moving judgment
is pending. review/movie.json pins the film and regenerable local streams.
