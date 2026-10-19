# Python Script, API Version = V21
# ACTION_DIR and REPORT are injected by the host builder into a run-owned copy.
from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import *
from SpaceClaim.Api.V21.Modeler import Body as ModelerBody
from System import Array
import json, math, zipfile, hashlib, os, traceback

report = dict(status='failed', events=[], tests=[])
def bodies():
    return [b for b in GetRootPart().GetDescendants[DesignBody]() if b.Parent == GetRootPart()]
def bounds(item):
    shape = item.Shape if hasattr(item,'Shape') else item
    b = shape.GetBoundingBox(Matrix.Identity)
    return [float(v)*1000 for v in (b.MinCorner.X,b.MinCorner.Y,b.MinCorner.Z,b.MaxCorner.X,b.MaxCorner.Y,b.MaxCorner.Z)]
def close(a,b,t=.001):
    if math.isnan(float(a)) or math.isinf(float(a)) or abs(a-b)>t:
        raise AssertionError(str((a,b,t)))
def boxmatch(item,expected):
    return all(abs(a-b)<.001 for a,b in zip(bounds(item),expected))
def solid(body,volume,bbox,volume_tolerance=.001):
    topology = body.Shape if isinstance(body, DesignBody) else body.Master.Shape
    if not topology.IsClosed or not topology.IsManifold or topology.PieceCount!=1:
        raise AssertionError('Invalid solid')
    close(float(body.Shape.Volume)*1e9,volume,volume_tolerance)
    if not boxmatch(body,bbox): raise AssertionError(str((bounds(body),bbox)))
    return dict(bbox_mm=bounds(body),volume_mm3=float(body.Shape.Volume)*1e9)
def one(items):
    items=list(items)
    if len(items)!=1: raise AssertionError('Expected unique object: '+str(len(items)))
    return items[0]
def call(ident,params):
    path=os.path.join(ACTION_DIR,ident.lower()+'.scscript')
    with open(path,'rb') as stream: digest=hashlib.sha256(stream.read()).hexdigest()
    with zipfile.ZipFile(path) as archive: source=archive.read('_script')
    event=dict(id=ident,status='failed',archive_sha256=digest,source_sha256=hashlib.sha256(source).hexdigest()); report['events'].append(event)
    scope=dict(globals()); scope['ATOMIC_INPUT']=params
    try: exec(compile(source,ident+'::_script','exec'),scope,scope)
    except: event['error']=traceback.format_exc(); raise
    event['status']='executed'
    return scope['ATOMIC_OUTPUT']
def group(name,fn):
    row=dict(id=name,status='failed'); report['tests'].append(row)
    try: row['checks']=fn(); row['status']='passed'
    except: row['error']=traceback.format_exc()
def point(values): return Point.Create(*[v/1000.0 for v in values])
def block(low,high):
    r=BlockBody.Create(point(low),point(high),ExtrudeType.ForceIndependent)
    if not r.Success: raise AssertionError('Fixture block failed')
    return r.CreatedBody
def sheet(vertices):
    pts=[point(v) for v in vertices]
    curves=Array[ITrimmedCurve]([CurveSegment.Create(pts[i],pts[(i+1)%len(pts)]) for i in range(len(pts))])
    plane=Plane.Create(Frame.Create(pts[0],Direction.DirX,Direction.DirY))
    b=DesignBody.Create(GetRootPart(),'TEST_SECTION',ModelerBody.CreatePlanarBody(plane,curves))
    return one(b.Faces)
def test_until():
    target=block([0,-10,12],[20,10,14])
    face=one(f for f in target.Faces if boxmatch(f,[0,-10,12,20,10,12]))
    section=sheet([[8,-3,0],[12,-3,0],[12,3,0],[8,3,0]])
    out=call('MA-07',dict(profile_face=section,target_face=face,direction=[0,0,1],seed_point_mm=[10,0,0]))
    b=out['body'] if isinstance(out,dict) else out
    return solid(b,288,[8,-3,0,12,3,12])
def test_revolve():
    section=sheet([[52,0,0],[54,0,0],[54,6,0],[52,6,0]])
    out=call('MA-08',dict(profile_face=section,axis_origin_mm=[50,0,0],axis_direction=[0,1,0],angle_degrees=360))
    b=out['body'] if isinstance(out,dict) else out
    # Curved-body kernel integration is approximate; independently constrain
    # both analytic surfaces and their trims, not only an aggregate volume.
    cylinders=[f for f in b.Faces if f.Shape.Geometry.GetType().Name=='Cylinder']
    if len(cylinders)!=2: raise AssertionError('Expected inner and outer cylinders')
    areas=[]
    for radius in (2,4):
        face=one(f for f in cylinders if boxmatch(f,[50-radius,0,-radius,50+radius,6,radius]))
        close(float(face.Shape.Area)*1e6,2*math.pi*radius*6,.01)
        areas.append(float(face.Shape.Area)*1e6)
    checks=solid(b,72*math.pi,[46,0,-4,54,6,4],.02)
    checks['volume_tolerance_mm3']=.02
    checks['cylinder_areas_mm2']=areas
    return checks
def test_shell():
    b=block([80,0,0],[90,10,10])
    top=one(f for f in b.Faces if boxmatch(f,[80,0,10,90,10,10]))
    out=call('MA-11',dict(body=b,remove_faces=[top],offset_mm=-1))
    b=out['body'] if isinstance(out,dict) else out
    return solid(b,424,[80,0,0,90,10,10])
def test_mirror():
    b=block([110,0,0],[114,6,8])
    plane=block([99,-10,-10],[100,10,10])
    face=one(f for f in plane.Faces if boxmatch(f,[100,-10,-10,100,10,10]))
    out=call('MA-17',dict(body=b,plane_face=face,source_policy='preserve',volume_tolerance_mm3=.001,bbox_tolerance_mm=.001))
    solid(b,192,[110,0,0,114,6,8])
    return solid(out,192,[86,0,0,90,6,8])
def test_volume():
    outer=ModelerBody.ExtrudeProfile(RectangleProfile(Plane.Create(Frame.Create(point([145,5,0]),Direction.DirX,Direction.DirY)),.01,.01,PointUV.Create(0,0),0),.01)
    inner=ModelerBody.ExtrudeProfile(RectangleProfile(Plane.Create(Frame.Create(point([145,5,2]),Direction.DirX,Direction.DirY)),.006,.006,PointUV.Create(0,0),0),.006)
    outer.Subtract(Array[ModelerBody]([inner]))
    b=DesignBody.Create(GetRootPart(),'ENCLOSED_SOURCE',outer)
    solid(b,784,[140,0,0,150,10,10])
    seed=one(f for f in b.Faces if boxmatch(f,[142,2,2,142,8,8]))
    out=call('MA-25',dict(source_body=b,seed_face=seed,seed_point_mm=[142,5,5],position_tolerance_mm=.001))
    solid(b,784,[140,0,0,150,10,10])
    return solid(out,216,[142,2,2,148,8,8])

try:
    if bodies(): raise AssertionError('Requires a fresh blank root design')
    group('until-planar-face',test_until)
    group('revolve-ring',test_revolve)
    group('open-shell',test_shell)
    group('mirror-body',test_mirror)
    group('enclosed-volume',test_volume)
    report['status']='passed' if all(t['status']=='passed' for t in report['tests']) else 'failed'
except: report['error']=traceback.format_exc()
with open(REPORT,'wb') as stream: stream.write(json.dumps(report,indent=2).encode('utf-8'))
print(json.dumps(report))
