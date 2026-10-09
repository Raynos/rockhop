"""Refresh ordering and fail-closed witnesses; no mock is a Blender pass."""
import unittest
from types import SimpleNamespace as NS
import gameplay_conditioned05 as adapter


class Rig(dict):
    def __init__(self):
        super().__init__(live=1.)
        self.events = []
        self.tagged = False
        self.pose = NS(bones={})
    def update_tag(self):
        self.events.append('tag')
        self.tagged = True
    def evaluated_get(self, graph):
        self.events.append('evaluated')
        return self


def fixture(refresh=True, muted=False):
    rig = Rig()
    limbs = []
    for kind in ('arm', 'leg'):
        for side in ('L', 'R'):
            name = kind+side
            limbs.append({'kind': kind, 'side': side, 'mechanismLower': name, 'targetControl': name+'Target'})
            rig.pose.bones[name] = NS(constraints=[NS(type='IK', influence=1., mute=muted)])
            rig.pose.bones[name+'Target'] = {'ik': 1.}
    context = {'limbs': limbs, 'ikProperty': 'ik', 'liveProperty': 'live'}
    def update():
        rig.events.append('update')
        if refresh and rig.tagged:
            for limb in limbs:
                rig.pose.bones[limb['mechanismLower']].constraints[0].influence = rig.pose.bones[limb['targetControl']]['ik']
        rig.tagged = False
    def original(rig, context, modes):
        rig.events.append('set')
        for limb in context['limbs']:
            rig.pose.bones[limb['targetControl']]['ik'] = modes[limb['kind']+limb['side']]
    bpy = NS(context=NS(view_layer=NS(update=update), evaluated_depsgraph_get=lambda: object(), scene=NS(frame_current=51)))
    return original, bpy, rig, context


class RefreshFixtures(unittest.TestCase):
    def test_tag_precedes_update_and_witness_preserves_stale_before_value(self):
        args = fixture()
        emitted = []
        adapter.refresh_modes(*args, dict.fromkeys(('armL', 'armR', 'legL', 'legR'), 0), emitted.append)
        self.assertEqual(args[2].events, ['set', 'tag', 'update', 'evaluated'])
        self.assertEqual(emitted[0]['frame'], 51)
        self.assertTrue(all(row['sourceInfluenceBeforeTag'] == 1. and row['evaluatedInfluenceAfterTag'] == 0.
                            for row in emitted[0]['limbs']))

    def test_each_limb_and_return_to_ik_are_verified(self):
        args = fixture()
        emitted = []
        for modes in ({'armL': 0, 'armR': 1, 'legL': 1, 'legR': 0},
                      dict.fromkeys(('armL', 'armR', 'legL', 'legR'), 1)):
            adapter.refresh_modes(*args, modes, emitted.append)
            self.assertEqual({row['limb']: row['evaluatedInfluenceAfterTag'] for row in emitted[-1]['limbs']}, modes)

    def test_failed_driver_refresh_emits_actual_witness_then_rejects(self):
        emitted = []
        with self.assertRaises(AssertionError):
            adapter.refresh_modes(*fixture(refresh=False), dict.fromkeys(('armL', 'armR', 'legL', 'legR'), 0), emitted.append)
        self.assertTrue(all(row['evaluatedInfluenceAfterTag'] == 1. for row in emitted[0]['limbs']))

    def test_muted_constraints_cannot_be_claimed_active(self):
        with self.assertRaises(AssertionError):
            adapter.refresh_modes(*fixture(muted=True), dict.fromkeys(('armL', 'armR', 'legL', 'legR'), 1), lambda row: None)


if __name__ == '__main__':
    unittest.main()
