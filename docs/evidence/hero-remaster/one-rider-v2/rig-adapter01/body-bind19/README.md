# Local hip pose-corrective basis — unaccepted checkpoint118

A local/global ARAP solve uses actual source triangle edges and exact-position
aliases, hard unchanged patch boundaries and soft proximity to the original
played shape. It adds1mm clearance against the48 actual upward seat triangles.
1694 physical vertices move within source Y.72–.959175m and pure pelvis/thigh
support. No head/neck/hood/sleeve/hand/foot change, skeleton or contact rewrite.
Fifteen fixed iterations, six actual recorded poses, no parameter sweep.

CPU hip fold indicators reduce311→2 neutral and443→15 maximum backward lean;
upper-leg indicators reduce152→0 and148→0 respectively. Worst hip stretch
4.606→3.466x. All six local projected negative seat-vertex counts are zero;
neutral clearance becomes1mm. Original contact reconstruction remains16.722nm.

This is promising authoring evidence, not an accepted character. Normal-fold
counts use transported ARAP normals and do not prove whole-surface collision
or a natural silhouette. Source corrections reach21.456cm; posed changes
reach15.196cm. They require actual visual inspection and continuous rig-driver
validation. The finite iteration residual remains about0.37–0.74mm; no claim
of converged exact isometry. No GLB, GPU, physics or production changes.

The inverse exact recorded skin transform converts each posed sculpt to a
source-space delta. Minimum skin singular values stay above.1; reapplying the
same matrices recovers targets within1e-12m. Parent repeats all6 solves and
86 frozen buffers reproduce exact SHA. All source/target f64s are retained
privately with archive receipts. One NumPy2 batch-vector shape error stopped
before saved targets and was corrected without changing the shape method.

Next: private append-only corrective targets with an explicit continuous
relative thigh/pelvis driver. First judge moving shape in matched side/rear
textured and gray, then body/face vs mockups. No static-only game-ready claim.

[ARAP research paper](https://igl.ethz.ch/projects/ARAP/arap_web.pdf) documents
the local rotation/global position method. This measured implementation adds
specific source boundaries and seat constraints; research is no acceptance.
