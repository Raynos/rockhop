# Cloud model metadata and generic attribution

Ask258. The checker supports different explicit models for different sessions.
There is no Astra-6 default. This turn has no supported reader exposing its
actual cloud execution model, so its label remains user-provided.

The installed Codex CLI 0.159.3 generated the [saved protocol types](protocol/)
without starting a server or connecting to Desktop. `Thread.model` explicitly
means current configured or latest persisted model, not per-turn execution
telemetry. `Turn` has no model field. `model/rerouted` carries a thread/turn and
from/to model, but this event alone cannot establish a complete execution trace.
Token-usage types have no model identifier. The
[official app-server documentation](https://learn.chatgpt.com/docs/app-server)
documents read-only `thread/read` and model rerouting; availability of a public
protocol does not supply a connected reader for this delegated cloud turn.

Requested settings, a picker, `model/list`, a default config and the assistant's
self-report cannot prove which model executed a turn. No private cloud backend
claim is made. An authoritative runtime export would need matching session and
turn identity plus execution-model semantics, including any routed models.
No speculative adapter or raw Desktop connection was added.

All [63 hook tests](hook-tests.txt) pass. New synthetic tests exercise separate
Sol and Luna sessions, reject another session's declaration, invalidate the old
model/hash after an authorized model change, and fail with missing desktop
metadata when the explicit cloud route is absent. Synthetic labels are test
fixtures, not attribution evidence for a real session. Existing declaration,
staged-byte, provenance, desktop and ordinary-commit checks remain enabled.
See [pins and bounded findings](validation.json).

For the QA lane, its declaration at
`docs/evidence/hero-remaster/rider-contact-diagnostic-2026-10-03/user-declaration.json`
binds session `01a10103-4be7-732e-ba8c-2e3153b17015`. Set
`CODEX_CLOUD_ATTRIBUTION_FILE` to that path and run
`node .githooks/resolve-attribution.mjs`. Use all four emitted trailers in the
final block, Assisted-by last. The exact declaration bytes must be staged.
This validates the user's explicit label and provenance, not automatic model
detection or rider acceptance.

Cleanup remains conditional on publication and ownership. Ignored masters,
raw generation assets, active QA files and unpublished checkpoints are preserved.
No repository-wide cleanup or source deletion was performed.
