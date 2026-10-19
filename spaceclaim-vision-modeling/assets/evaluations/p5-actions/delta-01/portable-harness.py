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
    bodies=list(root.GetDescendants[DesignBody]())
    cylinder=unique(b for b in bodies if b.Name=='measurement-cylinder')
    cone=unique(b for b in bodies if b.Name=='measurement-cone')
    p=dict(root=root,unit='mm',frame='world')
    def cylinder_check(out):
        check_close(out['radius'],5)
        check_close(out['span'],20)
        check_close(abs(out['axis'][2]),1)
        return dict(radius=out['radius'],span=out['span'],axis=out['axis'])
    def cone_check(out):
        check_close(out['angle'],math.atan(2.0/6.0)*180/math.pi)
        check_close(out['span'],6)
        return dict(angle_deg=out['angle'],span=out['span'])
    test('VA-13',dict(p,body=cylinder,face=unique(f for f in cylinder.Faces if f.Shape.Geometry.GetType().Name=='Cylinder')),cylinder_check)
    test('VA-14',dict(p,body=cone,face=unique(f for f in cone.Faces if f.Shape.Geometry.GetType().Name=='Cone'),angle_mode='half'),cone_check)
    def match(out):
        if not out['matches']: raise AssertionError('Mismatch')
        return dict(matches=True)
    test('VA-16',dict(root=root,positions_mm=[[0,0,0],[20,0,0],[40,0,0]],tolerance_mm=.001,expected_rule=dict(mode='linear',step_mm=[20,0,0],count=3)),match)
    test('VA-16',dict(root=root,positions_mm=[[5,0,0],[0,5,0],[-5,0,0],[0,-5,0]],tolerance_mm=.001,expected_rule=dict(mode='circular',center_mm=[0,0,0],axis=[0,0,1],pitch_radius_mm=5,angle_step_deg=90,count=4)),match)
    diagnostic=[]
    for g in WindowHelper.GetGroups():
        row=dict(type=g.GetType().FullName)
        for name in ['Name','Parent','Members','Items']:
            try:
                value=getattr(g,name)
                row[name]=dict(type=value.GetType().FullName,text=unicode(value))
                if name in ['Members','Items']:
                    row[name]['values']=[dict(type=x.GetType().FullName,text=unicode(x)) for x in value]
            except Exception as exc: row[name]=dict(error=unicode(exc))
        diagnostic.append(row)
    report['group_diagnostic']=diagnostic
    report['root_type']=root.GetType().FullName
    report['status']='passed' if all(x['status']=='passed' for x in report['tests']) else 'failed'

try:
    probe()
except:
    report['error']=traceback.format_exc()
finally:
    with open(REPORT,'wb') as stream:
        stream.write(json.dumps(report,indent=2,allow_nan=False).encode('utf-8'))
print(report['status'])
