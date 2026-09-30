# Fresh anatomical head feasibility: rejected fit

The parent rejects this current surface: the narrow dense fit leaves a
visible left cheek/nose scar, and jaw/brow proportions remain too delicate
and generic for the approved adult male target. This is an anatomical
retopology alternative, not an accepted source direction or game-ready head.

The first prototype preserves real CC0 MPFB eyelid, lip, nose, ear and scalp
topology from a freshly instantiated source. Native CC0 eye surfaces were
instantiated against that source. Their first placement fell below the
eyelid openings; one explicit component translation onto measured fresh
anatomical eye anchors corrected the visible placement. Both prototypes,
recipes, outputs and actual gray images remain frozen. No historical
production mesh was copied.

[Aligned actual four views](mpfb-v4-eye-aligned/gray-four-views.jpg) and
[aligned actual closeups](mpfb-v4-eye-aligned/closeups-four-views.jpg) expose
the scar rather than concealing it. [First eye-placement evidence](mpfb-v4-fast/closeups-four-views.jpg)
is retained. Four-view renders use the unchanged dense-source framing;
closeups use the separately recorded tighter camera and light aim.
Both use Blender 5.2.1, Cycles CPU, four threads and twelve samples.

The explicit source-to-native adapter uses scales X=2.5, vertical=2.035,
depth=2.0, followed by smooth normalized Gaussian landmark displacement.
That initial displacement moves 4,377 cage vertices at most 0.005013 native
units; it is separate from the later dense-fit bound. The subdivided skin
then accepts 601 verified bare-skin snaps, at most 0.003989 native units.
10,370 samples have no dense surface within the 0.004 bound; 1,625 fail the
normal gate. These accepted-subset metrics do not establish whole-head
likeness, and the rejected visible scar shows that even a bounded snap can
damage appearance.

Measured skin topology has 69,681 vertices, 139,136 triangles, zero
nonmanifold edges, zero area-degenerate triangles, and one 224-edge neck-base
boundary. That base is visibly jagged and remains unjoined. Native eye
surfaces contain four separate cornea/sclera components, each with a
40-edge source boundary. The actual sided eye bounding-center separation
is 0.156924 native units, about 65.91 mm at the proposed 0.42 m/native
display scale. Construction's 0.162 entry is the requested landmark target,
not the measured final separation.

Scalp geometry is continuous with the anatomical face; it has no approved
buzz material. Skin/eye construction currently drops source UV coordinates.
No usable character UV, texture/detail bake, neck join, rig, animation,
contact, likeness or gameplay acceptance is claimed. Full original dense
Pixal data and the fresh anatomical source remain unchanged, as verified
by before/after SHA256 in [verification](verification.json).

Owned recipes are `mpfb_head_v4.py`, `mpfb_head_v4_eye_aligned.py` and
`verify_mpfb_v4.py`. Large frozen masters are outside Git under
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/head-cleanup/`
in `mpfb-v4-fast` and `mpfb-v4-eye-aligned`. Frozen recipe copies have matching
construction hashes there. The initial slow preparation recipe is retained
as `mpfb-head-v4-frozen.py`; stopping that performance bug occurred before
fit or output and did not erase any anatomical failure.

The parent selected one targeted alternative after committing this finding:
remove the scar-producing snap and use explicit reference jaw/brow landmarks
with smooth transitions, protecting feature loops. No global refit/remesh
or bake is authorized by these topology counts. The original feasibility
deadline remains 00:31:54 UTC. Prior two original head-repair failures,
two unconstrained implementation gates and the rejected constrained cage
remain preserved; this alternative does not reset them.
