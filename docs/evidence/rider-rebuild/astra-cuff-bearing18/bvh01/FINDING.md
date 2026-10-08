# Actual Blender confirms world-coordinate cuff ray miss

The exact native07 failed source bearing has no world-coordinate Blender BVH cuff hit. The same actual triangles and ray, translated into a wrist-relative frame before float conversion, yield41.087783873mm, matching finite double triangle distance41.087783117mm. Actual wearer hits exist in both frames at33.484254032/33.484261483mm. Floor surgery cannot affect any source face at this station.

Keep every source bearing, existing finite0.3m ray bound, geometric checks and selected source. Correct construction by conditioning actual cuff/wearer ray trees at the wrist before converting to mathutils.Vector; original B.hit_radius currently rounds the origin too early. Any missing cuff query must still be diagnosed or resolved against actual finite retained triangles, never skipped or replaced with a body profile.

Validation: Actual CPU2 Blender replay exits0/1.169s; parent checks the exact source/input and four BVH returns against sparse finite-triangle replay.

Limits: One bearing identifies a numerical defect. No new constructed model, full cuff containment, sleeve geometry or dressed moving art passes. Native08 remains pending.
