"""Static low-frequency cloth-shell preparation; not an integration helper.

No bpy, native mutation, render, model inference or executable buildWardrobe entry.
Parent actual baseline verdict must precede authoring the single next candidate.
Input positions and skeleton/body FOUR fields use the existing native Z-up frame.
"""

import math


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def central_section(positions, polygons, z):
    """Return the closed central anatomical loop; never collect arm extents.

    Source mesh edge identities define the section graph. The central trunk loop
    crosses the skeleton midline; disconnected hands/arms are separate graphs.
    Exceptional plane/vertex coincidence is rejected rather than guessed.
    """
    intersections, graph = {}, {}
    for polygon in polygons:
        crossed = []
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            p, q = positions[a], positions[b]
            if (p[2] - z) * (q[2] - z) < 0:
                edge = tuple(sorted((a, b)))
                if edge not in intersections:
                    t = (z - p[2]) / (q[2] - p[2])
                    intersections[edge] = tuple(p[d] + t * (q[d] - p[d]) for d in range(3))
                crossed.append(edge)
        if crossed:
            assert len(crossed) == 2, ("Ambiguous section polygon", z, crossed)
            a, b = crossed
            graph.setdefault(a, set()).add(b)
            graph.setdefault(b, set()).add(a)
    assert graph and all(len(row) == 2 for row in graph.values()), z
    remaining = set(graph)
    central = []
    while remaining:
        component = {min(remaining)}
        frontier = list(component)
        while frontier:
            for neighbor in graph[frontier.pop()]:
                if neighbor not in component:
                    component.add(neighbor)
                    frontier.append(neighbor)
        remaining -= component
        points = [intersections[e] for e in sorted(component)]
        if min(p[0] for p in points) < 0 < max(p[0] for p in points):
            central.append(points)
    assert len(central) == 1, ("Unique central trunk loop required", z, len(central))
    return central[0]


def enclosing_profile(section, ease_metres=.025):
    """One convex oval envelope, with exact declared cross-section containment.

    This deliberately fills anatomical concavities. It is an initial shape
    proposal; only a later native shell/skin clearance evaluation can qualify it.
    """
    xmin, xmax = min(p[0] for p in section), max(p[0] for p in section)
    ymin, ymax = min(p[1] for p in section), max(p[1] for p in section)
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    rx, ry = (xmax - xmin) / 2 + ease_metres, (ymax - ymin) / 2 + ease_metres
    rho = max(((p[0] - cx) / rx) ** 2 + ((p[1] - cy) / ry) ** 2 for p in section)
    # Keep the declaration true for irregular source sections; no inward relax.
    expansion = max(1.0, math.sqrt(rho))
    rx, ry = rx * expansion, ry * expansion
    return {"z": section[0][2], "cx": cx, "cy": cy, "rx": rx, "ry": ry,
            "sourceSectionPointCount": len(section), "easeMetres": ease_metres,
            "maxSourceSquaredEllipseRadius": max(
                ((p[0] - cx) / rx) ** 2 + ((p[1] - cy) / ry) ** 2 for p in section)}


def torso_field_strength(four_row):
    """Native bone roles protect axilla/biceps; no blind abs-X torso mask.

    Shoulder influence remains legitimate on the torso. Actual rig04 pectorals
    contain it, so a 95%-spine test wrongly removes almost the whole chest.
    Limb-dominated charts get zero displacement; transition is continuous.
    """
    trunk = sum(w for name, w in four_row
                if name.startswith("DEF-spine") or name.startswith("DEF-pelvis."))
    arm = sum(w for name, w in four_row
              if any(name.startswith(stem) for stem in
                     ("DEF-upper_arm.", "DEF-forearm.", "DEF-hand.",
                      "DEF-palm.", "DEF-thumb.", "DEF-f_")))
    return smoothstep((trunk - .40) / .25) * smoothstep((.25 - arm) / .15)


PROPOSAL = {
    "readyForIntegration": False,
    "bodyAndSkeletonMutations": False,
    "candidateCount": 1,
    "source": "current official CC0 body and native04 actual FOUR field",
    "torsoSelection": "central anatomical section graph plus native trunk/limb roles",
    "preserve": "existing source chart, skin fields, collar/hem/cuff/armhole boundaries",
    "plannedGeometry": "smooth vertically lofted enclosing oval torso; broad shallow hem drape",
    "plannedDetail": "pocket reprojected onto cloth shell; proper side/pocket seam relief",
    "admission": "parent actual03/04 baseline verdict before completing helper04",
    "limits": "Static profile containment is neither clearance nor moving acceptance."
}
