"""Regression checks for stereo cancellation and offline runtime envelopes."""
import unittest

import numpy as np

from analyze import SR, seam_metrics
from remaster_mix import envelope
from remaster_master import stereo_silence


class RemasterChecks(unittest.TestCase):
    def test_antiphase_music_is_audible_in_stereo(self):
        tone = .1*np.cos(2*np.pi*440*np.arange(SR)/SR)
        self.assertEqual(stereo_silence(np.column_stack([tone, -tone])), 0)

    def test_opposite_stereo_jumps_cannot_cancel_the_seam_gate(self):
        t = np.arange(SR)/SR
        common = .001*np.cos(2*np.pi*440*t)
        ramp = np.linspace(-.3, .3, SR)
        body = np.column_stack([common+ramp, common-ramp])
        report = seam_metrics(body, body[:SR//10])
        self.assertGreater(report['seam_click'], 100)

    def test_continuous_stereo_period_has_small_boundary(self):
        t = np.arange(SR)/SR
        body = np.column_stack([.1*np.cos(2*np.pi*440*t), .07*np.cos(2*np.pi*660*t)])
        report = seam_metrics(body, body[:SR//10])
        self.assertLess(report['seam_click'], .1)
        self.assertEqual(report['seam_step_db'], 0)
        self.assertLess(report['seam_err_db'], -100)

    def test_music_duck_ignores_sub_half_db_changes(self):
        events = {'envelope': [{'time': 0, 'duck': .3}, {'time': .05, 'duck': .45}]}
        out = envelope(events, 'duck', SR//10, 1, .4, decibels=True, music=True)
        np.testing.assert_array_equal(out, np.ones(SR//10))

    def test_ambient_starts_silent_and_reaches_time_constant(self):
        out = envelope({'envelope': [{'time': 0, 'gain': 1}]}, 'gain', SR//2, 0, .2)
        self.assertEqual(out[0], 0)
        self.assertAlmostEqual(out[round(.2*SR)], 1-np.exp(-1))


if __name__ == '__main__':
    unittest.main()
