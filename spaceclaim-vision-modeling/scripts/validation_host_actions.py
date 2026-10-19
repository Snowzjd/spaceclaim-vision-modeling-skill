"""Identity and single-property checks. Never opens or controls SpaceClaim."""
from __future__ import annotations
import hashlib
import math
from pathlib import Path
import stat


class ValidationInputError(ValueError):
    pass


def _digest(value):
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdefABCDEF' for c in value):
        raise ValidationInputError('Expected a SHA-256 digest')
    return value.lower()


def check_output_file_identity(path, expected_sha256):
    target=Path(path)
    if not target.is_absolute():
        raise ValidationInputError('Use an explicit absolute file path')
    for component in (target,*target.parents):
        if component.is_symlink() or (component.exists() and getattr(component.stat(),'st_file_attributes',0) & getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',1024)):
            raise ValidationInputError('Reparse/symlink identity is unsupported')
    if not target.is_file():
        raise ValidationInputError('Expected a regular existing output file')
    expected=_digest(expected_sha256)
    digest=hashlib.sha256()
    with target.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            digest.update(block)
    actual=digest.hexdigest()
    return dict(action_id='VA-19',status='passed' if actual==expected else 'failed',
        path=str(target),sha256=actual,expected_sha256=expected,size_bytes=target.stat().st_size,
        evidence_level='host_checked',geometry_verified=False)


def check_native_save_result(path, expected_sha256, save_record, run_ref):
    if Path(path).suffix.lower()!='.scdoc':
        raise ValidationInputError('Expected a native .scdoc')
    if not isinstance(run_ref,str) or not run_ref.strip():
        raise ValidationInputError('Supply a run reference')
    if not isinstance(save_record,dict) or save_record.get('run_ref')!=run_ref:
        raise ValidationInputError('Save record must belong to this run')
    if save_record.get('status')!='passed' or _digest(save_record.get('sha256'))!=_digest(expected_sha256):
        raise ValidationInputError('Save record lacks a matching passed hash')
    result=check_output_file_identity(path,expected_sha256)
    if result['size_bytes']==0:
        result['status']='failed'
    result.update(action_id='VA-20',run_ref=run_ref,save_record_consistent=result['status']=='passed',
                  native_save_observed=False,native_reopen='not_tested')
    return result


def _finite(value):
    return isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value)


def _equal(actual,expected,tolerance):
    if _finite(actual) and _finite(expected):
        return abs(actual-expected)<=tolerance
    if isinstance(actual,(int,float)) and not isinstance(actual,bool) or isinstance(expected,(int,float)) and not isinstance(expected,bool):
        raise ValidationInputError('Mixed or nonfinite numeric property')
    if isinstance(actual,list) and isinstance(expected,list):
        if not actual or not expected:
            raise ValidationInputError('An empty vector is not a measured property')
        if not all(_finite(v) for v in actual+expected):
            raise ValidationInputError('Only flat finite numeric vectors are supported')
        return len(actual)==len(expected) and all(abs(a-b)<=tolerance for a,b in zip(actual,expected))
    if type(actual) is type(expected) and isinstance(actual,(str,bool)):
        if isinstance(actual,str) and (not actual or not expected):
            raise ValidationInputError('Missing textual property')
        return actual==expected
    raise ValidationInputError('Unsupported or mismatched property representation')


def check_observed_property(observation,expected_value,expected_artifact_sha256,*,
                            absolute_tolerance=0.0,action_id='VA-23'):
    """Compare one declared observation; caller independently obtains it."""
    kinds={'VA-23':'native_reopen','VA-25':'reimport'}
    if action_id not in kinds:
        raise ValidationInputError('Expected VA-23 or VA-25')
    if not _finite(absolute_tolerance) or absolute_tolerance<0:
        raise ValidationInputError('Tolerance must be finite and nonnegative')
    if not isinstance(observation,dict):
        raise ValidationInputError('Supply one observed property record')
    if observation.get('source_kind')!=kinds[action_id] or observation.get('status')!='measured':
        raise ValidationInputError('Wrong or unmeasured observation source')
    for field in ('property','object_identity','observation_ref'):
        if not isinstance(observation.get(field),str) or not observation[field].strip():
            raise ValidationInputError('Missing '+field)
    if _digest(observation.get('artifact_sha256'))!=_digest(expected_artifact_sha256):
        raise ValidationInputError('Observation belongs to a different artifact')
    matched=_equal(observation.get('value'),expected_value,absolute_tolerance)
    return dict(action_id=action_id,status='passed' if matched else 'failed',
        property=observation['property'],object_identity=observation['object_identity'],
        actual=observation['value'],expected=expected_value,absolute_tolerance=absolute_tolerance,
        observation_ref=observation['observation_ref'],artifact_sha256=expected_artifact_sha256,
        evidence_level='host_checked',runtime_observed=False)
