# Cached normal startup audit

Finding: The current offline run takes 12,479 ms through normal loading.
The partial ship-gate hook skips that path; its ~197 ms figure cannot
contradict the player-flow delay or establish a boot improvement.

Validation: Read current boot/e2e sources and saved normal offline, partial
gate and historical WebKit reports. No new browser or timing run.
[Audit](../../docs/evidence/course-remaster/cached-startup-audit/README.md). Ask 126's speed target remains open.

Limits: No causal attribution. Cached asset traversal, hero decode, shader
work and pre-entry scheduling require one frozen normal-app phase trace.
No runtime, budget or physics changes. Physical phone startup remains open.

## Measured normal-app phase trace

Finding: The loader's own phase rows expose 5,827 ms first-frame work and
269 ms cached pack reading. Its removal occurs at page time 13,696 ms;
the harness observes that later. The suite hard-codes software launch flags
despite the requested Metal environment, so hardware attribution is invalid.

Validation: One immutable normal-app offline suite passes 11/11, preserving
real offline assets/purchase/swaps and exact ride hash. Harness typecheck,
scoped lint, init-script parsing and whitespace checks pass.
[Phase report](../../docs/evidence/course-remaster/cached-startup-audit/trace-swiftshader/summary.json).

Limits: Actual GL renderer string is missing in this first trace. Rounded
loader rows and observer timestamps are labelled; no isolated causal or
physical-phone speed claim. Correct backend selection/verification next.
