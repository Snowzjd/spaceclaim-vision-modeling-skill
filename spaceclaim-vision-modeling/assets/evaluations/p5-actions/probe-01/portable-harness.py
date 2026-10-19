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


def create_fixture():
    if list(GetRootPart().GetDescendants[DesignBody]()):
        raise ValueError('This synthetic test requires a new unsaved design')
    block=BlockBody.Create(point([0,0,0]),point([7,11,13]),ExtrudeType.ForceIndependent).CreatedBody
    RenameObject.Execute(BodySelection.Create(block),'measurement-block')
    plane=Plane.Create(Frame.Create(Point.Create(0,0,0),Direction.DirX,Direction.DirY))
    cylinders=[]
    for x,name in ((30,'measurement-cylinder'),(60,'measurement-round')):
        profile=CircleProfile(plane,.005,PointUV.Create(x/1000.0,0),0)
        kernel=ModelerBody.ExtrudeProfile(profile,.020)
        cylinders.append(DesignBody.Create(GetRootPart(),name,kernel))
    cylinder,rounded=cylinders
    edge=unique(e for e in rounded.Edges if at_bounds(e,[55,-5,0,65,5,0]))
    result=ConstantRound.Execute(EdgeSelection.Create(edge),.001)
    if not result.Success:
        raise AssertionError('Synthetic circular-edge fillet failed')
    # Re-enumerate after topology mutation; do not use stale edge caches.
    rounded=unique(b for b in GetRootPart().GetDescendants[DesignBody]() if b.Name=='measurement-round')
    vertices=[[92,0,0],[94,6,0],[90,6,0],[90,0,0]]
    pts=[point(v) for v in vertices]
    curves=Array[ITrimmedCurve]([CurveSegment.Create(pts[i],pts[(i+1)%4]) for i in range(4)])
    sheet=DesignBody.Create(GetRootPart(),'fixture-section',ModelerBody.CreatePlanarBody(plane,curves))
    options=RevolveFaceOptions()
    options.ExtrudeType=ExtrudeType.ForceIndependent
    options.PullSymmetric=False
    before=list(GetRootPart().GetDescendants[DesignBody]())
    result=RevolveFaces.Execute(FaceSelection.Create(unique(sheet.Faces)),Line.Create(point([90,0,0]),Direction.DirY),2*math.pi,options,None)
    if not result.Success:
        raise AssertionError('Synthetic conical revolve failed')
    cone=unique(b for b in GetRootPart().GetDescendants[DesignBody]() if b not in before and b.Shape.IsClosed)
    RenameObject.Execute(BodySelection.Create(cone),'measurement-cone')
    top=unique(f for f in block.Faces if at_bounds(f,[0,0,13,7,11,13]))
    group_result=NamedSelection.Create(FaceSelection.Create(top),Selection.Empty())
    if not group_result.Success:
        raise AssertionError('Synthetic group creation failed')
    return dict(block=block,cylinder=cylinder,rounded=rounded,cone=cone,top=top,group=group_result.CreatedNamedSelection)


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
    fixture=create_fixture()
    root=GetRootPart()
    b=fixture['block']
    p=dict(root=root,body=b,unit='mm',frame='world')
    def enumeration(out):
        names=[str(x.Name) for x in out['bodies']]
        if not set(['measurement-block','measurement-cylinder','measurement-round','measurement-cone']).issubset(set(names)):
            raise AssertionError('Missing independently created named fixture body')
        return dict(names=names,count=out['count'])
    test('VA-04',dict(root=root),enumeration)
    test('VA-05',p,measured('count',6))
    test('VA-06',p,measured('count',12))
    q=dict(p,objects=list(b.Faces),expected_count=6,object_kind='face')
    test('VA-07',q,measured('count',6))
    test('VA-08',p,measured('bbox',[0,0,0,7,11,13]))
    test('VA-09',p,measured('volume',1001))
    test('VA-10',p,measured('surface_area',622))
    for mode,field,value in [('area','area',77),('center','center',[3.5,5.5,13]),('normal','normal',[0,0,1])]:
        test('VA-11',dict(p,face=fixture['top'],property=mode),measured(field,value))
    def plane_kind(out):
        if out['analytic_type']!='Plane': raise AssertionError('Plane classification')
        return dict(analytic_type=out['analytic_type'])
    test('VA-12',dict(p,face=fixture['top']),plane_kind)
    cylinder=fixture['cylinder']
    cylinder_face=unique(f for f in cylinder.Faces if f.Shape.Geometry.GetType().Name=='Cylinder')
    def cylinder_check(out):
        check_close(out['radius'],5)
        check_close(out['span'][1]-out['span'][0],20)
        check_close(abs(out['axis'][2]),1)
        return dict(radius=out['radius'],span=out['span'],axis=out['axis'])
    test('VA-13',dict(p,body=cylinder,face=cylinder_face),cylinder_check)
    cone=fixture['cone']
    cone_face=unique(f for f in cone.Faces if f.Shape.Geometry.GetType().Name=='Cone')
    def cone_check(out):
        check_close(out['angle'],math.atan(2.0/6.0)*180/math.pi)
        check_close(out['span'][1]-out['span'][0],6)
        return dict(angle_deg=out['angle'],span=out['span'])
    test('VA-14',dict(p,body=cone,face=cone_face,angle_mode='half'),cone_check)
    rounded=fixture['rounded']
    torus=unique(f for f in rounded.Faces if f.Shape.Geometry.GetType().Name=='Torus')
    test('VA-15',dict(p,body=rounded,face=torus,fillet_relation='analytic_minor_radius'),measured('minor_radius',1))
    def match(out):
        if not out['matches']: raise AssertionError('Property does not match')
        return dict(matches=True)
    test('VA-16',dict(feature_positions_mm=[[0,0,0],[20,0,0],[40,0,0]],tolerance_mm=.001,expected_rule=dict(mode='linear',step_mm=[20,0,0],count=3)),match)
    test('VA-17',dict(root=root,body=b,expected_name='measurement-block'),match)
    test('VA-18',dict(root=root,group=fixture['group'],expected_members=[fixture['top']]),match)
    report['fixture_after']=dict(block_bbox_mm=fixture_bounds(b),block_volume_mm3=float(b.Shape.Volume)*1e9)
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
