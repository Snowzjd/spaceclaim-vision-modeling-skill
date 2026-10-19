"""Check four-stage handoff integrity on the host; never execute or accept CAD.

Inputs are declared contracts, not independent observations. Unknown stages stay
pending. Candidate routing and modeling remain decisions of the Skill, not this
checker; it is not a composition engine.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re

STAGES=("geometry_understanding","modeling_strategy_scripting","execution_recovery","validation_visual_review")
KINDS=("geometry_contract","build_contract","execution_contract","acceptance_contract")
FIELDS=(
    "source_manifest observed_geometry bodies_and_features spatial_relations coordinate_system dimensions_with_provenance symmetry_and_repetition confidence validation_intent",
    "geometry_contract_ref parameter_table construction_strategy ordered_operation_plan topology_dependencies semantic_selection_plan failure_checkpoints validation_plan target_environment entry_state_policy output_policy scscript_artifact host_preflight_result unresolved_risks",
    "build_contract_ref entry_state_observed executed_artifact_identity stage_events runtime_report model_artifact failure_state recovery_actions save_state unresolved_runtime_risks",
    "artifact_identity geometry_acceptance body_feature_and_name_checks dimension_bbox_and_volume_checks native_save_result native_reopen_result visual_review_views visual_agreement requested_export_result evidence_map unresolved_risks overall_status",
)
LAYERS=("spaceclaim_execution","geometry_measurements","native_save","native_reopen","visual_review","requested_export")
STATUSES={"draft","requires_clarification","ready","passed","failed","not_tested"}
SHAPES=(
    dict(source_manifest=list,observed_geometry=(list,dict),bodies_and_features=list,
         spatial_relations=list,coordinate_system=dict,dimensions_with_provenance=list,
         symmetry_and_repetition=(list,dict),confidence=(str,dict,int,float),validation_intent=(list,dict)),
    dict(parameter_table=(list,dict),construction_strategy=(str,dict),ordered_operation_plan=list,
         topology_dependencies=(list,dict),semantic_selection_plan=(list,dict),failure_checkpoints=(list,dict),
         validation_plan=(list,dict),target_environment=dict,entry_state_policy=(str,dict),
         output_policy=dict,unresolved_risks=list),
    dict(entry_state_observed=dict,stage_events=list,runtime_report=dict,model_artifact=dict,
         failure_state=(str,dict),recovery_actions=list,save_state=(str,dict),unresolved_runtime_risks=list),
    dict(artifact_identity=dict,geometry_acceptance=(str,dict,list),body_feature_and_name_checks=(dict,list),
         dimension_bbox_and_volume_checks=(dict,list),native_save_result=(str,dict),native_reopen_result=(str,dict),
         visual_review_views=list,visual_agreement=(str,dict),requested_export_result=(str,dict),evidence_map=dict,
         unresolved_risks=list,overall_status=str),
)

def contract_sha256(contract):
    return hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()

def file_sha256(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): digest.update(block)
    return digest.hexdigest()

def validate_handoff(document,artifact_root):
    root=Path(artifact_root).resolve()
    issues=[]
    def issue(path,message): issues.append(dict(path=path,message=message))
    def check_artifact(ref,path,extension=None):
        if not isinstance(ref,dict):
            issue(path,'Expected artifact path and SHA-256'); return
        name,digest=ref.get('path'),ref.get('sha256')
        if not isinstance(name,str) or not name or re.match(r'^(?:[A-Za-z]:|[/\\])',name):
            issue(path,'Use a relative artifact path under the supplied run root'); return
        target=(root/name).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            issue(path,'Artifact is missing or escapes the supplied run root'); return
        if extension and target.suffix.lower()!=extension:
            issue(path,'Formal execution artifact must be '+extension)
        if not isinstance(digest,str) or not re.fullmatch('[0-9a-fA-F]{64}',digest) or file_sha256(target)!=digest.lower():
            issue(path,'Artifact hash mismatch')
    def check_model(ref,path):
        if isinstance(ref,dict) and 'unsaved_document_id' in ref:
            if not isinstance(ref['unsaved_document_id'],str) or not ref['unsaved_document_id'].strip():
                issue(path,'Unsaved model requires an explicit document identity')
            if 'path' in ref: issue(path,'Choose either persisted or unsaved model identity')
            check_artifact(ref.get('observation_ref'),path+'.observation_ref')
        else: check_artifact(ref,path)
    if not isinstance(document,dict) or type(document.get('handoff_version')) is not int or document.get('handoff_version')!=1 or not isinstance(document.get('contracts'),list):
        return dict(status='failed',evidence_level='host_handoff_integrity_only',issues=[dict(path='$',message='Expected handoff_version1 and contracts array')],next_stage=STAGES[0],cad_verified=False)
    try: contract_sha256(document)
    except (TypeError,ValueError):
        return dict(status='failed',evidence_level='host_handoff_integrity_only',issues=[dict(path='$',message='Expected finite serializable JSON values')],next_stage=STAGES[0],cad_verified=False)
    contracts=document['contracts']
    if not 1<=len(contracts)<=4: issue('$.contracts','Expected one to four ordered core-stage contracts')
    seen={}
    pending=None
    for index,contract in enumerate(contracts[:4]):
        issue_count=len(issues)
        loc='$.contracts[%d]'%index
        if not isinstance(contract,dict):
            issue(loc,'Expected contract object')
            if pending is None: pending=STAGES[index]
            continue
        stage=STAGES[index]
        ident=contract.get('contract_id')
        if not isinstance(ident,str) or not ident.strip() or ident in seen:
            issue(loc+'.contract_id','Expected unique nonempty contract identity')
        if contract.get('stage')!=stage or contract.get('contract_kind')!=KINDS[index]:
            issue(loc,'Core stages/kinds must remain in order')
        if type(contract.get('contract_version')) is not int or contract['contract_version']<1:
            issue(loc+'.contract_version','Expected positive integer version')
        status=contract.get('handoff_status')
        if not isinstance(status,str) or status not in STATUSES: issue(loc+'.handoff_status','Unknown handoff status')
        for field in ['upstream_contract_refs','artifact_refs','assumptions','unresolved_items','evidence_refs']:
            if not isinstance(contract.get(field),list): issue(loc+'.'+field,'Expected explicit array')
        for field in ['artifact_refs','evidence_refs']:
            for n,ref in enumerate(contract.get(field,[]) if isinstance(contract.get(field),list) else []):
                check_artifact(ref,loc+'.'+field+'[%d]'%n)
        upstream=contract.get('upstream_contract_refs',[])
        previous=contracts[index-1] if index and isinstance(contracts[index-1],dict) else {}
        previous_id=previous.get('contract_id')
        valid_links=[]
        for ref in upstream if isinstance(upstream,list) else []:
            if not isinstance(ref,dict) or not isinstance(ref.get('contract_id'),str) or ref.get('contract_id') not in seen:
                issue(loc+'.upstream_contract_refs','Upstream reference does not identify an earlier contract'); continue
            prior=seen[ref['contract_id']]
            if ref.get('sha256')!=contract_sha256(prior):
                issue(loc+'.upstream_contract_refs','Stale upstream contract hash')
            valid_links.append(ref['contract_id'])
        completed=status in ('ready','passed')
        if completed:
            if pending is not None: issue(loc,'Cannot complete a stage after an incomplete upstream stage')
            if contract.get('unresolved_items'): issue(loc+'.unresolved_items','Ready/passed handoff cannot retain blocking unresolved items; accepted assumptions belong in assumptions')
            if index and previous_id not in valid_links: issue(loc+'.upstream_contract_refs','Missing immediately preceding contract')
            for field in FIELDS[index].split():
                if field not in contract or contract[field] is None: issue(loc+'.'+field,'Missing required completed-stage output')
            for field,types in SHAPES[index].items():
                if not isinstance(contract.get(field),types) or isinstance(contract.get(field),bool):
                    issue(loc+'.'+field,'Invalid completed-stage payload shape')
            if index==0 and (not contract.get('source_manifest') or not contract.get('coordinate_system')):
                issue(loc,'Source manifest and coordinate system cannot be empty in a completed geometry contract')
            if index==1:
                if contract.get('geometry_contract_ref')!=previous_id: issue(loc+'.geometry_contract_ref','Wrong geometry contract identity')
                check_artifact(contract.get('scscript_artifact'),loc+'.scscript_artifact','.scscript')
                if not isinstance(contract.get('host_preflight_result'),dict) or contract['host_preflight_result'].get('status')!='passed':
                    issue(loc+'.host_preflight_result','Build handoff requires passed host preflight')
            if index==2:
                if contract.get('build_contract_ref')!=previous_id: issue(loc+'.build_contract_ref','Wrong build contract identity')
                check_artifact(contract.get('executed_artifact_identity'),loc+'.executed_artifact_identity','.scscript')
                if contract.get('executed_artifact_identity')!=previous.get('scscript_artifact'):
                    issue(loc+'.executed_artifact_identity','Executed artifact differs from accepted build')
                check_model(contract.get('model_artifact'),loc+'.model_artifact')
                if isinstance(contract.get('runtime_report'),dict) and contract['runtime_report'].get('status')=='failed':
                    issue(loc+'.runtime_report','A declared failed run requires recovery, not completed execution')
            if index==3:
                if contract.get('artifact_identity')!=previous.get('model_artifact'):
                    issue(loc+'.artifact_identity','Acceptance model differs from execution output')
                check_model(contract.get('artifact_identity'),loc+'.artifact_identity')
                if contract.get('overall_status') not in ('passed','failed','not_tested','needs_manual_review'):
                    issue(loc+'.overall_status','Invalid acceptance status')
                required=document.get('required_evidence_layers')
                if not isinstance(required,list) or any(not isinstance(x,str) or x not in LAYERS for x in required):
                    issue('$.required_evidence_layers','Declare the requested evidence layers explicitly')
                    required=[]
                evidence=contract.get('evidence_map')
                if not isinstance(evidence,dict): issue(loc+'.evidence_map','Expected explicit evidence map')
                else:
                    for layer in LAYERS:
                        value=evidence.get(layer)
                        if not isinstance(value,dict) or value.get('status') not in ('passed','failed','not_tested','not_applicable'):
                            issue(loc+'.evidence_map.'+layer,'Missing or invalid independent evidence layer'); continue
                        refs=value.get('evidence_refs')
                        if not isinstance(refs,list): issue(loc+'.evidence_map.'+layer,'Expected explicit evidence_refs array')
                        if value['status'] in ('passed','failed') and (not isinstance(refs,list) or not refs):
                            issue(loc+'.evidence_map.'+layer,'Observed result requires evidence references')
                        for n,ref in enumerate(refs if isinstance(refs,list) else []): check_artifact(ref,loc+'.evidence_map.'+layer+'[%d]'%n)
                    if contract.get('overall_status')=='passed':
                        if not required: issue(loc+'.overall_status','Overall passed requires at least one requested evidence layer')
                        for layer in required:
                            if not isinstance(evidence.get(layer),dict) or evidence[layer].get('status')!='passed':
                                issue(loc+'.overall_status','Requested layer has not passed: '+layer)
                        if any(isinstance(value,dict) and value.get('status')=='failed' for value in evidence.values()):
                            issue(loc+'.overall_status','A failed evidence layer cannot become overall passed')
                if pending is None and contract.get('overall_status')!='passed': pending=stage
        elif pending is None: pending=stage
        if len(issues)>issue_count and pending is None: pending=stage
        if isinstance(ident,str): seen[ident]=contract
    if pending is None and len(contracts)<4: pending=STAGES[len(contracts)]
    return dict(status='failed' if issues else 'passed',evidence_level='host_handoff_integrity_only',issues=issues,next_stage=pending,cad_verified=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('handoff',type=Path)
    parser.add_argument('--artifact-root',type=Path,required=True)
    args=parser.parse_args()
    try:
        result=validate_handoff(json.loads(args.handoff.read_text(encoding='utf-8'),parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON'))),args.artifact_root)
    except (ValueError,OSError) as exc:
        result=dict(status='failed',evidence_level='host_handoff_integrity_only',issues=[dict(path='$',message=str(exc))],cad_verified=False)
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='passed' else 1

if __name__=='__main__': raise SystemExit(main())
