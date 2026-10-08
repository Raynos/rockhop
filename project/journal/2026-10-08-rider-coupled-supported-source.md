Finding: The private solver now samples the arm/leg contact-gap crossover within its existing20degree interval, at most11candidates. Physical COM diagnostics/tests explicitly preserve the actual X/Y contract and report finite lateral COM separately.

Validation: Same selected72b90source with calibration02 passes8targeted actual-source tests, exit0/2.309s, covering41leans, fixed lengths, X/Y COM, bike-local invariance, all75reset byte identity and crash/restart. Earlier7pass/1XYZfailure retained; exact baseline/refined COM comparison retained compressed. Baseline lateral maximum12.764um, refined17.203um; no proven rounding attribution.

Limits: Static source contains no clips, so authored-clip test intentionally excluded. Actual Pro failure-neighbourhood continuity, full surfaces and solve cost pending; no global optimality, anatomical or art acceptance. No physical/anatomy/source-appearance changes; R0–R5open.
