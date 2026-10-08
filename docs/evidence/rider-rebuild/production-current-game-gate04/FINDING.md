# Current-player Metal baseline passes; software result retained

Root initially omitted TRIALS_BROWSER_BACKEND=metal, selecting portable SwiftShader. That actual run remains preserved in production-current-game-gate03:9/11, first-frame6079.85ms and restart-frame557.34ms fail software timing limits. Physics finish/hash/crash/restart ticks still passed.

Explicit Metal headless run passes11/11: ready218.22ms, first-frame435.38ms, restart-frameP955.68ms. Recorded finish8.591666666666667 and hash622bb2554e0f9a26 remain byte-identical. Guardexit0 in5.601s; actual renderer reports AppleM5Max Metal.

Validation: parent read both actual workers and checked all11 current Metal report checks. All runs silent/headless.
Limits: existing player partial baseline only; new garments are not in player assets, and no new rider/mobile release verdict is granted. Software timing failure remains recorded rather than overwritten.
