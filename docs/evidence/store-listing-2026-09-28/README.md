# Store listing draft reconciled with the current game

The iOS and Android English descriptions previously advertised an Obsidian medal and four free-ride playgrounds. Those features conflict with the approved twelve-course campaign: Diamond is above Gold, and the free-ride levels were removed. Both descriptions now name the 12 courses, Bronze/Silver/Gold/Diamond, saved PB ghost and replay, one-tap checkpoint retry, and the earned 800-Scrap Pro bike. The copy avoids claiming that a first-time player has already learned the course or that physical phone timing has been qualified.

`node scripts/store-metadata.mjs` passes the platform character limits and retired/competitor-name scan: each full description is 1,318 of 4,000 characters. This is a corrected **draft**; final copy still needs comparison against the signed release build, rights declaration, screenshots, live legal/support URLs, and owner review before submission.

The metadata check now rejects the retired terms “Obsidian,” “free ride”/“free-ride,” and “playground(s)” so a later copy edit cannot silently restore those promises. The corrected listing still passes the check.
