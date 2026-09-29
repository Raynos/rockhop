# Selected A map HUD — played landscape gate

The user selected [command strip A](../../../assets/design/worldmap-3d/hud-round/a-command-strip.png). The actual 3D island now carries a persistent bottom HUD: medal progress, previous/next level, a selected-course tile with its real art and lock/medal state, a twelve-level picker, and a one-tap **Play Next** target. Rotate and Menu sit above the map. Tapping a tower still selects it, and dragging still moves the island by default.

## Real browser evidence

- [852×393 command strip](command-strip-852x393.png) with a seeded, valid three-medal Coast save. The first unmedalled unlocked course is **04 · A1 Sawdust**, and the orange button says **Play Next · A1 Sawdust**.
- [667×375 compact layout](command-strip-667x375.png), [all twelve picker entries](twelve-level-picker.png), and [locked D1 rule with Play Next still available](locked-stop-play-next.png).
- [Silent played WebKit clip](played-map-hud.mp4) and [machine report](report.json). The clip enters from Menu, browses next/previous, opens the picker, selects a locked Quarry stop, then uses Play Next to launch **A1** without selecting its flag again. It records no page or console errors.

The 852×393 and 667×375 controls all measure at least 44 CSS pixels high and wide, stay in the viewport, and do not overlap. The picker lists 12/12 campaign courses. A locked selection disables its Ride tile and shows “Medal every Alpine track”; it does not change the unlocked Play Next target. The earlier [played map gate](../world-map-pan-focus/README.md) still passes 12/12 tower taps, pan after selection, Rotate, portrait prompt, and selected Ride handoff. The [current four-section host Metal gate](metal-four-section-gate.json) passes 11/11 boot, clear, crash and restart checks; its golden source stamp is stale after unrelated scene edits, so that gate is partial evidence, not a store ship verdict.

The screenshots were captured before this implementation was committed, so their developer build stamp names the preceding `0e75f415` base; the pictured HUD code is the working-tree candidate. The real public SHA must be checked after production deployment. Physical iPhone readability, touch feel, frame pacing and battery remain release gates.

## Follow-up: tower labels and medal cues

The user's chosen A reference prompted a second [played visual pass](label-fidelity/command-strip-852x393.png). Each 3D flag now carries a camera-facing number plate with a four-step Bronze/Silver/Gold/Diamond ladder, painted from the saved medal; the dock's selected-course tile shows the same ladder at touch-screen size. [Medal-state capture](label-fidelity/medal-state-markers.png) exercises all four ranks and a locked tower. The [smaller landscape layout](label-fidelity/command-strip-667x375.png) and [locked tile](label-fidelity/locked-stop-play-next.png) were captured from the same build.

The [played HUD clip](label-fidelity/played-map-hud.mp4) and [report](label-fidelity/hud-report.json) pass Menu → Map → next/previous → 12-course picker → locked selection → one-tap Play Next into A1 with zero WebKit errors. The [played map clip](label-fidelity/played-map.mp4) and [report](label-fidelity/map-report.json) pass all 12 tower taps, pan immediately after focus, Rotate, portrait prompt and Ride handoff. The 852×393 host WebKit sample is 48 fps, 290 draw calls and 414,266 triangles; the earlier sample was 48 fps, 280 calls and 414,554 triangles. This is a host sample, not iPhone performance evidence. The [four-section host Metal gate](label-fidelity/metal-four-section-gate.json) passes 11/11; its flat-test golden source stamp is stale. The follow-up screenshots carry the preceding build stamp `13134604` because they were captured before this round's commit.
