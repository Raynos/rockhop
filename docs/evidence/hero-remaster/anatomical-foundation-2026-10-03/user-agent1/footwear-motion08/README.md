# Matched footwear movement — unaccepted

Source08 has complete foot uppers, separate closed soles and real ankle
openings. Its rest test passes, but the explicit ankle/toe test rejects a
movement-safe claim. Preserve this source as a control; do not promote it.

`motion.json` records all625 native samples, exact region vertex/face/UV
ancestry and immutable stream hashes. `outcome.json` extracts the failure:

| Motion | Measured samples | Frames with new-body contacts | Max upper pairs | Max outsole pairs |
| --- | ---: | ---: | ---: | ---: |
| Original FK | 529 | 0 | 0 | 0 |
| Added ankle20deg/toe15deg | 96 | 42 | 142 | 357 |

At11.75s/source564 the upper has142 contacts and the virtually capped
below125mm foot enclosure proxy leaves20L/23R witnesses outside. At12.75s/
source612 the outsole has357 contacts. Triangle overlap and the capped
three-axis majority ray proxy are diagnostics, not signed clearance.

The matched film plays157 samples at12fps, one continuous full orbit:
LEFT old appearance05, RIGHT complete08. Both share the exact body, rig,
pose and corrective coefficients. Source materials and UVs are preserved;
baked mesh normals are recomputed. The display includes only footwear,
feet, lower calves and jeans cuffs; the lower-leg crop is deliberate and
is not a whole-rider art judgment. The final96 measured samples are added
ankle/toe motion, not recorded supported bike motion. No recoloring hides
coverage failures. Generated media/streams remain local; receipts pin them.

`ship-round36/report.json` is the separate shipped-control gameplay gate:
4810 byte-identical input ticks, clear40.083333333s, crash103 and restart1tick,
cold boot2934.657ms, frame submission3.5ms, errors0. It is not a candidate
footwear or physical iOS qualification; the existing track triangle-budget
warning remains in the report.

The latest human architecture preference is properly fitted skinning plus
lightweight consumed collision-aware corrections, with secondary motion
only where it helps within the mobile budget. Preserve full-cloth controls;
full-body cloth is not the default. This test adds no collision response,
and rest-fit or original-FK success cannot excuse the ankle/toe failure.
Agent3 owns actual runtime collision response; root judges moving form.

Film: `review/matched-old05-complete08-footwear-v1.mp4`, SHA256
`3075788373ac80290300968ef51761508631f0a78f5153c0168fc4c33ccb83f9`.
All157frames fully decoded, one silent H264 stream, exact12fps timestamps,
13.083333s duration and minimum visible normalized border0.138269.
`review/movie.json` and `review/review.json` freeze those receipts.
