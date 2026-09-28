# ROCKHOP 3D world-map visual studies

These are generated concept images for choosing an art direction, not screenshots of the game or frames from one actual 3D asset. Each map style has nine separately generated camera studies, numbered 01–09 on its board. The generator can reinterpret small landmarks and the exact number/position of start posts between views; the production model must use one fixed mesh, one road, and exactly 12 clickable starts (three in each biome). All five studies use coast → forest → quarry → snow and avoid circular arenas.

| Style | 3×3 board | Direction |
|---|---|---|
| A | [Cinematic natural world](map-styles/A/board-3x3.jpg) | Realistic PBR island, water, quarry, forest and peaks |
| B | [Handcrafted tabletop](map-styles/B/board-3x3.jpg) | Museum-scale wood, plaster, resin and brass miniature |
| C | [Adventure atlas](map-styles/C/board-3x3.jpg) | Saturated, painterly relief with detailed modeled landmarks |
| D | [Night motorsport](map-styles/D/board-3x3.jpg) | Practical start lights, floodlit quarry and blue snow |
| E | [Geological cutaway](map-styles/E/board-3x3.jpg) | Continuous terrain slab with dramatic visible rock strata |

View order: 01 northwest overview; 02 north; 03 northeast; 04 east; 05 southeast; 06 south; 07 southwest; 08 west; 09 overhead. Each numbered full-resolution JPEG sits beside its board.

## Clickable level-start object study

[Nine one-view concepts](level-starts/board-3x3.jpg) use one coastal road setting and the same camera height. Each full-resolution JPEG is in `level-starts/`.

| Number | Idea | Intended interaction cue |
|---|---|---|
| 01 | Start gantry | Pass through a physical start line |
| 02 | First-jump vignette | Preview the first piece of gameplay |
| 03 | Ready bike | Mount the parked bike |
| 04 | Ignition tower | Pull a starter lever / light sequence |
| 05 | Trailhead arch | Enter the route |
| 06 | Tire-track burst | Follow an active, muddy trail |
| 07 | Mechanical checkpoint | Activate a road-facing arm |
| 08 | Topographic track totem | Read the upcoming line in carved relief |
| 09 | Rally flag tower | Ride from the flagged start point |

**User selection:** the roadside tower with flags, represented by **09**, is accepted as the level-start object direction. Its final game model must stay legible and clickable at phone map scale, with focus/lock/progress states; this concept image is a visual reference, not a production asset.
