# T-pose215 fixture utility — unaccepted checkpoint

The private generator uses the exact consumed GLB skin order, node rest hierarchy,
inverse binds, mesh bind and declared bone-local anatomical frames. Hierarchical
FK produces desired matrices before world deformation. It retains source bone
rolls and lengths, rather than changing only the old C19 centre array.

Five meaningful CPU controls passed: actual synthetic GLB/SHA/name/order reading;
wrong-axis/bind/parent refusal; rolled-bone FK with independent pivot rotation and
child connection proof; real Three SkinnedMesh vertex deformation with nonidentity
mesh bind; and halfstep/reverse/asymmetric requests. Harness typecheck and focused
oxlint exited 0. Exact commands and source hashes are in verification.json.

Builder output is source utility only. No actual new rider is rigged, no new
binding has been invented, no rendered evidence is accepted, and public player,
physics, bike and frozen cosmetic work are untouched. Parent owns integration,
review, shared plan/journal updates and checkpoint commit.

See harness/hero-remaster/basic-pose-tpose215/README.md for CLI, manifest API,
semantic angle conventions and remaining live/render/gameplay requirements.
The existing centre-only fixture player cannot establish actual rest rotation
or bind compatibility; strengthen that guard before consuming a new fixture.
