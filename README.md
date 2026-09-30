# Klosterkirche Maria Immaculata, Biburg (Lkr. Kelheim)

Printable model of the church only (the convent buildings and the sacristy annex north of the north tower are left out).

## Layout
- `blender/build_church.py` is the parametric generator. All dimensions are constants at the top. Rerun it to rebuild.
- `blender/kloster_biburg.blend` is a saved copy of the scene.
- `export/KlosterkircheBiburg_1-250.stl` is the **master** print file: in mm, watertight, one body, 196 × 102 × 153 mm, with a 0.8 m plinth and tower balls and crosses.
- `export/KlosterkircheBiburg_1-250_no-finials.stl` is the same model without the balls and crosses (145 mm tall), for adding brass-wire crosses. Build it with `FINIALS=False` and export it with `SUFFIX="_no-finials"`.
- `export/split/` is the colour-split print set (from `tools/split_parts.py`): `body_stone` plus five red roofs (main cross-shaped roof, 2 aisles, 2 small side-choir roofs) plus five copper parts (2 tower helms with crosses and a locating peg, 3 apse cones). Each piece drops straight down onto the body and sits on the gable tops. Pieces rest on the sloped seats. Every other contact gets a 0.2 mm gap from `tools/clearance.py`, which runs offline with manifold3d **after** `split_parts.py`. It's in mm, so it holds at any scale: use `clearance.py 0.3` for a loose filament fit or `0.1` for resin. `tools/fit_check.py` measures each piece's contacts as seat, zero-gap vertical or undercut. The preview is `renders/split_exploded.png`.
  Rebuild order: `bl.py blender/build_church.py`, then `bl.py tools/split_parts.py`, then `uv run --with manifold3d --with trimesh python tools/clearance.py`.
- `export/*_no-sacristy.stl` and `export/split_no-sacristy/` are the church-only version, without the low sacristy annex north of the north tower. The default files include the sacristy, whose footprint and roof come from LoD2. With the sacristy removed, the north side gets the mirrored side-choir and tower-foot windows.
- `tools/export_all.sh` rebuilds and exports every variant, applies clearance, and validates all files.
- `tools/bl.py` sends a script to the Blender MCP add-on socket (port 9876, protocol `{"type":"execute","code":..,"strict_json":..}\0`).
- `tools/render_views.py` renders views into `renders/`.
- `tools/match_render.py` renders from a solved photo camera, for overlay checks.
- `tools/pnp_check.py` solves the camera of the 2020 photo from LoD2 corners and back-solves heights.
- `tools/export_stl.py` bakes the booleans, checks manifoldness and writes the STL. Set `SCALE=` before running it for other scales.
- `refs/` holds the sources: `lod2/` (official Bavarian LoD2 CityGML tile 708_5408, building `DEBY_LOD2_5717218`), `photos/` (Wikimedia Commons, category *Maria Immaculata (Biburg)*), `video/` + `frames/` (the two drone videos, frames every 2 s).
- `analysis/` holds the photo overlays and the solved camera.

## Where the numbers come from
- **LoD2 (lidar/cadastre)**: footprint, nave/transept/choir ridge 20.86 m, eaves 14.84 m, aisle lean-tos 10.5 → 7.3 m, apses (r 3.95 m, eaves 11.6 m; side apses r 1.8 m, eaves 7.45 m), tower plan 6.0 × 4.6 m. The building axis is 17.85° north of east.
- **Tower heights**: LoD2's tower pyramids are wrong (eaves 23.4 m, apex 39.2 m, and 39.2 is really the cross). The camera of `2020_St_Maria_Biburg.jpg` was solved against 11 LoD2 corners (15 px mean error, camera 1.5 m above ground). From that fit: eaves 27.2–28.6 m, helm apex 35.0–35.7 m, cross ≈ 37.9 m. Within that range, the eave height (28.8 m) is set by the belfry layout: the lower band is at 20.3 m, the two storeys are identical, and the upper storey's recessed panel on the E/W faces is nearly square with an even 0.9 m wall margin at the sides and top. The helm is 7.9 m, so its apex is at 36.7 m. Wikipedia gives "36 m".
- **Apses**: LoD2's cone tips (13.7 / 9.2 m) are too flat. All three cones are set to 50°, per the photos. The side-apse eaves are raised from 7.45 to 8.3 m, because the photos show them taller relative to the main apse.
- **Window x positions, west gable decoration, portal**: back-projected from the same photo.
- **Details** from close-up photos: splayed window embrasures that slope from the outer arch in to the glass. Arched corbel tables on the west and east gables and the apses: the wall above the arch line projects, the arches are cut back flush with the wall below, and all undersides slope at 45° so they print without supports. Also the cross opening and three oculi with recessed rings in the west gable, coupled belfry arcades on all 4 faces (upper storey in a rectangular blind field), string courses, one clock (south tower, south face), and copper standing seams on the apse cones and tower helms. The red roofs and helms have bell-cast eaves: over the last 1.2 m they flatten to 60% of their pitch. The west front's shoulders over the aisle ends have their own 0.9 m roof strip, 2.5° flatter than the aisle roofs, stepping down onto them. The seams are triangular ridges 0.48 × 0.32 mm at 1:250, so they print without overhang.

## Known simplifications
- The portal is modelled in 3D (stepped jambs, 3/4 columns with bases and capitals, impost band, two roll mouldings, dentil archivolt, lintel, Christ relief, platform step), but the carving on the capitals and impost is not. The tower sawtooth friezes, the lion corbels at the gable feet, sculptures and the figure at the west gable apex are also left out.
- There is one clock, on the S face of the south tower (the one the photos show).
- The towers may sit about 0.5 m east of reality (a residual in the photo overlay, within the fit error).
