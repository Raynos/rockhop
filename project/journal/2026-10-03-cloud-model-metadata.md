# Generic cloud model metadata audit

Finding: CLI 0.159.3 Thread.model is configured/persisted metadata, explicitly
not per-turn telemetry; Turn lacks an execution-model field. No supported
active-cloud metadata reader is exposed here. Keep user-provided provenance
and no default model. Add generic session/model regression coverage.

Validation: All63hook tests pass, including Sol and Luna isolation, model
changes, absent-route failure and all prior desktop/cloud commit gates.
Saved7static protocol types and SHA256 pins; no server or UI was started.
Evidence: docs/evidence/cloud-model-metadata-2026-10-03/. Ask258.

Limits: Public schema does not describe every private cloud backend. User
authorization is not automatic execution-model detection. Cleanup remains
conditional; unique ignored assets and other owners' active work stay intact.
