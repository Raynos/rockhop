Both selected gloves completed; save was never reached.

Actual03 ran71.804seconds then hit65GiB anonymous, child−15. Both scratch releases and unused-hoodie skip occurred. The new GLOVE_CHECKPOINT_SAVE marker is absent: full protected-state comparison in stop_after_gloves occurs before checkpoint.save. No native save was started, so this attempt does not measure uncompressed saving or establish compression as the earlier cause. Shared host growth remains unisolated.

Move the explicitly unaccepted constructed-native checkpoint before the expensive after-comparison; preserve expected source fingerprints and require a separate reopened comparison before protected-state success. Keep all geometry and guard limits unchanged. No moving art acceptance.
