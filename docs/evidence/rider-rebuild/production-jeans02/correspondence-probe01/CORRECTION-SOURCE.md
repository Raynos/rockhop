# One authored pelvis correspondence correction

The actual diagnostic returned exit0 in19.363s. All4656 covered black pixels
were predicted ray misses; none were black despite a predicted bounded hit.
The regional UV sample overlap was zero. Long front-waist rays reach physical
rear cloth; long rear-seat rays reach physical front cloth. Increasing the
distance would capture those wrong surfaces. Source/body enclosure is irrelevant.

The earlier452/1764 bounded front/rear-cross bins used source face normals.
Reading actual source positions shows zero of those bounded front hits at
physical rearY>.035, and zero bounded rear hits at physical frontY<-.05. They
establish opposed source normals, not physical cross-panel transfer. This
correction uses actual physical source positions and original face IDs for its
capture gate; source normal signs are not semantic labels.

The wearing receiver's flat top reachesZ1.055. Original selected front-centre
waist is lower. An exactX0 section of the original evaluated triangles reaches
frontZ1.011709/Y-.186517 and rearZ1.063292/Y+.094020. A steeply tilted cage from
the unchanged wearing surface would mix this feature-height mismatch with ray
direction. Parent authorized an independent editable projection receiver and
cage with exact inherited target face order/UV, leaving wearing95654876 exact.

The authored five-row projection controls are frozen before execution:

| Wearing targetZ | Front-centre proxyZ | Side proxyZ | Rear-centre proxyZ |
|---|---|---|---|
| .830 | .830 | .830 | .830 |
| .910 | .910 | .910 | .910 |
| .980 | .962 | .980 | .980 |
| 1.020 | .986 | 1.018 | 1.020 |
| 1.055 | 1.005 | 1.045 | 1.055 |

Eight angular controls per row keep the centre fly atX0, paired pocket sides
on their originalX signs and the lateral seam on its side. Front proxy top
is6.7mm below the actual source centre section top; rear top is8.3mm below.
Every actual XYZ proxy/cage point is in correction-controls.json. Interpolation
is fixed bilinear authoring, with no fit solver or optimization. The projection
mesh is a material correspondence derivative, never wearer fit authority.

Cage radii are measured from the complete420800-row original evaluated source.
Only `originalEvaluatedPositions` was read from the immutable lineage container;
the rejected fitted arrays/native were never used. Its arraySHA isbc3b850e….
At execution it must equal the original source freshly evaluated from9565,
element for element, before any derivative is admitted. Each of40 controls has
a ±22.5degree/±8mm source envelope, sample count and original vertex witness.
The local radial maximum divided bycos22.5 gives polygon chord allowance;
8mm authored clearance is added. This replaces the unsupported fixed25mm idea.

Representative actual cage coordinates (Y for front/rear, X for side):

| Row | FrontY | SideX | RearY |
|---|---|---|---|
| .830 | -.162911 | .236719 | .177854 |
| .910 | -.197803 | .224421 | .204681 |
| .980 | -.210256 | .200985 | .182006 |
| 1.020 | -.225899 | .192202 | .155622 |
| 1.055 | -.226867 | .185360 | .133293 |

The40 anchor receipts support these controls. They do not prove continuous
whole-cage enclosure. The worker first saves actual editable proxy/cage meshes,
unchanged wearing target, original dense/PBR and body75 into
`authored-correspondence.blend`, before the direct capture gate or any maps.
Actual native geometry work therefore survives a gate failure.

Original source and receiver faces are isolated into two physical halves at
Y-.017, with4mm source cut overlap. Receiver halves partition the original
pelvis face IDs exactly. Each proxy/cage retains the corresponding receiver's
face order, UVs and fields, and must also have identical tessellation to its
paired cage. Source cuts preserve original selected UV/corner-normal/face lineage.
Only proxy/cage normals are reset to automatic normals derived from the edited
projection geometry; the original source and wearing normals remain untouched.

The actual custom-cage rays start on the cage and point toward the projection
receiver. The gate requires every covered diagnostic sample to hit the intended
physical source half andX side, with first hit at most80mm. No missing sample
is excluded. The exact arrays, source UV/face IDs and masks persist for both
halves. Failure stops before maps, with the saved native and report retained.
Python raster/BVH precision limitations remain explicit; actual Cycles maps and
views remain the parent judge.

One admitted pelvis probe is two isolated halves × three1024 maps: selected
albedo, original packed MR and actual tangent normal. An explicit custom cage
uses no maximum-distance cutoff (`max_ray_distance=0`); the direct physical
capture gate provides the bound instead. No extrusion or distance sweep occurs.
The old .018 extrusion property remains recorded and is ignored by custom-cage
coordinates. Raw six regional maps persist. Three composite maps select actual
baked pixels by exact receiver UV ownership plus16pixel margin domains; no
covered miss is filled synthetically. Normal detail is baked in the derived
projection tangent frame and applied in the wearing target tangent frame.
That retargeted shading requires actual image review.

After saving the actual mapped wearing receiver, the existing helper renders
six close matched original-source/receiver views. Legs and underbody below
the originalZ.84 receiver cut remain unprobed. This is not a usable whole
garment, final4K, material/fit/motion/player/device acceptance.

Proposed sole parent-owned CPU2 job,600s, canonical unchanged lock controller:

```sh
env OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2 NUMEXPR_NUM_THREADS=2 \
python3 assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py \
  --out docs/evidence/rider-rebuild/production-jeans02/correspondence-probe01/cage-probe-guard01 \
  --limit-seconds 600 -- \
  /Applications/Blender.app/Contents/MacOS/Blender -b -t 2 --python-exit-code 1 \
  --python assets/blender/rider-rebuild/production-jeans02/correspondence-probe01/correct.py -- \
  assets/blender/rider-rebuild/production-jeans02/correspondence-probe01/correction-intake.json \
  harness/out/rider-rebuild/production-jeans02/correspondence-probe01/cage-probe01
```

Only lightweight immutable-array measurements, source authoring, AST/pin and
control interpolation validation ran during preparation. No Blender/model/
render/bake/fit job, prior-source overwrite, global doc, index edit or commit.
Exact source/intake/controls/envelope hashes are in correction-source-checkpoint.json.
