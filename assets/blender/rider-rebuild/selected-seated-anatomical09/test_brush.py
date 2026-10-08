"""One actual native-quad mechanism fixture; no Blender or mesh mutation."""
import json
import math
from pathlib import Path
import unittest
from weight_brush import smooth_rows


class NativeBrushFixture(unittest.TestCase):
    def test_actual_quad_gradient_and_common_average_compression(self):
        fixture = json.loads((Path(__file__).parent/'witness-fixture.json').read_text())
        self.assertEqual(fixture['quad'], [17070, 17071, 8575, 8574])
        rows = [{c['joint']: c['weight'] for c in v['components']} for v in fixture['rows']]
        graph = [{1, 3}, {0, 2}, {1, 3}, {0, 2}]
        full, final, removed = smooth_rows(rows, graph, {2: 1., 3: 1.}, .5, 2)
        self.assertEqual(final[:2], rows[:2])
        gradient = lambda r: r[3]['DEF-thighL']-r[2]['DEF-thighL']
        self.assertTrue(0 < gradient(final) < gradient(rows))
        def length(weights):
            points = []
            for i in (2, 3):
                components = {c['joint']: c['pointBike'] for c in fixture['rows'][i]['components']}
                points.append([sum(weights[i].get(k, 0)*p[a] for k, p in components.items()) for a in range(3)])
            return math.dist(*points)
        common = {k: (rows[2].get(k, 0)+rows[3].get(k, 0))/2 for k in rows[2].keys()|rows[3].keys()}
        rest = math.dist(*(fixture['rows'][i]['sourceXYZ'] for i in (2, 3)))
        self.assertAlmostEqual(rest, .018591, places=6)
        self.assertAlmostEqual(length(rows), .062235, places=6)
        self.assertAlmostEqual(length([{}, {}, common, common]), .014512, places=6)
        self.assertTrue(rest < length(final) < length(rows))
        self.assertEqual(set(removed), {2, 3})
        for i in (2, 3):
            self.assertAlmostEqual(sum(final[i].values()), 1.)
            self.assertLessEqual(len(final[i]), 4)
            self.assertAlmostEqual(sum(full[i].values()), 1.)


if __name__ == '__main__': unittest.main()
