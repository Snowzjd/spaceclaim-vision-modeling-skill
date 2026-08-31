# Modeling strategy

1. Require a new unsaved document with zero bodies and new output paths.
2. Construct a transient rectangular prism in an explicit XY plane.
3. Construct a transient central cylinder with a 0.1 mm overlap into the plate and unite it with the plate.
4. Construct four extended transient cylindrical cutters and subtract them.
5. Attach the single closed transient result as one design body.
6. Select the four original vertical plate-corner edges by endpoint location and Z span; apply R10 constant rounds.
7. Re-enumerate the body and validate bounds, volume, name, corner cylinders, support cylinder, and mounting-hole cylinders.
8. Save only after every geometry assertion passes and emit a structured forward report.
9. Close and reopen the native model, then run a separate read-only feature audit.

The script does not infer extra edge treatments. The interpretation that support height is measured above the plate top remains explicit in the requirement and runtime report.
