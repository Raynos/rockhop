"""Declarative topology scaffold. Deliberately cannot instantiate a mesh yet.

Physical vertices are keyed by semantic seam IDs and rational edge split
parameters; coordinate rounding/proximity never establishes ownership.
"""
from fractions import Fraction

class SharedEdgeRegistry:
    def __init__(self):
        self.positions = {}
        self.edge_nodes = {}
        self.quads = []
        self.transitions = []

    def declare_node(self, key, position):
        position = tuple(float(v) for v in position)
        if key in self.positions and self.positions[key] != position:
            raise ValueError('Conflicting authored position for shared node')
        self.positions[key] = position
        return key

    def declare_edge(self, edge_id, first, last, subdivisions):
        if subdivisions < 1:
            raise ValueError('Nonpositive edge subdivision count')
        self.edge_nodes[edge_id] = tuple(
            (edge_id, Fraction(k, subdivisions))
            for k in range(subdivisions + 1)
        )
        # Actual source/world positions are intentionally absent until contract.
        return self.edge_nodes[edge_id]

    def declare_quad(self, nodes):
        if len(nodes) != 4 or len(set(nodes)) != 4:
            raise ValueError('Quad must have four distinct physical node IDs')
        self.quads.append(tuple(nodes))

    def declare_triangle_transition(self, nodes, reason):
        if len(nodes) != 3 or len(set(nodes)) != 3:
            raise ValueError('Transition triangle requires three distinct IDs')
        if not reason:
            raise ValueError('Boundary parity transition needs explicit reason')
        self.transitions.append((tuple(nodes), reason))


def require_frozen_contract(contract):
    required = (
        'sourceSHA256', 'coordinateAdapter', 'sourceProfileSections',
        'orderedCuffCycles', 'hoodBodyBoundary', 'lowerBoundaryContract',
        'retainedDonorTriangleMasks', 'parentGeometryGo',
    )
    missing = [k for k in required if k not in contract]
    if missing:
        raise RuntimeError('Construction blocked: missing ' + ', '.join(missing))
    if not contract['parentGeometryGo']:
        raise RuntimeError('Construction awaits parent machine checkpoint')
    if contract['sourceSHA256'] != '186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e':
        raise RuntimeError('Unexpected donor source')
    return contract


# No bpy import, vertex sampling, mesh instantiation or output export here.
# Boundary parity, non-simple collar, source hem and physical donor attachment
# choices remain explicit contract inputs, never automatic geometry defaults.
