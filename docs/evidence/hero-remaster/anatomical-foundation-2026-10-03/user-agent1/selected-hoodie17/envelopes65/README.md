# Body and garment ray inventory — diagnostic, no fit

Source17 remains frozen with2552 body/one self pair and ten boundary loops.
This read-only unit measures5120 identical body/garment rays:32torso heights
×64angles and16stations×48angles on each canonical arm segment. Full ray
records are deterministically compressed in `radial-rays.json.gz`, pinned
by the summary. Queries stop at12 surfaces or1metre; no ray reaches12hits.

All body first hits are outward with zero misses. Garment has88misses,
296outward first hits and4736inward first hits. Every inward first hit is
followed by an outward second hit. Median first entry/exit spacing is about
7mm across torso and sleeves. This is evidence of a finite material wall;
it does not identify every surface as unwanted lining or establish whether
the nominal bone center lies inside the intended garment lumen.

Rejecting inward garment first hits merely because the body first hit exits
its own solid would discard most relevant measurements. Conversely, directly
inflating from these nominal-center radius ratios would be unjustified:
extreme prospective ratios reach209.126 on the left upper arm and112.514
on the left forearm. Body rays can traverse a connected torso/arm region,
and a nominal center can lie close to or inside a garment wall. Missing rays
and both orientations remain explicit; no fitting or coverage waiver.

Next measure actual source sleeve section contours/centers and wall nesting
before deriving a coherent anatomical cage fit. Preserve original donor
features/UV/PBR and the continuous elbow correction. No independent point
snaps, arbitrary global radius sweep, or global inward-face deletion follows
this report. Source native/PBR hashes remain exact; no mesh movement/save,
new capture, rig/weights, broad motion, inference, worker or promotion.
All M0–M5/mobile/root played art gates remain open.
