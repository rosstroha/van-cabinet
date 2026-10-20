# Van cabinet concept

Review the first layout in [front and interior layout](concept/layout.png), [CAD perspective](concept/isometric.svg), [moving-part preview](concept/review.png) and [front drawing](concept/review.svg). The sink is on the left, with removable greywater below. The toilet and independent dog platform are on the right. Full-overlay birch fronts use grouped diagonal rounded vent slots inspired by the bed.

Overall: 30 W x 18 D x 33 H inches. Height is confirmed; depth remains provisional. Width includes the countertop and closed fronts, with 1/8 inch remaining below the maximum. The rear 7/8 inch space clears the specified 5/8 inch C-pillar protrusion. Verify trim, exact pillar position, countertop fit and installation tolerance in the van.

The cabinet rests on its plywood sides, divider and recessed plinth, with no cabinet feet. The toe kick is 3 inches high and recessed 2 inches from the closed fronts. Its right panel clips to the toilet sled and moves with it, concealing the sled rollers when closed.

The lower right door opens independently before a floor-supported toilet sled rolls out 18 inches. Keep the floor path clear and level. The independent dog platform is approximately half the cabinet width, 12 inches deep, on provisional locking slide envelopes. Roller parking restraints, travel latches, hold-downs and actual hinges remain to be selected. Target occupants: 45 lb dog and 200 lb seated person, plus component weights. No safe load rating is established.

[COMPONENTS.md](COMPONENTS.md) records RV component candidates and manufacturer sources. The model reserves a Thetford 335 toilet, COMET 19 L wastewater canister and Dometic VA930 sink. Components are unapproved bounding boxes. Sink overlap with the solid countertop is intentional: no sink cutout has been approved. Final sink, faucet, drain trap, vent, tank port orientation and disconnects require measurement.

The bed adjoins the RIGHT side when viewed from the front. That side and the center divider include aligned provisional 1.5 inch water-line openings, 3 inches from the wall and 24 inches above the floor. The left exterior side has no water-entry hole. The route passes behind the drawers and above the tank. Its position needs checking against bed structure and concealed services. No matching bed hole is specified. Rear mounting rails reserve attachment areas for either permitted mounting method. Measure van structure and use rigid spacers across the rear gap. No attachment drilling pattern is released.

Import `concept/cabinet_stowed.step` or `concept/cabinet_deployed.step` into Fusion 360. They contain separate named solids in millimetres. In the STEP files, x increases right from the left edge, y increases from the front toward the wall, and z increases above the finished floor. Extended parts have negative y coordinates. The `_clearance.step` variants add component bounding boxes. STEP does not preserve a native Fusion parameter timeline. Edit [parameters.json](parameters.json), then rebuild with `.venv/bin/python build_concept.py` to regenerate the design.

Dependencies are listed in [requirements-cad.txt](requirements-cad.txt). For a new environment, create a virtual environment and install those dependencies. All source scripts live in this directory; generated files live in `concept/`.

The panel list and BRep checks establish preliminary geometry and stock-size feasibility only. All panel bounding rectangles fit within a 48 inch CNC width. This is not a nested toolpath or a production cut list: joinery, tool radii, hinge/slide mounting, plywood thickness measurement, crash retention, motion clearances and load validation remain unfinished.

## Browser viewer

Run `npm --prefix viewer start`, then open http://127.0.0.1:8765 to orbit the CAD model, extend the toilet and dog platform, hide panels, and select parts. See [viewer/README.md](viewer/README.md) for controls, rebuild commands and browser verification.
