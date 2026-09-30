"""Pure selection/layout regression tests; no model, sound playback or network."""
import unittest
import tempfile
import contextlib
import io
import os
from unittest.mock import patch
from pathlib import Path
import numpy as np
from sfx_build import append_atlas, selected_window, loop_metrics, qualifies, encode, NEGATIVES
from sfx_generate import pending_takes, memory_gate

class SfxBuildTests(unittest.TestCase):
    def test_selected_nonzero_bed_window_is_mastered(self):
        x = np.arange(20000, dtype=np.float32)[:,None]
        y = selected_window(x, 5, 1000, 'bed')
        self.assertEqual(len(y), 10000)
        self.assertEqual(float(y[0,0]), 5000)
        self.assertEqual(float(y[-1,0]), 14999)
        y[0,0] = -1
        self.assertEqual(float(x[5000,0]), 5000)
    def test_atlas_variants_offsets_and_durations_are_deterministic(self):
        def build():
            atlas=[];cursor=0;clips=[]
            for frames in [1200,700,1800]:
                cursor,clip=append_atlas(atlas,cursor,np.ones((frames,1),np.float32),1000,.4)
                clips.append(clip)
            return clips,np.concatenate(atlas),cursor
        first=build();second=build()
        self.assertEqual(first[0],second[0]);self.assertTrue(np.array_equal(first[1],second[1]))
        self.assertEqual([c['start'] for c in first[0]],[0,1.35,2.2])
        self.assertEqual([c['duration'] for c in first[0]],[1.2,.7,1.8])
        self.assertEqual(first[2],4150)
    def test_semantic_thresholds_and_negative_winners_reject(self):
        row={'rank':2,'match':'a coast','best_bed':'coast'}
        self.assertTrue(qualifies(row,'coast','bed'))
        self.assertFalse(qualifies(row,'alpine','bed'))
        self.assertFalse(qualifies({**row,'rank':3},'coast','bed'))
        self.assertTrue(qualifies({**row,'rank':3},'crowdRoar','oneshot'))
        self.assertFalse(qualifies({**row,'rank':4},'crowdRoar','oneshot'))
        self.assertFalse(qualifies({**row,'rank':3},'grunt','oneshot'))
        for negative in NEGATIVES:
            self.assertFalse(qualifies({**row,'rank':1,'match':negative},'grunt','oneshot'))
    def test_wrap_proxies_detect_discontinuity_and_energy_jump(self):
        x=np.sin(np.arange(1000)*2*np.pi/50).astype(np.float32)
        self.assertTrue(loop_metrics(x,0,1,1000)['seam_proxy_pass'])
        x[-1]=10
        self.assertFalse(loop_metrics(x,0,1,1000)['seam_proxy_pass'])
        x=np.r_[np.ones(500)*.01,np.ones(500)*.5].astype(np.float32)
        self.assertGreater(loop_metrics(x,0,1,1000)['wrap_energy_step_db_50ms'],30)
    def test_seed_first_model_batches_resume_and_require_provenance(self):
        families = {str(i):{} for i in range(9)}
        with tempfile.TemporaryDirectory() as scratch:
            out=Path(scratch)
            first=pending_takes(families,[1,2],out,list(families),9)
            self.assertEqual(len(first),9)
            self.assertTrue(all(seed==1 for _,seed,_ in first))
            for _,_,dest in first:
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_text('fixture');dest.with_suffix('.json').write_text('{}')
            second=pending_takes(families,[1,2],out,list(families),9)
            self.assertEqual(len(second),9)
            self.assertTrue(all(seed==2 for _,seed,_ in second))
            first[0][2].with_suffix('.json').unlink()
            self.assertEqual(pending_takes(families,[1,2],out,list(families),1)[0][1],1)
            first[0][2].with_suffix('.json').write_text('{}')
            for _,_,dest in second:
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_text('fixture');dest.with_suffix('.json').write_text('{}')
            forced=pending_takes(families,[1,2],out,list(families),9,{('0',1),('0',2),('1',1)})
            self.assertEqual([(family,seed) for family,seed,_ in forced],[('0',1),('1',1),('0',2)])
    def test_mp3_channel_bitrates_hash_lag_bounds_and_peak(self):
        sr=48000
        x=(.1*np.sin(np.arange(sr)*2*np.pi*440/sr)).astype(np.float32)[:,None]
        with tempfile.TemporaryDirectory() as scratch:
            root=Path(scratch)
            for mono in [True,False]:
                name,metrics,decoded=encode(x.copy(),sr,root/('voice.mp3' if mono else 'bed.mp3'),root,mono=mono)
                self.assertRegex(name,r'^[a-z]+-[0-9a-f]{12}\.mp3$')
                self.assertEqual(metrics['channels'],1 if mono else 2)
                self.assertEqual(metrics['bitrate'],'96k' if mono else '128k')
                self.assertLessEqual(metrics['truepeak_dbfs'],-1)
                self.assertEqual(metrics['decoded_clipped_samples'],0)
                self.assertAlmostEqual(metrics['decoded_duration_s'],1,places=4)
                self.assertLess(abs(metrics['decode_lag_s']),.001)
                self.assertEqual(len(decoded),sr)
                self.assertTrue((root/name).is_file())
    def test_dual_mono_atlas_keeps_amplitude_after_runtime_average(self):
        sr = 48000
        mono = (.1*np.sin(np.arange(sr)*2*np.pi*440/sr)).astype(np.float32)[:,None]
        stereo = np.repeat(mono, 2, axis=1)
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            _, _, baseline = encode(mono, sr, root/'original.mp3', root, mono=True)
            _, metrics, averaged = encode(stereo, sr, root/'reactions.mp3', root)
            ratio = np.sqrt(np.mean(averaged**2)/np.mean(baseline**2))
            self.assertLess(abs(20*np.log10(ratio)), .1)
            self.assertEqual(metrics['channels'], 2)
            self.assertEqual(metrics['bitrate'], '128k')
            self.assertLess(abs(metrics['decode_lag_s']), .001)

    def test_memory_gate_uses_projected_anonymous_pressure_and_other_processes(self):
        def gate(anonymous,pressure,reserve,top=''):
            with patch('sfx_generate.subprocess.check_output',side_effect=[f'{anonymous} 12 20',str(pressure),top]), contextlib.redirect_stdout(io.StringIO()):
                return memory_gate(reserve)
        self.assertEqual(gate(46,1,22)['reserve_gib'],22)
        self.assertEqual(gate(60,1,0,f'{os.getpid()} Python 22G\n')['other_over_15gb'],[])
        for anonymous,pressure,reserve,top in [(48,1,22,''),(46,2,22,''),(46,1,22,'999999 Other Model 16G\n')]:
            with self.assertRaises(SystemExit) as raised:
                gate(anonymous,pressure,reserve,top)
            self.assertEqual(raised.exception.code,75)

if __name__=='__main__':
    unittest.main()
