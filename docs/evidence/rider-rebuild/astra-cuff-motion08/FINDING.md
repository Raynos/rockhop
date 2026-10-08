# The remaining fragment is a different exposed cuff sector

**Keep selected geometry ancestry and all weights; change one connected proximal cuff sector.** Garage09's direct current-triangle rays identify right glove native vertices 120752/120746/119253 and 143964/144364/144043. The earlier sphere-culling rays missed these real glove surfaces. Reconstruction from the exact GLB and captured live palettes agrees with all six live vertices within **2.55e-16 m**.

The first triangle is **7.39–7.81 mm outside at rest**, **7.24–7.68 mm outside posed**. Its nearest selected guide vertices **3593/3635/3384 received zero cuff05 displacement**. The second triangle maps to **4118**, received only **0.95 mm**, and remains **5.61–6.17 mm outside at rest / 5.63–6.18 mm posed**. Applying the nearby sleeve's rest-surface weight field to these glove points changes their posed positions by only **0.002–0.038 mm**. These are uncovered rest-fit sectors, not evidence for weight tuning.

## Bounded final source proposal

Use one continuous cuff-band taper through **3384 → 3593 → 3635 → 4118** on both saved selected guides. Interpolate the radial contraction across this connected sector and blend its perimeter; do not apply four independent bumps. The measured controls lie 22–24.5 mm up the forearm, below cuff05's 30 mm full-strength threshold. The new controls must receive their measured displacement without that old attenuation. Preserve all protected local04 palm/digit vertices, original UV/PBR/weights, and the corrected old 5713/5187/4968 lip.

| Guide | R axial / radius mm | R inward offset mm | L axial / radius mm | L inward offset mm |
|---|---:|---:|---:|---:|
| 3384 | 23.843 / 37.064 | 9.151 | 23.768 / 37.230 | 12.391 |
| 3593 | 22.043 / 36.133 | 8.290 | 21.976 / 36.288 | 11.696 |
| 3635 | 23.511 / 36.972 | 9.059 | 23.437 / 37.138 | 12.262 |
| 4118 | 24.500 / 36.694 | 7.501 | 24.431 / 36.604 | 10.769 |

These are incremental offsets from **current cuff05**, along each control's inward forearm radial direction. Exact native/source vectors are in `receipt.json` → `hands` → `proposedGuideControls`. The projected controls independently remeasure **1.458–1.502 mm inside** the actual sleeve. All eight controls have exactly zero prior anatomical04 brush displacement. Left/right amounts differ because the actual sleeve surfaces differ; do not mirror one amount or impose a global offset.

This is a measured source proposal, not an authored or accepted result. Transfer through the established dense correspondence, verify triangle orientation and unchanged protected fields, remeasure the full affected dense sector and old witnesses, then judge the actual Garage orbit/grip film. The control margin alone does not guarantee the dense transfer or moving silhouette. This is the second and final bounded cuff geometry mechanism under the parent's failure budget.

Reproduce with the existing NumPy Python, capped BLAS threads, running `inspect-current.py`. Clean read-only run: exit 0, approximately 0.5 seconds. Source GLB SHA and full live-capture SHA are pinned in `receipt.json`. No native, asset, material, rig, or browser state was changed.
