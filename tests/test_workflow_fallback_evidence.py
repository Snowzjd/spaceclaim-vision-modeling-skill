"""Check P6 portable preparation evidence without executing SpaceClaim."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/'spaceclaim-vision-modeling'
DATA=PKG/'assets/evaluations/p6-integration'
sys.path.insert(0,str(PKG/'scripts'))
from audit_scscript import audit_archive
from validate_workflow_handoff import validate_handoff

def read(name): return json.loads((DATA/name).read_text(encoding='utf-8'))

class WorkflowFallbackEvidenceTests(unittest.TestCase):
    def test_manifest_and_provenance_bind_public_bytes(self):
        manifest=read('manifest.json')
        for name,digest in manifest['files'].items():
            self.assertEqual(digest,hashlib.sha256((DATA/name).read_bytes()).hexdigest(),name)
        for record in read('evaluation.json')['provenance']:
            ref=record['public']
            self.assertEqual(ref['sha256'],manifest['files'][ref['path']])

    def test_formal_archive_exact_source_and_unconfigured_guard(self):
        for revision in ['initial','corrected']:
            source=(DATA/(revision+'.py')).read_bytes()
            with zipfile.ZipFile(DATA/(revision+'.scscript')) as archive:
                self.assertEqual(source,archive.read('_script'))
            self.assertEqual('passed',audit_archive(DATA/(revision+'.scscript'),require_api='21')['status'])
            # Guard must fail on the host before reaching unavailable CAD imports,
            # with no output directories, report writes or model mutations.
            with self.assertRaisesRegex(ValueError,'Configure explicit'):
                exec(compile(source,str(DATA/(revision+'.py')),'exec'),{})

    def test_dimensions_derived_from_request_not_other_case(self):
        source=ast.parse((DATA/'corrected.py').read_text(encoding='utf-8'))
        values={node.targets[0].id:ast.literal_eval(node.value) for node in source.body
                if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name)}
        vertices=values['PROFILE_VERTICES_MM']
        self.assertEqual([[0,0,0],[19,0,0],[0,13,0]],vertices)
        volume=19*13*0.5*7
        self.assertEqual(volume,values['EXPECTED_VOLUME_MM3'])
        delta=values['TRANSLATION_MM']
        bounds=delta+[19+delta[0],13+delta[1],7+delta[2]]
        self.assertEqual(bounds,values['EXPECTED_AFTER_BBOX_MM'])

    def test_missing_dimensions_stop_without_script(self):
        clarification=read('clarification.json')
        self.assertEqual('not_generated',clarification['script_status'])
        self.assertTrue({'thickness_mm','notch_depth_mm'} <= {x['id'] for x in clarification['questions']})
        self.assertFalse(read('evaluation.json')['request_B_script_generated'])

    def test_handoffs_delta_and_evidence_remain_bounded(self):
        for request,stage in [('A','modeling_strategy_scripting'),('B','geometry_understanding')]:
            result=validate_handoff(read('handoff-'+request+'.json'),DATA)
            self.assertEqual('passed',result['status'],result['issues'])
            self.assertEqual(stage,result['next_stage'])
            self.assertFalse(result['cad_verified'])
        evidence=read('evaluation.json')
        self.assertEqual('passed_after_review_delta',evidence['status'])
        self.assertEqual(3,len(evidence['review_corrections']))
        self.assertEqual([],evidence['candidates_promoted'])
        self.assertEqual({'not_tested'},set(evidence['evidence_layers'].values()))
        self.assertFalse(evidence['desktop_or_cad_execution_performed'])
        self.assertEqual('execution_recovery',evidence['local_handoff_checks']['A']['result']['next_stage'])
        self.assertEqual('generic_v0.2_fallback',read('routing-record.json')['selected_route'])
        self.assertEqual(['references/operation-registry.json'],read('package-isolation.json')['removed_from_copy_only'])

if __name__=='__main__': unittest.main()
