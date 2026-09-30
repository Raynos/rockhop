# Outstanding-file cleanup on main · ask 208

Audio and hero owners landed their reviewed work on main; the parent split the course remnants into separate findings. All source, export candidates, tests, assets and evidence visible to Git are retained. Ignored editable masters, generated outputs and caches stay outside version control. No branch or worktree was created for this cleanup.

## Commits before this final status round

```
ceaf8dbb art(hero): sharpen the private Garage remaster review
0e00571a feat(audio): remaster the score and every sound family
1de7fa94 art(hero): merge the reviewed remaster and production plan
23533cd3 design(coast): reject sparse harbor in the full played ride
3e26f29a docs(alpine): preserve the seeded forest rollout proposal
d526d084 art(snowline): preserve the authored source-only landmark kit
97a76125 art(quarry): preserve an unintegrated machinery authoring recipe
659a3999 test(physics): label the p50 gate and retain its failing profile
8e052083 docs(tooling): record the verifier lint finding and correction
25d5de83 test(hero): isolate LOD selection from Garage canvas resize
```

The final round commits this evidence, plan/ask reconciliation and latest host gate. It makes ten main commits from the cleanup starting point. Candidate Snowline/Quarry source is unimported; rejected Coast hooks remain isolated in a prototype patch. Hero candidate exports remain outside the normal public model selection. Git cleanup does not increase the completed-course count: 0/12.

## Verification

- Full application and harness typecheck: pass.
- Full repository lint: pass after explicit UTF-16 comparator repair in the Snowline verifier.
- Normal build: pass, about 691 KiB player gzip against the unchanged 700 KiB cap.
- Thirteen focused Snowline/Garage tests: pass. Corrected exact-decoder output is byte-identical to the saved report.
- [First Metal partial gate](first-round-gate.json): 12/14; boot p50 329.94 ms versus 300, synced restart p95 38.78 ms versus 33. Tests overlapped; no causal attribution.
- [Second required round gate](final-round-gate.json), without concurrent root tests: 14/14, cold boot, exact C1 Rookie/Pro and D3 Pro clear, crash, single-tick restart and bundle. Boot p50 138.07 ms; synced restart p95 31.56 ms. [Built entry/version identities](build-provenance.json) preserve the shared-checkout provenance.
- Credential-pattern scan of newly committed text and outstanding files: no token/private-key pattern hits; commit hooks run for every round.

The recorded R3 CPU failure remains open; its five-microsecond limit is unchanged. Physical landscape phones, uncoached rider trials and whole-course graphics remain unqualified. Other chat owns the checked audio deployment and its Garage fixture CI repair; this cleanup is a main commit claim, not a production claim.
