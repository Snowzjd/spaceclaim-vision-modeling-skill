# Python Script, API Version = V21
from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import *
import json, os, zipfile, hashlib, traceback
report = dict(status='failed', tests=[])
def check():
    if list(GetRootPart().GetDescendants[DesignBody]()):
        raise ValueError('Test requires a new unsaved design')
    BlockBody.Create(Point.Create(0,0,0),Point.Create(.007,.011,.013))
    current = list(GetRootPart().GetDescendants[DesignBody]())
    if len(current)!=1 or abs(float(current[0].Shape.Volume)*1e9-1001)>.001:
        raise AssertionError('Independent fixture volume mismatch')
    with zipfile.ZipFile(ACTION) as archive:
        action = archive.read('_script')
    params = dict(expected_root=GetRootPart(), run_root=RUN,
        output_path=os.path.join(RUN,'native.scdoc'), critical_checks=[dict(id='volume',status='failed')])
    scope = dict(globals())
    scope['ATOMIC_INPUT'] = params
    try:
        exec(compile(action,'EX14::_script','exec'),scope,scope)
    except ValueError:
        if os.path.exists(params['output_path']):
            raise AssertionError('Failed critical check saved output')
        report['tests'].append(dict(id='critical-save-block',status='passed'))
    else:
        raise AssertionError('Critical failure did not block save')
    params['critical_checks']=[dict(id='volume',status='passed')]
    scope['ATOMIC_INPUT']=params
    exec(compile(action,'EX14::_script','exec'),scope,scope)
    output=scope['ATOMIC_OUTPUT']
    if not os.path.isfile(output['path']):
        raise AssertionError('Native output absent')
    with open(ACTION,'rb') as stream:
        report['action_sha256']=hashlib.sha256(stream.read()).hexdigest()
    report['source_sha256']=hashlib.sha256(action).hexdigest()
    report['tests'].append(dict(id='native-save',status='passed',sha256=output['sha256'],volume_mm3=1001))
    report['status']='passed'
try:
    check()
except:
    report['error']=traceback.format_exc()
finally:
    with open(os.path.join(RUN,'report.json'),'wb') as stream:
        stream.write(json.dumps(report,indent=2).encode('utf-8'))
print(report['status'])
