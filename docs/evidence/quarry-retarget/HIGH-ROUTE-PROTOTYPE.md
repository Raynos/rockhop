# D3 upper route prototype — held out of production

The shipping D3 course retains the six narrowed rope-bridge gaps. The optional elevated Diamond route was tested and then removed from `quarry.ts`: it gave no measured advantage to the Pro bike. This file preserves the reproducible geometry and input evidence for a later design round.

## Prototype geometry

Append these to the completed D3 track only in a temporary test copy:

```ts
track.obstacles.push({ kind: 'plank', pos: { x: 385.7, y: 1.5 }, params: { length: 5, height: 0.2, angleDeg: 15, oneWay: true, surface: 'wood', prop: 'rope-bridge' } });
const platformObstacleIndex = track.obstacles.length;
track.obstacles.push({ kind: 'open-platform', pos: { x: 396, y: 0 }, params: { length: 18, height: 3.0, thickness: 0.18, surface: 'wood' } });
track.diamondGoal = { id: 'd3-high-bridge', platformObstacleIndex, x: 404, minRearY: 3.2 };
```

The lower road remains passable beneath the platform. The goal records the rear wheel grounded on the upper deck near y=3.34; lower passage records a rear wheel near y=0.4 with no proof. `harness/quarry-high-search.mts` tests 1,800 three-window control combinations per bike from the same clean x=380 approach snapshot. `harness/quarry-high-record.mts` records exact full-course replays for the selected plans. Four recordings and reports are `d3-{rookie,pro}-{upper,lower}.json` and companion `-report.json` files in this directory. Every saved result finished with 0 faults and a byte-identical replay hash.

| Bike | Route | Time | Proof | Medal | Hash |
| --- | --- | ---: | --- | --- | --- |
| Rookie | upper | 35.325 s | yes | Platinum | `a6bbaedd4f1cae71` |
| Rookie | lower | 35.242 s | no | Gold | `2e4a3cea9b126987` |
| Pro | upper | 32.825 s | yes | Platinum | `912e3b4c81f610b3` |
| Pro | lower | 34.050 s | no | Gold | `71a16f51af875569` |

The sweep found 90 Rookie proof crossings and 60 Pro proof crossings; 96 Rookie and 46 Pro candidates finished. Pro was faster on the matched successful input, but its Diamond time target uses a stricter bike scale. This geometry did not establish a meaningful Pro-only or Pro-favored challenge. It is intentionally excluded from the shipping track. The next D3 route attempt must demonstrate a Pro advantage through level geometry and broad input search, without a bike-ID gate.
