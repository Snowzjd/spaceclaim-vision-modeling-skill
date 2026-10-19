"""P4 interface checks, not proof of desktop actions or successful repairs."""
import json
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / 'spaceclaim-vision-modeling'
IDS = ['EX-%02d' % i for i in range(1, 15)] + ['ER-%02d' % i for i in range(1, 13)]


class ExecutionGuidanceTests(unittest.TestCase):
    def test_independent_snapshots_and_delta_are_bound(self):
        folder=PKG/'assets/evaluations/p4-actions'
        initial=json.loads((folder/'results.json').read_text(encoding='utf-8'))
        delta=json.loads((folder/'delta-results.json').read_text(encoding='utf-8'))
        self.assertEqual(set(IDS), {c['catalog_id'] for c in initial['cases']})
        self.assertEqual(26,len(initial['cases']))
        self.assertEqual(hashlib.sha256((folder/'raw-inputs.json').read_bytes()).hexdigest(),initial['input_snapshot']['sha256'])
        for ident,digest in initial['guidance_snapshot']['sha256'].items():
            self.assertEqual(digest,hashlib.sha256((folder/'initial-guides'/(ident.lower()+'.json')).read_bytes()).hexdigest())
        for binding in delta['guidance_snapshot'].values():
            self.assertEqual(binding['sha256'],hashlib.sha256((ROOT/binding['path']).read_bytes()).hexdigest())
        self.assertEqual({'ER-04','ER-05','ER-08'},{c['catalog_id'] for c in delta['cases']})
        self.assertEqual(delta['base_snapshot']['original_results_sha256'],hashlib.sha256((folder/'results.json').read_bytes()).hexdigest())

    def test_emitted_selector_handles_dictionary_records_and_rejects_ambiguity(self):
        folder=PKG/'assets/evaluations/p4-actions'
        inputs=json.loads((folder/'raw-inputs.json').read_text(encoding='utf-8'))
        delta=json.loads((folder/'delta-results.json').read_text(encoding='utf-8'))
        raw=next(c for c in inputs['cases'] if c['catalog_id']=='ER-04')['raw_input']
        source=next(c for c in delta['cases'] if c['catalog_id']=='ER-04')['result']['corrected_selector']
        env=dict(candidate_attributes=raw['candidate_attributes'],target_semantics=raw['target_semantics'])
        exec(compile(source,'independent-selector','exec'),env)
        self.assertEqual('face-b',env['candidate']['candidate_id'])
        env['candidate_attributes']=[env['candidate'],env['candidate']]
        with self.assertRaises(RuntimeError):
            exec(compile(source,'independent-selector','exec'),env)

    def test_unresolved_repairs_stay_unresolved(self):
        folder=PKG/'assets/evaluations/p4-actions'
        delta=json.loads((folder/'delta-results.json').read_text(encoding='utf-8'))
        for case in delta['cases']:
            self.assertEqual('not_performed',case['runtime_evidence'])
            if case['catalog_id'] in ('ER-05','ER-08'):
                self.assertTrue(case['result']['needs_manual_review'])
        rename=next(c for c in delta['cases'] if c['catalog_id']=='ER-08')
        self.assertFalse(rename['action_plan'])
        self.assertIsNone(rename['result']['naming_resolution']['final_name'])

    def test_single_action_interfaces_are_unambiguous(self):
        for ident in IDS:
            with self.subTest(action=ident):
                guide = json.loads((PKG / 'references/atomic-guidance' / (ident.lower()+'.json')).read_text(encoding='utf-8'))
                self.assertEqual(ident, guide['catalog_id'])
                for key in ('input_fields', 'result_fields'):
                    fields = guide[key]
                    self.assertTrue(fields)
                    self.assertEqual(len(fields), len({f['name'] for f in fields}))
                    for field in fields:
                        self.assertTrue(field['type'])
                        self.assertTrue(field['description'])
                self.assertTrue(guide['procedure'])
                self.assertTrue(guide['rejection_rules'])

    def test_recovery_guidance_does_not_claim_runtime_evidence(self):
        registry = json.loads((PKG / 'references/operation-registry.json').read_text(encoding='utf-8'))
        for entry in registry['operations']:
            if entry['stage'] != 'execution_recovery':
                continue
            template = json.loads((PKG / entry['template_path']).read_text(encoding='utf-8'))
            if template['implementation']['mode'] in ('reasoning_guidance', 'computer_use'):
                self.assertNotEqual('passed', template['evidence_level']['layers']['spaceclaim_execution']['status'])


if __name__ == '__main__':
    unittest.main()
