# Fixed camera path — diagram only

This draft starts at Emerald Corner and repeats the same 1–77 grouped camera checks, covering all 86 original spawn spots. It does not change the app or send game input.

- Numbered circles: inspect the selected gameplay camera view for a gem.
- Pink dots: original spawn coordinates.
- B1–B16: intermediate camera clicks to bridge offscreen gaps. Close/reopen the map to recenter; do not spend a gem inspection on these points.
- R1: intermediate return camera click after check 77, before restarting at 1.

The model uses the existing 12.45 pixels/tile default-zoom atlas and an inferred reopened camera centre of (285,530) in the 570×1029 reference screenshot. Each consecutive click, including B/R, is checked against the existing clickable map bounds and legend exclusion. B/R points use bundled playable terrain and avoid the known Loong Haven IV portal hit box. All 77 grouped checks and all 86 original spots are included exactly once per pass.

This is a candidate order found by a reproducible route heuristic, not a proven minimum. A gem-only direct chain is disconnected under this viewport model, including isolated Forsaken Lotus Pond and Frosted Plain targets. Additional camera selections can connect the draft without dragging in the model.

Actual recentering, edge clamping, selectable ground, other map icons and account-specific locked regions have not been tested in the game. Locked-area skipping may require different connecting clicks. The route must be checked on fresh screenshots before it is integrated into live input. No real-world speed improvement has been measured.

The PNG is full resolution; the SVG remains sharp when zoomed. Hover over a marker in the SVG to see its camera coordinates and original spawn members. The CSV lists the fixed check order and preceding bridge clicks; route.json includes the full geometry and assumptions.

plan.py and draw.py are the exact one-off analysis/rendering scripts used in the cloud workspace. Their paths refer to that workspace. Application code and release packages are unchanged.
