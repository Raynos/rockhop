Finding: Startup service-worker update work could outlive its capped wait, adopt a late install and reload normal play or Garage. Deadline now cancels startup-only state/control/reload listeners and ignores late update completion; explicit player update still works.

Validation: Six lifecycle regression cases pass, including late update, late install, stalled handover, on-time update, first-install claim and explicit cancellation. Inline startup test passes with8KiB budget; full typecheck and scoped lint pass.

Limits: Reproduced code-level late-reload defect, not proof it caused the reported phone event. Real phone OOM/context loss and normal played lifecycle comparison remain open; code is not yet deployed.
