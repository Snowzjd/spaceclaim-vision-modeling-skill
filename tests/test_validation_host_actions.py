import importlib.util
import hashlib
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validation_host_actions',ROOT/'spaceclaim-vision-modeling/scripts/validation_host_actions.py')
M=importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


class ValidationHostActionsTests(unittest.TestCase):
    def test_file_identity_matches_and_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'model.scdoc'
            path.write_bytes(b'synthetic')
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual('passed',M.check_output_file_identity(path,digest)['status'])
            self.assertEqual('failed',M.check_output_file_identity(path,'0'*64)['status'])
            self.assertFalse(M.check_output_file_identity(path,digest)['geometry_verified'])

    def test_identity_rejects_missing_directory_relative_and_bad_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            for path,digest in [(Path(folder),'0'*64),(Path(folder)/'missing','0'*64),('relative','0'*64)]:
                with self.assertRaises(M.ValidationInputError):
                    M.check_output_file_identity(path,digest)

    def test_save_check_is_identity_only_and_requires_correlated_record(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'model.scdoc'
            path.write_bytes(b'synthetic')
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            record=dict(status='passed',run_ref='run-a',sha256=digest)
            result=M.check_native_save_result(path,digest,record,'run-a')
            self.assertTrue(result['save_record_consistent'])
            self.assertFalse(result['native_save_observed'])
            with self.assertRaises(M.ValidationInputError):
                M.check_native_save_result(path,digest,record,'run-b')

    def observation(self,value=12):
        return dict(source_kind='native_reopen',status='measured',property='volume_mm3',
                    object_identity='semantic-body',observation_ref='measurement-1',artifact_sha256='a'*64,value=value)

    def test_scalar_vector_and_string_comparisons(self):
        for actual,expected,tolerance in [(12,12.01,.02),([1,2,3],[1,2,3.01],.02),('part','part',0)]:
            self.assertEqual('passed',M.check_observed_property(self.observation(actual),expected,'a'*64,absolute_tolerance=tolerance)['status'])
        self.assertEqual('failed',M.check_observed_property(self.observation(),13,'a'*64)['status'])

    def test_nonfinite_mixed_and_missing_properties_rejected(self):
        for actual,expected in [(float('nan'),1),(True,1),([],[]),({'x':1},{'x':1}),('', '')]:
            with self.assertRaises(M.ValidationInputError):
                M.check_observed_property(self.observation(actual),expected,'a'*64)
        for tol in (-1,float('inf'),True):
            with self.assertRaises(M.ValidationInputError):
                M.check_observed_property(self.observation(),12,'a'*64,absolute_tolerance=tol)

    def test_reopen_and_reimport_are_not_interchangeable(self):
        obs=self.observation()
        with self.assertRaises(M.ValidationInputError):
            M.check_observed_property(obs,12,'a'*64,action_id='VA-25')
        with self.assertRaises(M.ValidationInputError):
            M.check_observed_property(obs,12,'b'*64)
        obs['source_kind']='reimport'
        result=M.check_observed_property(obs,12,'a'*64,action_id='VA-25')
        self.assertEqual('passed',result['status'])
        self.assertFalse(result['runtime_observed'])


if __name__=='__main__':
    unittest.main()
