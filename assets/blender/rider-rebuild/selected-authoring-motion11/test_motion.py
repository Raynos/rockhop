"""Check foot stance and jump physics before any native construction."""
import math
import json
from pathlib import Path
import unittest
from motion import SCORES, foot_cycle, score


class MovementScore(unittest.TestCase):
    def test_source_leg_lengths_reach_all_travelling_targets(self):
        root=Path(__file__).resolve().parents[4]
        contract=json.loads((root/'harness/out/rider-rebuild/selected-complete-engine01/engine05/rider-contract.json').read_text())
        heads={b['name']:b['head'] for b in contract['nativeRest']['bones']}
        add=lambda a,b:[x+y for x,y in zip(a,b)]
        sub=lambda a,b:[x-y for x,y in zip(a,b)]
        def rotate(p,degrees,axis):
            c,s=math.cos(math.radians(degrees)),math.sin(math.radians(degrees)); x,y,z=p
            return [c*x-s*y,s*x+c*y,z] if axis=='z' else [x,c*y-s*z,s*y+c*z]
        pelvis=heads['DEF-spine']
        for name,spec in SCORES.items():
            if name=='RiderRangeOfMotion': continue
            for i in range(1001):
                r=score(name,spec['seconds']*i/1000)
                for side in ('L','R'):
                    f=r['feet'][side]; source_sole=heads['SoleSocket.'+side]; source_foot=heads['DEF-foot.'+side]; p=source_sole[:]
                    if 'turnFrom' in f:
                        pivot=[pelvis[0],pelvis[1],0.]
                        a=add(rotate(sub(p,pivot),f['turnFrom'],'z'),pivot); b=add(rotate(sub(p,pivot),f['turnTo'],'z'),pivot)
                        p=[x+(y-x)*f['turnBlend'] for x,y in zip(a,b)]
                    ankle=add(add(p,[0.,-f['forward'],f['up']]),rotate(sub(source_foot,source_sole),f.get('yaw',0.),'z'))
                    hip=add(add(pelvis,r['root']),rotate(rotate(sub(heads['DEF-thigh.'+side],pelvis),r['pitch'],'x'),r['yaw'],'z'))
                    a=math.dist(heads['DEF-thigh.'+side],heads['DEF-shin.'+side]);b=math.dist(heads['DEF-shin.'+side],source_foot)
                    distance=math.dist(hip,ankle)
                    self.assertLess(distance,a+b-.0001,(name,i,side,distance,a+b))
                    self.assertGreater(distance,abs(a-b)+.0001)

    def test_travelling_stance_has_no_ground_slide(self):
        for name, duty in [('RiderWalk', .62), ('RiderJog', .40)]:
            duration = SCORES[name]['seconds']; stride = SCORES[name]['rootForwardM']
            for offset in (0., .5):
                plants = {}
                for i in range(1001):
                    r = foot_cycle(duration*i/1000, duration, stride, duty, offset, .1)
                    self.assertGreaterEqual(r['up'], 0.)
                    if r['planted']:
                        self.assertEqual(r['up'], 0.)
                        self.assertAlmostEqual(plants.setdefault(r['plant'], r['forward']), r['forward'])

    def test_cycle_seam_has_declared_root_delta(self):
        for name in ('RiderWalk', 'RiderJog'):
            row = SCORES[name]; a, b = score(name, 0.), score(name, row['seconds'])
            self.assertAlmostEqual(b['root'][1]-a['root'][1], -row['rootForwardM'])
            for side in ('L', 'R'):
                self.assertAlmostEqual(b['feet'][side]['forward']-a['feet'][side]['forward'], row['rootForwardM'])
                self.assertAlmostEqual(b['feet'][side]['up'], a['feet'][side]['up'])

    def test_jump_airborne_arc_and_ground_contacts(self):
        h = .00001
        for t, v in [(.85, 9.81*.25), (1.35, -9.81*.25)]:
            velocity = (score('RiderJumpLand', t+h)['root'][2]-score('RiderJumpLand', t-h)['root'][2])/(2*h)
            self.assertAlmostEqual(velocity, v, places=3)
        self.assertAlmostEqual(score('RiderJumpLand', 1.1)['root'][2], 9.81*.5**2/8)
        for i in range(251):
            t=i/100; r=score('RiderJumpLand', t)
            if t < .85 or t >= 1.35:
                self.assertTrue(all(p['planted'] and p['up']==0 for p in r['feet'].values()))
        self.assertEqual(score('RiderJumpLand', 2.5)['root'], [0., -0., -0.])

    def test_turn_changes_foot_orientation_only_during_lift(self):
        for i in range(1, 300):
            r = score('RiderTurn90', i/100)
            for foot in r['feet'].values():
                if foot['turnFrom'] != foot['turnTo'] and i%100:
                    self.assertGreater(foot['up'], 0.)
        end = score('RiderTurn90', 3.)
        self.assertEqual(end['yaw'], 90.)
        self.assertTrue(all(f['yaw']==90. and f['up']<1e-20 for f in end['feet'].values()))


if __name__ == '__main__': unittest.main()
