# Python Script, API Version = V21
# Local synthetic probe fixture only; not an atomic operation or public recipe.
from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import *
from SpaceClaim.Api.V21.Modeler import Body as ModelerBody
from System import Array
import math


def unique(items):
    items=list(items)
    if len(items)!=1:
        raise AssertionError('Fixture needs one semantic match: '+str(len(items)))
    return items[0]


def fixture_bounds(item):
    shape=item.Shape if hasattr(item,'Shape') else item
    box=shape.GetBoundingBox(Matrix.Identity)
    return [float(v)*1000 for v in (box.MinCorner.X,box.MinCorner.Y,box.MinCorner.Z,box.MaxCorner.X,box.MaxCorner.Y,box.MaxCorner.Z)]


def at_bounds(item,values):
    return all(abs(a-b)<.001 for a,b in zip(fixture_bounds(item),values))


def point(values):
    return Point.Create(*[v/1000.0 for v in values])




import json,zipfile,hashlib,os,traceback
report=dict(status='failed',events=[],tests=[])

def check_close(actual,expected,tolerance=.001):
    if isinstance(expected,(list,tuple)):
        if len(actual)!=len(expected): raise AssertionError('Vector length')
        for a,b in zip(actual,expected): check_close(a,b,tolerance)
    elif math.isnan(float(actual)) or math.isinf(float(actual)) or abs(actual-expected)>tolerance:
        raise AssertionError('Mismatch: '+str((actual,expected,tolerance)))

def call(ident,params):
    path=os.path.join(ACTION_DIR,ident.lower()+'.scscript')
    with open(path,'rb') as stream: digest=hashlib.sha256(stream.read()).hexdigest()
    with zipfile.ZipFile(path) as archive: source=archive.read('_script')
    scope=dict(globals())
    scope['ATOMIC_INPUT']=params
    event=dict(id=ident,status='failed',archive_sha256=digest,source_sha256=hashlib.sha256(source).hexdigest())
    report['events'].append(event)
    try:
        exec(compile(source,ident+'::_script','exec'),scope,scope)
        result=scope['ATOMIC_OUTPUT']
        event['returned_status']=result.get('status')
        if result.get('status')!='passed':
            raise AssertionError('Action did not pass: '+str(result.get('reason',result.get('status'))))
        event['status']='executed'
        return result
    except:
        event['error']=traceback.format_exc()
        raise

def test(ident,params,assertion):
    row=dict(id=ident,status='failed')
    report['tests'].append(row)
    try:
        out=call(ident,params)
        row['check']=assertion(out)
        row['status']='passed'
    except:
        row['error']=traceback.format_exc()

def measured(field,expected,tol=.001):
    def verify(out):
        check_close(out[field],expected,tol)
        return {field:out[field]}
    return verify


def probe():
    root=GetRootPart()
    block=unique(b for b in root.GetDescendants[DesignBody]() if b.Name=='measurement-block')
    top=unique(f for f in block.Faces if at_bounds(f,[0,0,13,7,11,13]))
    groups=list(WindowHelper.GetGroups())
    group=unique(g for g in groups if len(list(g.Members))==1 and top in list(g.Members))
    def members(out):
        if not out['matches'] or out['actual_count']!=1 or out['expected_count']!=1:
            raise AssertionError('Group membership mismatch')
        return dict(matches=True,actual_count=out['actual_count'],expected_count=out['expected_count'])
    test('VA-18',dict(root=root,group=group,expected_members=[top]),members)
    report['fixture_after']=dict(block_bbox_mm=fixture_bounds(block),block_volume_mm3=float(block.Shape.Volume)*1e9)
    check_close(report['fixture_after']['block_volume_mm3'],1001)
    report['status']='passed' if all(x['status']=='passed' for x in report['tests']) else 'failed'

try:
    probe()
except:
    report['error']=traceback.format_exc()
finally:
    with open(REPORT,'wb') as stream:
        stream.write(json.dumps(report,indent=2,allow_nan=False).encode('utf-8'))
print(report['status'])
