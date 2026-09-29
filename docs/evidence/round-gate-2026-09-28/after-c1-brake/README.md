# Gate after C1 brake sign

Commit `b899928d`, source fingerprint `a415fcb8`, on host ANGLE Metal (Apple M5 Max).

`TRIALS_BROWSER_BACKEND=metal pnpm harness:gate --build --only=boot,clear,crash,restart` passed **11/11** checks. The clear finished at the pinned 8.591666666666667 s and hash `622bb2554e0f9a26`; the crash reached restartable control in 25 ms and each of 20 manual restarts resumed on the next tick. Ready median was 145 ms and first synchronized frame 622 ms. [Machine report](metal-partial.json).

This is a partial host gate, not a ship verdict. It does not cover the production Safari startup crash reported afterward, physical phones, offline pack, or the full release gate.
