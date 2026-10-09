# Complete native63 face failure diagnosis

Finding: All 26,528 recorded face-normal dots reproduce exactly. Of 95
failures, one is an exact inherited triangle whose BVH bearing is its
neighbor; 94 are new faces. The proposed fan union includes every failing
new target/bearing patch and preserves all prior constraints.

Validation: Four CPU fixture groups pass. The complete evidence and proposed
fixed-point extension are in
[handoff](../../docs/evidence/rider-rebuild/selected-boot-face66/source-handoff.json).

Limits: No bearing correction, new constructor or native job ran. A future
constructor requires a full face census on every iteration and independent
native qualification; the 1 mm and 0.25 thresholds remain unchanged.
