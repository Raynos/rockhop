"""The existing native-quad fixture plus actual saved full-support evidence."""
import hashlib
import json
from pathlib import Path
import unittest

from support_brush02 import coalesce, finish, smooth_rows
from weight_brush import smooth_rows as original_brush

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


class AnatomicalSupportFixture(unittest.TestCase):
    def test_same_actual_quad_brush_commutes_with_equivalent_supports(self):
        fixture = json.loads((HERE/'witness-fixture.json').read_text())
        names = {'DEF-thighL': 'DEF-thigh.L', 'DEF-pelvisL': 'DEF-pelvis.L',
                 'DEF-pelvisR': 'DEF-pelvis.R', 'DEF-spine': 'DEF-spine'}
        rows = [{names[c['joint']]: c['weight'] for c in v['components']} for v in fixture['rows']]
        graph = [{1, 3}, {0, 2}, {1, 3}, {0, 2}]
        expected, _, _ = original_brush(rows, graph, {2: 1., 3: 1.}, .5, 8)
        full, final, _ = smooth_rows(rows, graph, {2: 1., 3: 1.}, .5, 8)
        self.assertEqual(full[:2], rows[:2]); self.assertEqual(final[:2], rows[:2])
        for i in (2, 3):
            for name, weight in coalesce(expected[i]).items(): self.assertAlmostEqual(full[i][name], weight, places=14)
            self.assertAlmostEqual(sum(final[i].values()), 1.)

    def test_actual_saved_field_requires_no_rank_pruning_after_named_coalescing(self):
        filename = ROOT/'harness/out/rider-rebuild/selected-seated-anatomical09/authored01/authored-weight-rows.json'
        self.assertEqual(hashlib.sha256(filename.read_bytes()).hexdigest(), '3af8d3ddd719f47a7f2e5073a5ab0dda00aa9ce2a25fa471c00b9718093bf4bf')
        rows = json.loads(filename.read_text()); self.assertEqual(len(rows), 2356)
        maxima = 0.; supports = set()
        for row in rows:
            full = coalesce(row['fullAuthored']); self.assertLessEqual(len(full), 4)
            final, removed = finish(full, .0001); maxima = max(maxima, removed); supports.update(full)
            if row['nativeID'] in (8565, 8566, 8396):
                self.assertEqual(set(final), {'DEF-spine', 'DEF-thigh.L', 'DEF-thigh.R'})
        self.assertIn('DEF-spine.001', supports); self.assertIn('DEF-shin.L', supports); self.assertIn('DEF-shin.R', supports)
        self.assertLess(maxima, .0002)
        print(json.dumps({'actualRows': len(rows), 'maximumCutoffOnlyRemovedMass': maxima, 'rankRemovedMass': 0}))


if __name__ == '__main__': unittest.main()
