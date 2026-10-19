"""Synthetic host-only handoff guards; fixtures are not CAD runtime evidence."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('handoff',ROOT/'spaceclaim-vision-modeling/scripts/validate_workflow_handoff.py')
H=importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)

class WorkflowHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for name,content in [('build.scscript',b'host-only artifact identity fixture'),('model.scdoc',b'not a CAD model'),('observation.json',b'{"synthetic":true}')]:
            (self.root/name).write_bytes(content)
        self.contracts=[]
        for index,stage in enumerate(H.STAGES):
            contract=dict(contract_id='stage-'+str(index),contract_kind=H.KINDS[index],contract_version=1,stage=stage,handoff_status='ready',
                upstream_contract_refs=[],artifact_refs=[],assumptions=[],unresolved_items=[],evidence_refs=[])
            contract.update({field:[] for field in H.FIELDS[index].split()})
            self.contracts.append(contract)
        g,b,e,a=self.contracts
        g.update(source_manifest=[dict(kind='text',content='Triangle (0,0),(19,0),(0,13) mm, height7mm')],
            coordinate_system=dict(unit='mm',handedness='right_handed'),confidence='high',dimensions_with_provenance=[dict(height=7,source='user text')])
        b.update(geometry_contract_ref=g['contract_id'],scscript_artifact=self.ref('build.scscript'),host_preflight_result=dict(status='passed'),construction_strategy='extrude',target_environment=dict(api='V21'),entry_state_policy='new_unsaved',output_policy=dict(native='new_path'))
        e.update(build_contract_ref=b['contract_id'],executed_artifact_identity=self.ref('build.scscript'),model_artifact=self.ref('model.scdoc'),entry_state_observed={},runtime_report={},failure_state='none',save_state='not_tested')
        a.update(artifact_identity=self.ref('model.scdoc'),overall_status='not_tested',native_save_result='not_tested',native_reopen_result='not_tested',visual_agreement='not_tested',requested_export_result='not_tested',evidence_map={layer:dict(status='not_tested',evidence_refs=[]) for layer in H.LAYERS})
        self.rebind()
        self.document=dict(handoff_version=1,required_evidence_layers=['geometry_measurements','visual_review'],contracts=self.contracts)

    def ref(self,name):
        return dict(path=name,sha256=hashlib.sha256((self.root/name).read_bytes()).hexdigest())
    def rebind(self):
        for index,contract in enumerate(self.contracts):
            contract['upstream_contract_refs']=[] if not index else [dict(contract_id=self.contracts[index-1]['contract_id'],sha256=H.contract_sha256(self.contracts[index-1]))]
    def check(self): return H.validate_handoff(self.document,self.root)
    def test_complete_structural_handoff_is_not_cad_verification(self):
        result=self.check()
        self.assertEqual('passed',result['status'])
        self.assertFalse(result['cad_verified'])
        self.assertEqual('host_handoff_integrity_only',result['evidence_level'])
        self.assertEqual('validation_visual_review',result['next_stage'])
    def test_preparation_only_returns_execution_as_pending(self):
        self.contracts[2]['handoff_status']='not_tested'
        self.contracts[3]['handoff_status']='not_tested'
        self.rebind()
        result=self.check()
        self.assertEqual('passed',result['status'])
        self.assertEqual('execution_recovery',result['next_stage'])
    def test_stale_upstream_dimensions_are_rejected(self):
        self.contracts[0]['dimensions_with_provenance'][0]['height']=8
        result=self.check()
        self.assertEqual('failed',result['status'])
        self.assertTrue(any('Stale' in x['message'] for x in result['issues']))
    def test_missing_dimension_cannot_be_ready_or_bypassed(self):
        self.contracts[0]['unresolved_items']=['thickness not supplied']
        self.contracts[0]['handoff_status']='requires_clarification'
        self.rebind()
        result=self.check()
        self.assertEqual('failed',result['status'])
        self.assertEqual('geometry_understanding',result['next_stage'])
    def test_plain_python_is_not_formal_execution_artifact(self):
        (self.root/'build.py').write_bytes(b'print(1)')
        self.contracts[1]['scscript_artifact']=self.ref('build.py')
        self.rebind()
        self.assertEqual('failed',self.check()['status'])
    def test_changed_execution_bytes_or_path_escape_are_rejected(self):
        original=copy.deepcopy(self.document)
        self.contracts[2]['executed_artifact_identity']['sha256']='0'*64
        self.rebind()
        self.assertEqual('failed',self.check()['status'])
        self.document=original
        self.document['contracts'][0]['artifact_refs']=[dict(path='../outside',sha256='0'*64)]
        self.assertEqual('failed',self.check()['status'])
    def test_unperformed_requested_layer_cannot_pass_overall(self):
        self.contracts[3]['overall_status']='passed'
        self.assertEqual('failed',self.check()['status'])
    def test_declared_pass_requires_bound_evidence_and_correct_model(self):
        acceptance=self.contracts[3]
        acceptance['overall_status']='passed'
        for layer in self.document['required_evidence_layers']:
            acceptance['evidence_map'][layer]=dict(status='passed',evidence_refs=[self.ref('observation.json')])
        self.assertEqual('passed',self.check()['status'])
        acceptance['artifact_identity']=self.ref('observation.json')
        self.assertEqual('failed',self.check()['status'])
    def test_malformed_contract_fields_fail_closed(self):
        self.contracts[0]['handoff_status']=[]
        self.contracts[1]['upstream_contract_refs']=[dict(contract_id=[])]
        self.assertEqual('failed',self.check()['status'])
    def test_missing_model_is_rejected_even_when_acceptance_copies_identity(self):
        self.contracts[2]['model_artifact']=dict(path='missing.scdoc',sha256='0'*64)
        self.contracts[3]['artifact_identity']=dict(self.contracts[2]['model_artifact'])
        self.rebind()
        self.assertEqual('failed',self.check()['status'])
    def test_unsaved_model_requires_a_bound_observation(self):
        self.contracts[2]['model_artifact']=dict(unsaved_document_id='synthetic-document',observation_ref=self.ref('observation.json'))
        self.contracts[3]['artifact_identity']=copy.deepcopy(self.contracts[2]['model_artifact'])
        self.rebind()
        self.assertEqual('passed',self.check()['status'])
        self.contracts[2]['model_artifact']['observation_ref']['sha256']='0'*64
        self.rebind()
        self.assertEqual('failed',self.check()['status'])
    def test_empty_or_malformed_acceptance_cannot_bypass_layers(self):
        self.document['required_evidence_layers']=[]
        self.contracts[3]['overall_status']='passed'
        self.assertEqual('failed',self.check()['status'])
        self.contracts[3]['overall_status']=[]
        self.assertEqual('failed',self.check()['status'])
    def test_unperformed_layer_still_requires_an_explicit_reference_array(self):
        self.contracts[3]['evidence_map']['visual_review']['evidence_refs']='wrong'
        self.assertEqual('failed',self.check()['status'])
    def test_geometry_payload_shape_is_checked(self):
        self.contracts[0].update(source_manifest='malformed',coordinate_system=42)
        self.rebind()
        self.assertEqual('failed',self.check()['status'])
    def test_bad_predecessor_and_nonfinite_json_return_failures(self):
        self.contracts[2]='bad predecessor'
        self.assertEqual('failed',self.check()['status'])
        self.document['unrelated_value']=float('nan')
        self.assertEqual('failed',self.check()['status'])

if __name__=='__main__': unittest.main()
