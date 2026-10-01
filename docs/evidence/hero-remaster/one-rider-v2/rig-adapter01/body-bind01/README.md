# First full nineteen-bone skin probe

Actual new character, CPU2 Blender standing-to-sitting animation, two camera
clips and all48 decoded frames. Five exported skin primitives use exactly
19 joints with at most four normalized finite influences. Source positions
and topology were preserved before binding; source master hashes remain
unchanged. Hidden shoulder/hip/elbow/knee/ankle joints are documented
estimates. Wrist joints are measured from the native new hands.

Parent sees no obvious wrist opening or face/neck tearing in the played
probe. This draft is **unaccepted**: independent synthetic extreme-pose
checks find ~58mm arm and ~42mm leg shortfalls. Estimate placement needs
correction before production IK evaluation. Skeletal palm sockets are
diagnostic and open fingers are not grip delivery. No seated chair target,
UniMate sampling, Garage motion, new LOD, or game-ready claim.

`build.py` reproduces the private bind/probe; `verify_glb.py` validates the
export structure and weights; `review_clip.py` encodes, decodes and boards
the actual frames. Runtime masters remain in ignored localai storage.
