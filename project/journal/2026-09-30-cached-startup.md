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
