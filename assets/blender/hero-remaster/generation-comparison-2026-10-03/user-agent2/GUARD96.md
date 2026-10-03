# Future owned Rockhop96GiB combined stop

Human request290 supersedes only the combined anonymous-plus-wired stop.
Invoke `run_bounded96.py` explicitly for future owned Rockhop jobs. Existing
controllers and the shared original `../run_bounded.py` retain their original
profile; localai/Wildshard defaults, OS settings and foreign work are unchanged.

The actual host reports `hw.memsize=137438953472`: exactly128GiB. The new
profile refuses to spawn a child on any other physical memory identity.
Admission stays anonymous<55GiB and anonymous+wired<68GiB. Stop remains
anonymous>=65GiB, or combined>=96GiB, or time>=1790seconds maximum. The
combined change does not lift the independent65GiB anonymous limit.

Use the same fresh pre-launch `lsof` check: launch only for exit1, empty
stdout and empty stderr. Ambiguity or another holder means no child launch.
The same canonical localai `.model.lock`, `lockf -k`, offline environment,
one-second polls, actual memory reader and owned process-group termination
remain. Never queue behind or evict a foreign holder. This explicit owned
copy is not a global default or unlimited memory.

The pinned original guard has no separate pressure/swap gate: its memory
reader reports anonymous, wired and free pages, and only anonymous/combined
are admission/stop predicates. Do not describe pressure/swap protection as
newly validated or removed. No existing guard predicate is weakened beyond
the human-authorized combined stop; the original reader is unchanged.

One-second samples are reactive, not an allocation cap. An allocation can
cross96GiB between samples before owned termination; kernel/allocation time
and the five-second SIGTERM grace can extend response. PBR05 actually sampled
105.7GiB against the old78GiB threshold. The96profile has not been stressed
with a high-memory model; boundary/ownership CPU probes qualify semantics.
Recipes and receipts must name the invoked controller SHA and actual limits.
