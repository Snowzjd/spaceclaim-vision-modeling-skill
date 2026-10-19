# Planning-only request D

Prepare independent MS-03, MS-05, MS-06 and MS-08 results using these inputs.
Do not construct a model, execute an API call or claim any measured geometry.

Target environment: SpaceClaim host 2022 R1 with V21 scripting API and IronPython
2.7. The installed V21 API documentation was read for the following signature
facts (not a live runtime test):

- `SpaceClaim.Api.V21.Modeler.Body.ExtrudeProfile(Profile profile, Double distance)`
  returns a Modeler Body, capped at both ends; profile is a closed planar loop.
- `SpaceClaim.Api.V21.Geometry.CircleProfile(Plane plane, Double radius,
  PointUV location, Double angle)` constructs a circular planar profile.

Source identifiers: `api.extrude` and `api.circle`, V21 local API XML member
names matching these symbols. No documentation binaries or manual content are
part of the public request. These are transcribed signature facts only.

One requested feature: a closed circular material addition with constant section,
diameter 14 mm, axial length 9 mm. Caller supplies a valid planar circle profile
of radius 0.007 m. Distance argument is 0.009 m. Available conceptual methods:

1. `closed-profile-extrusion`: supports one constant closed section using the
   version-bound ExtrudeProfile operation above, creating one capped body.
2. `section-loft`: supports different sections and requires at least two profile
   sections plus matching rules; no such extra sections or binding are supplied.

Select a method for this one feature and separately bind its API call. Do not
claim attachment/union to another body; no target body was supplied.

For an independent selection declaration, target the newly created body's
planar positive-end cap. Accepted geometry places its cylinder axis along +Z,
with end cap at z=9 mm and expected disk radius 7 mm. Expected analytic
properties, not measurements: plane z=9 mm, outward unit normal +Z, area
153.93804002589985 mm^2. Caller tolerances: position 0.001 mm, normal component
0.000001, area 0.001 mm^2. Candidate type is face; zero or multiple matches must
stop. No intervening topology modification and no previous object handle are
present. Declare criteria; do not select a live object.

For an independent assertion declaration, expected volume is
1385.4423602330984 mm^3. Caller-supplied measurement adapter contract:
`read_volume_mm3(body)` returns a finite kernel-measured volume in mm^3 or an
unavailable result. This adapter is supplied as a measurement interface only,
not an independently tested implementation. Absolute tolerance 0.01 mm^3;
unavailable measurement must not pass. Declare one assertion and retain that
evidence boundary.
