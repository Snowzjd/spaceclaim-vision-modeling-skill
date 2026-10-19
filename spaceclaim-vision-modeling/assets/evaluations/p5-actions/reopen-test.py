# Python Script, API Version = V21
from SpaceClaim.Api.V21 import *
from SpaceClaim.Api.V21.Geometry import *
import os,json,hashlib,traceback
report=dict(status='failed',source_kind='native_reopen')
try:
    actual=unicode(Window.ActiveWindow.Document.Path)
    if os.path.normcase(os.path.abspath(actual))!=os.path.normcase(os.path.abspath(EXPECTED)):
        raise ValueError('Wrong active native document')
    with open(actual,'rb') as stream:
        digest=hashlib.sha256(stream.read()).hexdigest()
    if digest!='17344d5004c2f160a8c484519bb77d5bb6a744f3ec085ad5c54e47f736e36bc3':
        raise ValueError('Unexpected native bytes')
    bodies=list(GetRootPart().GetDescendants[DesignBody]())
    if len(bodies)!=1: raise ValueError('Expected one reopened synthetic body')
    body=bodies[0]
    box=body.Shape.GetBoundingBox(Matrix.Identity)
    bbox=[float(v)*1000 for v in (box.MinCorner.X,box.MinCorner.Y,box.MinCorner.Z,box.MaxCorner.X,box.MaxCorner.Y,box.MaxCorner.Z)]
    volume=float(body.Shape.Volume)*1e9
    if any(abs(a-b)>.001 for a,b in zip(bbox,[0,0,0,7,11,13])) or abs(volume-1001)>.001:
        raise AssertionError('Native geometry persistence mismatch')
    report.update(status='passed',artifact_sha256=digest,active_path=actual,bbox_mm=bbox,volume_mm3=volume,count=1)
    report['observation']=dict(source_kind='native_reopen',status='measured',property='volume_mm3',object_identity='unique-solid-at-[0,0,0,7,11,13]-mm',observation_ref='reopen-01/report.json',artifact_sha256=digest,value=volume)
except:
    report['error']=traceback.format_exc()
finally:
    with open(REPORT,'wb') as stream:
        stream.write(json.dumps(report,indent=2,allow_nan=False).encode('utf-8'))
print(report['status'])
