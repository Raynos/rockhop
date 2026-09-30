# Quarry machinery source candidate

Eight immutable packed full/LOD GLBs and their SHA manifest are saved in
`assets/blender/course-kits/quarry-standard/delivery/`. The corrected join
transforms keep the gantry at ground level; the runtime leaf plans distinct
D1–D3 machine placement and derives D1 bedding from its four actual ledges.

Production does not import this kit. The model family is not in public models.
The [source audit](source-audit.json) and [decoder report](decoder-report.json)
pass again during cleanup; every checked output matches its tracked delivery
bytes and manifest SHA. Geometry uses the production Three/Meshopt decoder;
Node strips image references, so texture metadata is checked separately.
Full family: 709,732 B / 24,884 triangles / 22 draws. Low family: 406,228 B /
6,712 triangles / 22 draws. Each course loads only its planned subset.

No played visual, GPU, bitmap decode or physical-phone acceptance. Legacy
retirement and terrain composition need full moving parent review before
integration. These source and decoded-geometry checks earn no course credit.
