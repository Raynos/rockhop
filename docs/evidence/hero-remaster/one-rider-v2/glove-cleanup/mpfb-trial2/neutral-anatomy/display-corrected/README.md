# Superseded diagnostic neutral display

This display-only correction removed inherited untransformed shape keys from
the initial blank crops. It correctly retained canonical vertex coordinates
and native weights, but the frozen input NPZ serialized only tri/quads and
omitted two wrist-cut n-gons per hand: 1,654 polygons rather than 1,656.
Consequently this master has extra wrist boundaries and must not be used as
a complete anatomical cage. Its images and report are preserved as evidence
of that serialization defect.

[Complete export and display](../display-complete/README.md) recover every
polygon from the unchanged original neutral master, without altering anatomy,
posing or weights. Use those complete views for parent model judgment.
