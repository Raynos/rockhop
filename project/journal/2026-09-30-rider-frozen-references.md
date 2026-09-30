# Rider search reference checkpoint

Finding: five complete adult rider inputs and five nine-angle target boards
are frozen before inference. Native RGBA bytes have valid transparency and are
shared unchanged by Hunyuan3D and TRELLIS.2. References preserve lower native
arm angles rather than pretending to be exact 40° A-pose inputs.

Validation: parent viewed all five full-body references and generated boards;
foreground, hands and shoes fit. SHA-256 metadata and alpha ranges match saved
PNGs. LocalAI prepare freezes runner copies, settings and installed versions.

Limits: mockups are concept targets, not models. Exact yaw and foot/arm pose
vary; board 04 mixes some rotation directions. No inference, rigging, contact
pass, physics change or normal-player promotion is asserted by this commit.
