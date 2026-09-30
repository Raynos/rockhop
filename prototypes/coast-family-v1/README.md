# Coast family C1–C3: focused shared-kit review

**Status:** unaccepted art candidate. All three routes are playable; none has
passed a whole-course visual and uncoached phone-rider sign-off. The next art
pass reuses the existing Coast harbor/frontage bank and course geometry. It
targets contact materials, water/shore continuity, obstacle readability and
distinct composition across C1–C3. It does not commission another bespoke
model bank or change physics.

[`collider-guides.json`](collider-guides.json) is generated from current
`compileTrack` output by [`extract-guides.mts`](extract-guides.mts). Collider
hashes are C1 `76ea3119b6f91726`, C2 `df72daa55f60a8bf`, and C3
`dcd871366552383e`. Its XY profiles and obstacles constrain every scenic
choice. Preserve the actual tire path and the view into each landing.

| Course | Protected riding windows | Focused shared-kit target |
|---|---|---|
| C1 Low Tide | Brake x185.5; deck x209.6–255.13; causeway x285.13–347.13 | Retain existing contact ground; review authored brick/sawtooth frontage in motion. Preserve edge stripe, obstacles and sea fallback. |
| C2 Crane Hop | Pier 2 x103–137; pontoon x203.4–229.4; crane takeoff x301.4–306.84; barge landing x312.34–337.34 | Reuse Coast harbor materials and structures, clarify real pier/pontoon/barge contacts and the flight-to-landing sightline. Keep all collider skirts. |
| C3 Hull Breach | Stern x62.4–96.04; bilge x150.04–183.04; breach x250.24–304.02; slipway x360.02–390.02 | Reuse existing hull/debris and water grammar, improve surf/shore depth and the visible breach landing. Keep the curled lip and collision geometry truthful. |

The C1 combined ground+frontage V3 is rejected after a matched full ride and
two fault/retry windows. A darker ground tint trial also failed the contact
read. See [`C1_REVIEW.md`](C1_REVIEW.md). The two-file
[`frontage-only.patch`](frontage-only.patch) preserves current ground and
changes only the Coast bank selection and warehouse placements. It is a
candidate, not integrated or accepted. No current source or public asset was
edited by that patch.

C2/C3 reference footage:
`docs/evidence/course-remaster/c2/pier-art/after/full-final/sheet.jpg` and
`docs/evidence/course-remaster/c3/breach-art/after/rookie-full/sheet.jpg`.
The selected C1 harbor reference is
`docs/evidence/course-remaster/coast-authored-integration/v2-water-refined/after/full/sheet.jpg`.
These are played-frame indexes, not posed approval images. Next review uses
matched full rides plus fault/retry at 852×392 landscape, then quiet phone
performance and uncoached physical-phone riders. Only the parent integrates
shared renderer hooks and judges course sign-off. Current total: **0/12**.
