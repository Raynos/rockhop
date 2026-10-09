"""Serializer and exact real-baseline tests; no derivative or upload claim."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('focused_compile', Path(__file__).with_name('compile.py'))
compiler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compiler)


class CompileTests(unittest.TestCase):
    def setUp(self):
        self.raw, self.runtime, self.manifest = compiler.read_bases()
        self.upload = {'sha256': 'a' * 64, 'bytes': 75000000,
            'pathname': 'rider-remaster/' + 'a' * 64 + '/rider.glb',
            'url': self.manifest['url'].split('/rider-remaster/')[0] + '/rider-remaster/' + 'a' * 64 + '/rider.glb',
            'contentType': 'model/gltf-binary'}
        self.parity = {'candidate': {'sha256': 'a' * 64, 'bytes': 75000000},
            'sourcePatch': {'report': {'path': 'unit-fixture-report'}, 'patch': {'path': 'unit-fixture-patch'}},
            'changedAccessors': [{'mesh': 5, 'semantic': 'POSITION', 'accessor': 49}]}
        self.facts = {'pass': True, 'sourceSHA256': 'a' * 64, 'actualDecodedAccessorHashesChecked': True,
            'actualOriginalBINPrefixChecked': True, 'actualImagePayloadHashesChecked': True}
        self.template = (compiler.ROOT / 'src/render/hero/selectedAsset.ts').read_text()

    def assemble(self):
        return compiler.assemble(self.raw, self.runtime, self.manifest, self.upload, self.parity,
            compiler.encoded(self.parity), self.facts, self.template)

    def test_deterministic_packet_preserves_native_rest_and_actual_controls(self):
        first = self.assemble(); self.assertEqual(first, self.assemble())
        runtime = json.loads(first['rider-remaster-contract.json'])
        raw = json.loads(first['rider-contract.json'])
        self.assertEqual(runtime['nativeRest'], self.runtime['nativeRest'])
        self.assertEqual(runtime['specification'], self.runtime['specification'])
        for key in self.raw['driver']:
            if key != 'selectedGripProfile': self.assertEqual(raw['driver'][key], self.raw['driver'][key])
        self.assertEqual(runtime['metadataSHA256'], compiler.sha(first['rider-contract.json']))
        self.assertEqual(raw['driver']['selectedGripProfile']['authoringSourceSHA256'], compiler.AUTHORING)
        self.assertEqual(raw['driver']['selectedGripProfile']['authoringContractSHA256'], compiler.AUTHORING_CONTRACT)
        self.assertEqual(raw['driver']['selectedGripProfile']['baselineApplicationSourceSHA256'], compiler.BASELINE)
        self.assertEqual(raw['driver']['selectedGripProfile']['appliesToSourceSHA256'], self.upload['sha256'])
        self.assertEqual(self.runtime['sourceSHA256'], compiler.BASELINE)

    def test_reject_mismatched_candidate_hash(self):
        self.upload['sha256'] = 'b' * 64
        with self.assertRaises(AssertionError): self.assemble()

    def test_reject_mutable_or_wrong_upload_path(self):
        self.upload['url'] += '?mutable=1'
        with self.assertRaises(AssertionError): self.assemble()

    def test_reject_unverified_decoded_proof(self):
        self.facts['actualDecodedAccessorHashesChecked'] = False
        with self.assertRaises(AssertionError): self.assemble()


if __name__ == '__main__':
    unittest.main()
