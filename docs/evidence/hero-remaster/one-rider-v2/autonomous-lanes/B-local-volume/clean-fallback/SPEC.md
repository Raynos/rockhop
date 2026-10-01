# Read-only clean hood fallback specification

**No fallback geometry has been built or chosen.** Parent reserves the last old
source-hood repair allowance for lane C. If that fails at the 15th defect-family
failure, the original cut/strip/194–43–23 seam repair lineage is retired. This
specification does not rename that lineage or restart its counter.

## Available new sources

`inventory.json` verifies four preserved NEW Hunyuan3D 2.1 candidates other than
the chosen H21-4. Their native pre-reduction shapes are retained: H21-1 has 316,248
faces; H21-2 344,464; H21-3 338,506; H21-5 312,878. Actual PBR model and 2K base-color,
roughness and metallic maps have matching generation-record hashes. These are
potential **whole-hood donors**, not accepted or clean hood assets; no extraction,
source replacement or new generation occurred. All original comparisons remain.
Hunyuan 2.1 release scope is the previously accepted Americas-only scope.

Installed native MakeHuman/MPFB contains 20 clothing categories. Actual thumbnails
of the six male casual sets and female casual/sports/male work sets show shirts,
crew-neck sweatshirt, puffer jacket, T-shirts and overalls. **No installed hood
asset exists in this audited system pack.** Material/proxy declarations explicitly
state CC0 September 2020. `male_casualsuit02` can supply newly instantiated clean
crew-neck binding topology only; it cannot silently replace the hoodie with a
crew-neck outfit. Its blue logo/textures are not the tan target.

## Recommended fundamentally new architecture

Author a complete new **four-panel hood garment**: mirrored left/right outer cloth
panels and left/right lining panels, a new neck-binding band and explicit center,
opening and lower-hem seams. Start from clean 2D textile patterns or a fresh CC0
crew-neck binding template, not any failed source strip, old cut loop or source
hood face. The H21-4 hood is silhouette/material reference only. New cloth panels
must have deliberate sewn topology and a collar/shoulder attachment; the lower
body, sleeves, gloves, drawstrings outside the declared whole-hood region, both
original UV layers and PBR materials stay exact.

The whole continuous native head/neck/clavicle skin, its UVs and eyes stay fixed.
Cloth may cover skin and share its future skeleton; it is not welded to skin.
Fit the new neck binding to actual 3D neck/clavicle anatomy and preserve the hidden
216-edge skin base. The existing horizontal Z1.515 slice is not a universal garment
opening: it crosses lower-jaw/front-neck surfaces above a nonplanar hood rim.
Do not derive the new garment from the failed 194/43/23 seams.

The new hood should retain the target's lowered front opening, taller nape opening,
room around the neck, broad outer cowl and folded hood resting on the upper back.
Use explicit curved panel boundaries, seam allowance and authored drape folds;
avoid a flat collar, rigid necklace, torus, closed overlapping neck shell or a
procedural bubble. Neutral front/profile/rear/three-quarter views must establish
natural form before any detail bake. Preserve a high-resolution new panel master,
then reduce only after visual comparison; face topology is never remeshed.

A fresh whole-hood donor from H21-1/2/3/5 is a secondary option if actual matched
gray/PBR full-hood review clearly beats authored panels. Replace the **whole hood**
with that donor's geometry/UV/materials and a newly authored neck binding; adapting
yet another strip around an old failing source seam is not a clean fallback.
Do not resume P3's stopped repairs or use historical production rider geometry.

## Material mapping and protection

| Region | Mapping/material requirement |
|---|---|
| Preserved H21-4 torso, sleeves, jeans, shoes | Exact original positions, two UV arrays and slot 0 PBR; no reset/whole-body bake |
| Preserved native gloves | Exact slot 1 micrograin leather and `NativeGloveAtlas`; protect original UV and weights |
| Fixed native head/skin and eyes | Exact native UV and approved skin/iris foundation; parent owns brows and face palette |
| Fresh authored hood outer panels | New pattern UVs, tan cotton palette matched to original body; geometry carries drape folds |
| Fresh lining/binding | New pattern UVs, warm subdued lining, sewn edges and smooth normals; no skin-color camouflage |
| Optional whole-hood NEW donor | Preserve donor UV/PBR maps; disclose source change and independently judge seams |

For authored panels, use a clean cotton shader and CPU-bake actual new-hood-only
base-color, roughness and tangent-normal maps to its new UV atlas. Metal is zero.
Cotton microstructure is subtle; detail maps cannot conceal holes/intersections.
If original hood material is used as a detail donor, it is **material reference**,
not a geometry repair or reused cut boundary; restrict samples to verified cloth
and exclude head/hair/skin. Never bake the whole body or silently clear material
arrays. Verify all maps and material slots on GLB reimport; do not call procedural
shader appearance an exported PBR texture set before that verification.

## Bounded verification before rigging

1. One 30-minute CPU construction batch produces new panel topology and matched
   neutral full-character/four-neck views. Source guards compare every preserved
   triangle, UV corner, material index and source SHA. Parent judges actual anatomy,
   folds, back and opening; mesh counts alone do not pass.
2. If usable, one bounded CPU material/export batch generates actual PBR views,
   full front/back, face closeups and an independent GLB reimport proof. Parent
   full-character and face scores must both be at least 7/10, target 8/10 against
   approved mockups. Preserve the earlier candidate comparison and failure counts.
3. Verify the actual 216-edge skin boundary, including sampled edge interiors,
   remains concealed from nine cameras. Measure actual skin/cloth distance and
   intersections rather than projected XY containment. Give a temporary neck
   rotation/bend clip and coverage evidence before claiming a hidden boundary in
   motion. This is not a final 19-bone rig or gameplay pass.
4. Once appearance passes, the parent adapts the new hood/skin weights explicitly
   to the existing 19-bone/bind/socket contract, Garage blend and shared geometry
   settings. Preserve physics-driven lean/COM/IK, grip and sole contact behavior.
   Later matched lean/landing/contact gameplay tests remain mandatory.

CPU jobs use two threads in isolated lane roots with measured memory. No model
sampling, GPU/Metal work, global package change, source deletion, production asset
promotion or commits are authorized by this read-only fallback preparation.
