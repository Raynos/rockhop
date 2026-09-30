# Twelve-course graphics progress board

Before is on the left; the latest accepted art capture of the pictured location is on the right. These are frames extracted from actual played recordings with their original HUD. No artwork was generated or repainted.

- [Coast: C1, C2, C3](1-coast.jpg)
- [Alpine: A1, A2, A3](2-alpine.jpg)
- [Quarry: D1, D2, D3](3-quarry.jpg)
- [Snowline: S1, S2, S3](4-snowline.jpg)

The before footage is the saved 2026-09-29 [start-of-remaster baseline](../BASELINE.md), frozen at `609293eaac58913420a1e06ca8fc530bfc907cc1`. It already includes the first mechanical difficulty retarget and some older art. It is not the original accelerator-only demo. The after column comes from accepted scenery rounds preserved alongside their full moving rides. It is not a fresh screenshot of production or of the current unfinished audio, hero and Pro candidates.

## Reading the comparison

The initial baseline uses high renderer quality at 852×394; most subsequent accepted art captures use low quality at 852×392. Camera framing and video cadence also differ. The selected frames are close in recorded simulation time, but this is a visual progress survey, not a pixel-identical renderer A/B. [frames.json](frames.json) records each video path, SHA-256, frame number, cadence, dimensions and any video-window clock offset. Rebuild with `/opt/homebrew/bin/python3 docs/evidence/course-remaster/progress-board-2026-09-30/build.py` (Pillow and FFmpeg required).

D3 repeats the baseline because no later course graphics pass has landed. S3 shows changed teaching cues, with no substantive environment-art remaster. The new Blender tug and Alpine tree kit are still unaccepted candidates and are excluded. Small landmark/material changes do not close any full course: **0/12 courses are signed off**.

The relevant complete moving rides and limits are in [C1](../c1/brake-sightline/README.md), [C2](../c2/pier-art/README.md), [C3](../c3/breach-art/README.md), [A1](../a1/mill-complex/README.md), [A2](../a2/README.md), [A3](../a3/loader-cab/README.md), [D1](../d1/contact-road/README.md), [D2](../d2/cart-run/README.md), [S1](../s1/route-read/README.md), [S2](../s2/cornice-landmark/README.md) and [S3](../s3/README.md). The D3 bridge pass preceded the baseline; see [its historical comparison](../../d3-bridge-visual/README.md).
