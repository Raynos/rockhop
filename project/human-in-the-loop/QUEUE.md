# Human queue

Things that need **you**, not an agent. Everything else is `docs/tasks/ASKS.md`. Keep it short; **delete a line once it is
decided** — the decision lands in the thing it changed (the plan, the SPEC, the ASKS row). Each line leads with what it is
waiting on. IDs never reused. Ported from the FF15 demo's `HUMAN_REVIEW.md`.

- **HR-05 — First review-inbox note.** Waiting on: you — when the ✎ NOTE button ships, enter the password once and send one note;
  I pull it and the loop is proven.

- **HR-16 — Open the two store accounts (ask 86, [unified release plan](../../docs/plans/sol-6.1-2026-09-29-FINISH_TO_PUBLISH.md)).** Waiting on: you — enrol at
  developer.apple.com/programs (individual, $99/yr; your legal name shows as seller) and play.google.com/console (personal,
  $25; identity verification can take days). Start now: Google's 12-tester × 14-day closed test can't begin until the account exists.

- **HR-18 — Back up the Android upload key (ask 104).** Waiting on: you — copy `~/.config/rockhop/` (upload-keystore.jks + keystore.properties, alias `rockhop-upload`, SHA-256 `C3:61:7C:2E:…:1F:57`) to your password manager / an offline backup. It is not in git by design;
  losing it means a Play support upload-key reset. Also noted: the Android emulator gate is off at your request (machine load) — your own Android phone is the Android check once the
  internal-testing track exists (after HR-16).

- **HR-19 — Support email for the Rockhop store pages (ask 104).** Waiting on: you — both stores require a public privacy +
  support URL; `store/site` (rockhop.vercel.app) prints a contact email and refuses to build without one. Reply with the address
  to publish (a new alias like rockhop.support@… keeps your personal inbox off a public page). Then the parent deploys the site.

- **HR-20 — Recruit 12 Android closed testers (ask 104, D15).** Waiting on: you — Google opens Play production only after a closed test with ≥ 12 testers
  opted in for 14 continuous days. You said you need to recruit; gather 12 Google-account emails (friends, or a tester-exchange community) so the test
  can start the day the first build is on the internal track (after HR-16).

- **HR-21 — Uncoached C1 phone play for the twelve-course remaster (ask 170).** Waiting on: you and three fresh players — on landscape iPhones,
  have each start Low Tide without a technique briefing. Record attempts to clear, what they expect at the brake ramp before reaching it, each
  fault and the action they try next, Retry-to-control feel, the earned medal/next goal, and whether anyone voluntarily replays. A short screen
  recording plus `?review=1` notes is enough; the parent will compare this with the played bot and CLI evidence. This is a C1 sign-off gate,
  not a prerequisite for the independent course/art work.

- **HR-22 — Audio remaster audition and phone balance (ask 193).** Waiting on: you — compare the
  [before/after audition](../../docs/evidence/audio-remaster/audition/index.html) and played ride/crash mixes, then ride on
  iPhone Safari and desktop speakers/headphones. Judge musical taste, recognizable crowd/rider reactions, engine/traction
  readability, seams, mute, background/foreground recovery and Retry-to-control feel. Automated checks stay silent and
  cannot close these listening/device judgments.

- **HR-23 — Hero remaster visual and phone acceptance (asks 195, 201–203).** Waiting on: you — review the private [actual Garage/ride comparison](../../docs/evidence/hero-remaster/delivery/README.md) against the saved concepts, then judge the final candidate on your landscape iPhone and desktop. The current whole candidate is below the art target; this line does not block further autonomous art/render iteration. Sustained phone pacing and stranger attempts/restart remain release gates. Asks 218–220 authorize a rider-only five-design generation search; choose the complete body after nine-angle target/raw comparisons, then review the sitting animation and actual bike contacts as separate gates. The [earlier five rider boards](../../docs/evidence/hero-remaster/rider-selection/README.md) remain A1/A2 controls. Asks 225–226 add explicit rig mapping and matched physics lean/landing/contact evidence; two failed fixes of one defect require a new user choice, and Pixal3D remains an additional evaluated lane under the [new rider plan](../../docs/plans/sol-6.1-2026-09-30-RIDER_THREE_CHECKPOINTS.md).

- **HR-24 — Earned Rookie→Pro campaign check ([focused audit](../../docs/evidence/course-remaster/challenge-progression-audit/README.md)).** Waiting on: two fresh players — run unbriefed in landscape from empty saves through levels 1–8, earning 1,840 Scrap, buying/equipping Pro and attempting level 9, or stop at 90 minutes. Record attempts/fault corrections, medals/wallet after each clear/upgrade, retry latency and time seeking missing Scrap. Keep price/clocks fixed while measuring; assisted-agent results suggest a possible grind but do not establish one. This does not block independent art work.
