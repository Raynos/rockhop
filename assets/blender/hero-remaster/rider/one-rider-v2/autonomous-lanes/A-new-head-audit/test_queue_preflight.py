"""CPU-only wrapper contract tests. Model/lock/process calls are mocked."""
import unittest,importlib.util,json,io,sys,tempfile,signal
from pathlib import Path
from unittest.mock import patch,Mock
from contextlib import redirect_stdout
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('owned_queue',ROOT/'queued_model_worker.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class QueuePreflight(unittest.TestCase):
 def test_dry_run_never_locks_or_starts_worker(self):
  stdout=io.StringIO()
  with patch.object(sys,'argv',['fixture','--tag','fake','--','cpu-fixture']),patch.object(module.os,'execv') as lock,patch.object(module.subprocess,'Popen') as process,redirect_stdout(stdout):module.main()
  lock.assert_not_called();process.assert_not_called();report=json.loads(stdout.getvalue());self.assertFalse(report['eviction']);self.assertEqual(report['anonymousLimitBytes'],70e9)
 def test_actual_dispatch_is_canonical_lockf_without_eviction(self):
  with patch.object(sys,'argv',['fixture','--execute','--tag','fake','--','cpu-fixture']),patch.object(module.os,'execv',side_effect=SystemExit(0)) as execute:
   with self.assertRaises(SystemExit):module.main()
  binary,args=execute.call_args.args;self.assertEqual(binary,'/usr/bin/lockf');self.assertEqual(args[:3],['lockf','-k','/Users/raynos/projects/localai/.model.lock']);self.assertNotIn('evict.sh',' '.join(args))
 def run_fake_stop(self,memories,times):
  with tempfile.TemporaryDirectory() as directory:
   p=Mock();p.pid=45123;p.poll.return_value=None;p.wait.return_value=143
   with patch.object(module,'R',Path(directory)),patch.object(sys,'argv',['fixture','--execute','--inside-lock','--tag','fake','--','cpu-fixture']),patch.object(module.subprocess,'run',side_effect=[SimpleNamespace(stdout=f'{m} 0 0\n') for m in memories]),patch.object(module.subprocess,'Popen',return_value=p) as spawn,patch.object(module.os,'killpg') as kill,patch.object(module.time,'monotonic',side_effect=times),patch.object(module.time,'sleep'):
    with self.assertRaises(SystemExit):module.main()
   self.assertTrue(spawn.call_args.kwargs['start_new_session']);kill.assert_called_once_with(45123,signal.SIGTERM)
   return json.loads((Path(directory)/'fake-model-process.json').read_text())
 def test_memory_boundary_stops_only_owned_process_group(self):
  report=self.run_fake_stop([19.9,60.7],[0,.5,1,2]);self.assertEqual(report['stopReason'],'Anonymous memory reached preemptive 65 GB stop margin');self.assertTrue(report['noEviction']);self.assertEqual(report['preemptiveStopBytes'],65e9);self.assertEqual(report['pollIntervalSeconds'],1);self.assertEqual(report['samples'][0]['stage'],'memory-gate')
 def test_batch_timeout_covers_owned_group(self):
  report=self.run_fake_stop([19.9,19.9],[0,.5,1794,1795,1796]);self.assertEqual(report['stopReason'],'30-minute complete process-group deadline');self.assertEqual(report['timeLimitSeconds'],1800);self.assertLess(report['wallSeconds'],1800)
 def test_memory_gate_is_bounded_and_recorded_without_worker(self):
  with tempfile.TemporaryDirectory() as directory:
   with patch.object(module,'R',Path(directory)),patch.object(sys,'argv',['fixture','--execute','--inside-lock','--tag','fake','--','cpu-fixture']),patch.object(module.subprocess,'run',return_value=SimpleNamespace(stdout='61 0 0\n')),patch.object(module.subprocess,'Popen') as worker,patch.object(module.time,'monotonic',side_effect=[0,1794,1795,1796]):
    with self.assertRaises(RuntimeError):module.main()
   worker.assert_not_called();report=json.loads((Path(directory)/'fake-model-process.json').read_text());self.assertEqual(report['samples'][0]['anonymousGiB'],61);self.assertIsNone(report['exitCode'])
 def test_actual_h21_retention_precedes_every_cleanup(self):
  source=(ROOT/'hunyuan21-head-preserve.py').read_text();save=source.index("np.savez_compressed(out/'raw-shape.npz'")
  for cleanup in ['mesh=FloaterRemover()(mesh)','mesh=DegenerateFaceRemover()(mesh)','mesh=FaceReducer()(mesh']:
   self.assertLess(save,source.index(cleanup))
  self.assertIn("c.renderer_device='cpu'",source);self.assertIn("'version':'Hunyuan3D-2.1'",source);self.assertIn("hunyuan-paint-pbr.yaml",source)

if __name__=='__main__':unittest.main()
