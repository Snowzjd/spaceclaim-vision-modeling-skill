"""Public P5 evidence integrity, not a replacement for live CAD tests."""
import hashlib
import json
from pathlib import Path
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/'spaceclaim-vision-modeling'
EVIDENCE=PKG/'assets/evaluations/p5-actions'
ACTIONS=PKG/'assets/operation-templates/validation-visual-review/actions'
def load(path): return json.loads(path.read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

class ValidationRuntimeEvidenceTests(unittest.TestCase):
    def checked_ref(self,ref):
        path=ROOT/ref['path']
        self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()))
        self.assertEqual(sha(path),ref['sha256'])
        return path

    def test_exact_action_runtime_and_assertion_coverage(self):
        covered=set()
        snapshots=load(EVIDENCE/'runtime-snapshots.json')
        self.assertTrue(any(row['status']=='failed' for row in snapshots['runs']))
        for run in snapshots['runs']:
            report=load(self.checked_ref(run['report']))
            self.checked_ref(run['portable_harness'])
            for ref in run['actions']: self.checked_ref(ref)
            self.assertEqual(len(report['events']),len(report['tests']))
            for event,test in zip(report['events'],report['tests']):
                self.assertEqual(event['id'],test['id'])
                archive=EVIDENCE/run['run_id']/'actions'/(event['id'].lower()+'.scscript')
                self.assertEqual(sha(archive),event['archive_sha256'])
                with zipfile.ZipFile(archive) as bundle:
                    self.assertEqual(hashlib.sha256(bundle.read('_script')).hexdigest(),event['source_sha256'])
                current=ACTIONS/archive.name
                if sha(current)==event['archive_sha256'] and event['status']=='executed' and test['status']=='passed':
                    covered.add(event['id'])
        self.assertEqual({'VA-%02d'%n for n in range(4,19)},covered)

    def test_portable_harnesses_do_not_contain_machine_paths(self):
        for path in EVIDENCE.rglob('*test.py'):
            self.assertNotRegex(path.read_text(encoding='utf-8'),r'[A-Za-z]:[\\/]')
        for path in EVIDENCE.rglob('portable-harness.py'):
            source=path.read_text(encoding='utf-8')
            self.assertNotRegex(source,r'[A-Za-z]:[\\/]')
            self.assertNotRegex(source,r'(?m)^(ACTION_DIR|REPORT) = ')

    def test_visual_evidence_scopes_and_hashes(self):
        record=load(EVIDENCE/'visual-evidence.json')
        self.assertEqual(7,len(record['screenshots']))
        for shot in record['screenshots']:
            self.checked_ref(shot['screenshot'])
            self.checked_ref(shot['model'])
            self.assertTrue(shot['maximized'])
            for key in ['view','selection','expected','observed','occlusion']:
                self.assertTrue(shot[key])
        for action in record['actions']:
            self.checked_ref(action['guide'])
            self.checked_ref(action['screenshot'])
        spin=next(x for x in record['actions'] if x['catalog_id']=='VI-11')
        self.assertIn('direct middle drag not tested',spin['observed_variant'])
        clipped=next(x for x in record['screenshots'] if x['screenshot']['path'].endswith('spin-diagnostic.png'))
        self.assertFalse(clipped['clean_capture'])

    def test_reopen_observation_bound_to_native_bytes(self):
        record=load(EVIDENCE/'reopen-evidence.json')
        self.checked_ref(record['model'])
        self.checked_ref(record['portable_harness'])
        for action in record['controller_observations']:
            self.checked_ref(action['guide'])
        self.assertEqual(['VA-21','VA-22'],[x['catalog_id'] for x in record['controller_observations']])

if __name__=='__main__': unittest.main()
