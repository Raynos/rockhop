# Fresh native evaluated young-adult male: gray review

This is a new native anatomical alternative, still unaccepted. The earlier
v4/v5 extraction read `body.data.vertices`, which contained Basis coordinates
instead of MPFB's active male/age shape-key mix. That avoidable construction
mistake explains their generic face. The read-only
[Basis/macro audit](basis-macro-audit.json) records an up-to-57.16 mm source
head difference. The earlier source age 0.4 also blended child/young targets.
Their two rejected manual fits remain stopped and frozen.

This recipe freshly instantiates the installed CC0 MPFB source with gender
1, age 0.50, muscle 0.60, weight/proportions/height 0.50, and native race
weights Asian 0.25, Caucasian 0.35, African 0.40. It records all five actual
applied macro keys, saves the new source, then uses native
`TargetService.bake_targets` before extracting the head. No Gaussian shifts,
manual face edits, dense snaps, or historical meshes enter this version.

[Actual four neutral-gray views](gray-four-views.jpg) and
[actual closeups](closeups-four-views.jpg) show a coherent neutral male face,
eyelids/eyes, nose, lip and ear folds, and continuous scalp. They establish
neither exact approved Pixal/reference likeness nor final texture quality.
The forehead/cheek proportions remain for parent judgment. The temporary
source-neck extraction is visibly jagged and unjoined; no hood or body join
is implied.

The sole geometry adapter is uniform scale and translation. Measured source
eye-center separation is 0.058722 m; scale 2.672332 maps it to the proposed
0.156924 native separation. The actual exported sided eye bounding-center
separation measures 0.156973, about 65.93 mm at 0.42 m/native display scale.
No old anisotropic adapter or facial displacement field remains.

Native skin and eye `UVMap` layers survive extraction and subdivision. The
exported skin has 70,322 UV-seam vertices and eye surfaces 4,187, with finite
UV coordinates; the underlying skin topology contains 69,549 vertices,
138,880 triangles, no nonmanifold edges or area-degenerate triangles, and
one 216-edge source-neck boundary. Counts do not approve appearance or
prove self-intersection freedom. No skin/eye texture, buzz material,
UV-layout acceptance, detail/PBR bake, joined body, rig or movement exists.

Approved buzz reference and the untouched NEW Pixal dense face remain the
identity/detail target; this native face is not silently substituted as an
accepted identity. Original dense/source assets and all failures remain
preserved. Target file hashes, preset, actual keys, source UVs and adapter
are in [construction](construction.json); before/after immutable source
proof, topology and actual IPD/UV measurements are in
[verification](verification.json).

The first version of `mpfb_native_male_v6.py` failed before creating any
mesh because the installed macro API returns `[name, weight]` pairs instead
of dictionaries. That preparation failure and recipe remain frozen.
The completed sibling `mpfb_native_male_v6_api_fixed.py` changes only that
API indexing. `inspect_native_macros.py` reproduces the read-only Basis
finding; `verify_mpfb_v6.py` freezes actual artifacts. This API fix does not
reset or hide any prior art failure.

Large frozen masters and the new source are in
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/head-cleanup/mpfb-v6-native-male/`.
Matching frozen recipes live in its parent directory. All four views use
the common dense-source frame; closeups use their separately recorded tight
camera/light aim. Rendering is Cycles CPU, four threads, twelve samples.
No further morphology, bake or neck fit has started. Parent geometry review
is required before advancement; the original deadline is 00:31:54 UTC.
