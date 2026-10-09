"""Small source fixtures only; none substitutes for parent native execution."""
import math
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import conditioned_policy04 as policy
import gameplay_conditioned04 as builder
import native_playback04 as playback


class ConditioningFixtures(unittest.TestCase):
    def test_stable_keys_keep_ik(self):
        result = policy.conditioned_modes([0., .00009], [0., .00002], [0., .00009])
        self.assertEqual(result['modes'], [1, 1])
        self.assertEqual(result['switchFrames'], [])

    def test_failed_key_enters_fk_at_prior_agreeing_key(self):
        result = policy.conditioned_modes([0., 0., .0012, 0., 0.], [0.]*5, [0., .00003, .0012, .00003, 0.])
        self.assertEqual(result['modes'], [1, 0, 0, 1, 1])
        self.assertEqual(result['switchFrames'], [2, 4])

    def test_disagreeing_neighbors_expand_and_merge_intervals(self):
        result = policy.conditioned_modes([0., .001, 0., 0., .001, 0.], [0.]*6,
                                         [0., .001, .00011, .00011, .001, 0.])
        self.assertEqual(result['modes'], [0, 0, 0, 0, 0, 1])
        self.assertEqual(result['switchFrames'], [6])

    def test_endpoint_failures_require_no_invented_transition(self):
        result = policy.conditioned_modes([.001]*3, [.00002]*3, [.001]*3)
        self.assertEqual(result['modes'], [0, 0, 0])
        self.assertEqual(result['switchFrames'], [])
        self.assertIsNone(result['intervals'][0]['ikReturnFrame'])

    def test_invalid_or_failing_fk_is_rejected(self):
        for ik, fk, difference in [([0.], [.0001], [0.]), ([math.nan], [0.], [0.]),
                                    ([0.], [0.], [-1.]), ([0.], [], [0.])]:
            with self.assertRaises(AssertionError):
                policy.conditioned_modes(ik, fk, difference)

    def test_sparse_native_channels_are_preserved_and_missing_rest_filled(self):
        existing = SimpleNamespace(data_path='pose.bones["DEF-spine"].location', array_index=1)
        found = [existing]
        appended = []
        def add(_bag, path, index, value, start, end):
            appended.append((path, index, value, start, end))
            found.append(SimpleNamespace(data_path=path, array_index=index))
        with patch.object(playback, 'bag', return_value=object()), \
             patch.object(playback, 'curves', side_effect=lambda _action: iter(found)), \
             patch.object(playback, 'static_curve', side_effect=add):
            filled = playback.reset_tracks(object(), ['DEF-spine'], 1., 31., 0.)
        self.assertEqual(len(filled), 9)
        self.assertEqual(len(appended), 10)
        self.assertNotIn((existing.data_path, existing.array_index), filled)
        self.assertEqual(appended[-1], ('["M11_liveControls"]', 0, 0., 1., 31.))
        self.assertIn(('pose.bones["DEF-spine"].rotation_quaternion', 0, 1, 1., 31.), appended)
        self.assertIn(('pose.bones["DEF-spine"].scale', 2, 1, 1., 31.), appended)

    def test_streaming_pin_detects_mutation_under_python39(self):
        with tempfile.TemporaryDirectory(dir=builder.ROOT) as directory:
            path = Path(directory)/'pin.bin'
            path.write_bytes(b'a'*(1024*1024+3))
            pin = builder.pin_file(path)
            self.assertEqual(builder.pinned(pin), path)
            path.write_bytes(b'changed')
            with self.assertRaises(AssertionError):
                builder.pinned(pin)


if __name__ == '__main__':
    unittest.main()
