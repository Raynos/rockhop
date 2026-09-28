# Finish moment prototype review

The standalone [prototype](../../../prototypes/finish-remaster/) tests a clearer finish hierarchy at the user's landscape phone size. It does not replace the game's HUD. It uses a frame from the [played C1 finish clip](../gameplay-audit/clips/finish/clip.mp4), plus local game fonts. The other result times are explicitly sample data.

## Played evidence

- [8.4-second silent headless interaction clip](interaction.mp4): first clear → new PB → medal upgrade → no gain, then one-tap Retry, Next, Map and Replay routes. The [contact sheet](interaction-contact.jpg) samples the moving clip; it is not the primary evidence.
- [852×393 first-clear](first-clear.png), [new PB](new-pb.png), [medal upgrade](medal-up.png), and [no-gain](no-gain.png) captures.
- [Retry](retry-route.png), [Replay](replay-route.png), and [Map](map-route.png) are visibly identified as prototype route states. The replay bar is illustrative, not a deterministic replay.
- [667×375 compact landscape](compact-landscape.png) and [393×852 portrait prompt](portrait-prompt.png) were rendered in the same silent headless session.

At 667×375, button rectangles measured Retry 187×55, Next 159×55, Map 127×55, Replay 159×55 CSS pixels. Document scroll stayed exactly 667×375 and the report stayed on screen. The browser reported no page errors. The recording is H.264 852×394 because the encoder pads the odd 393-pixel height; screenshots retain 852×393.

## Findings and remaining failures

The result now spends its limited space on one earned medal, time, PB relation, faults, a next riding goal, and four labeled actions. First clear, a faster PB, a medal upgrade, and a repeat clear are visually and verbally distinct. Scrap earned and wallet are dashes with a pending note, so the prototype does not invent a reward ledger.

The hero uses an enlarged gameplay frame, and its rider is still soft; the checkered finish is outside the tighter crop. Production needs an authored camera move that keeps the actual bike and finish line in one strong shot. The clip proves the interface transitions, not game-engine restart latency, a working Next/Map destination, deterministic replay, or reward correctness. The small pending-reward note at 667×375 is near the lower edge of the report and should be reduced or moved when real economy data is known. Physical iPhone touch and safe-area testing remain open.
