Finding: Save-first was not actually achieved: full protected-state after-scan preceded native checkpoint. Actual03 dies after both glove constructors but before its save marker.

Validation: Actual71.804s/65GiB/child−15, complete worker and ancestry identities retained. Parent traced stop_after_gloves order and verified absent GLOVE_CHECKPOINT_SAVE marker.

Limits: No native checkpoint or measured compression benefit. New04 separates save from reopened geometry qualification without claiming success prematurely.
