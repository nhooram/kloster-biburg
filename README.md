# Klosterkirche Maria Immaculata, Biburg (Lkr. Kelheim)

A printable 1:250 model of the Romanesque former abbey church of Biburg, built from the official Bavarian LoD2 building data, a camera-solved photograph, two drone videos and close-up photos. It covers the church only; the convent buildings are left out. The low sacristy annex north of the north tower is included by default, and there's a church-only variant. The model is fully parametric: one Blender script builds it, and every print file is regenerated from that script.

![South-west view](docs/img/hero_sw.jpg)

| | |
|---|---|
| ![South-east](docs/img/hero_se.jpg) | ![North-east with sacristy](docs/img/hero_ne.jpg) |
| ![North-west](docs/img/hero_nw.jpg) | ![Roof plan](docs/img/top.jpg) |

---

## 1. Print files

All files are STL in mm at 1:250. Every one is watertight, a single body (checked by `tools/export_all.sh`), and sits on a 0.8 m (3.2 mm) plinth.

| File | Size X × Y × Z (mm) | Solid volume | Triangles | What it is |
|---|---|---|---|---|
| `export/KlosterkircheBiburg_1-250.stl` | 195.7 × 108.1 × 158.0 | 944.7 cm³ | 28 914 | **Master**, one piece: sacristy, tower balls and crosses |
| `export/KlosterkircheBiburg_1-250_no-finials.stl` | 195.7 × 108.1 × 150.0 | 944.6 cm³ | 28 108 | Same without balls and crosses (for brass-wire crosses) |
| `export/KlosterkircheBiburg_1-250_no-sacristy.stl` | 195.7 × 102.0 × 158.0 | 920.6 cm³ | 28 870 | Church only, no sacristy annex |
| `export/split/` (12 files) | see §4 | | | **Colour split**: stone body, red roofs, copper helms and apse cones |
| `export/split_no-sacristy/` (11 files) | | | | Colour split, church only |

These are solid volumes; the filament used depends on your infill and wall settings. The model is sized for FDM with a 0.4 mm nozzle. The finest features are the copper standing seams: triangular ridges 0.48 × 0.32 mm with no overhang. All undersides flatter than 45° are either fillets or chamfers, so it prints without supports.

### Variants

| Master | Church only (`SACRISTY=False`) |
|---|---|
| ![](docs/img/var_master.jpg) | ![](docs/img/var_no-sacristy.jpg) |
| **With finials** | **No finials (`FINIALS=False`)** |
| ![](docs/img/var_finials.jpg) | ![](docs/img/var_no-finials.jpg) |

Without the sacristy, the north side gets the mirror of the south side's side-choir window and tower-foot window. With it, those openings are hidden behind the annex, so they're left out.

---

## 2. Details

| | | |
|---|---|---|
| ![Belfry](docs/img/cu_belfry.jpg) | ![West portal](docs/img/cu_portal.jpg) | ![West gable](docs/img/cu_westgable.jpg) |
| Belfry: coupled arcades with colonnettes and impost blocks. The upper storey sits in a rectangular blind field; string courses. | West portal: stepped jambs, ¾ columns with bases and capitals, impost band, two roll mouldings, dentil archivolt, lintel, tympanum relief. | West gable: cross opening, three oculi with recessed rings, stepped arched corbel frieze. |
| ![Apses](docs/img/cu_apse.jpg) | ![Aisle shoulder](docs/img/cu_shoulder.jpg) | ![Sacristy](docs/img/cu_sacristy.jpg) |
| Apses: arched corbel tables with 45° undersides, splayed windows, copper cones with standing seams. | West front shoulder: its own 0.9 m roof strip, 2.5° flatter than the aisle roof and stepping down onto it. Roofs have bell-cast eaves. | Sacristy: L-plan with an angled north-west wall, hip roof, chimney, windows and doors, taken from drone frames. |

Roof modelling: the red roofs and the helms flatten to 60% of their pitch over the last 1.2 m at the eave (bell-cast). The same curve is applied to the roof top, its underside and the wall top, so the roof keeps an even 0.3 m (1.2 mm) thickness through the curve. Where a roof underside is flatter than 45° (aisles, sacristy), a 45° stone fillet fills the space between the eave and the wall so the eave prints without support.

---

## 3. Accuracy analysis

### 3.1 Sources

| Source | Used for |
|---|---|
| **LoD2 CityGML** (Bayerische Vermessungsverwaltung, tile 708_5408, building `DEBY_LOD2_5717218`), in `refs/lod2/` | Footprint, wall planes, ridge and eave heights of nave, transept, choir and aisles, apse radii, tower plan, sacristy footprint and roof |
| **2020 photo** `refs/photos/2020_St_Maria_Biburg.jpg`, camera solved by PnP (`tools/pnp_check.py`) | Tower eave, helm and cross heights; window x positions; west gable decoration; portal position |
| **Close-up photos** (Wikimedia Commons, category *Maria Immaculata (Biburg)*), in `refs/photos/` | Portal, belfry arcades, corbel friezes, apse windows, embrasures |
| **Two drone videos** (frames every 2 s in `refs/frames/`) | Roof layout, west front shoulders, sacristy windows, doors and chimney, north side openings |

The model's frame has the nave axis along x, with y = 0 on the axis, z = 0 at ground, and the west facade at x = −27.46. The real axis runs 17.85° north of east. `refs/lod2/church_local.json` keeps the LoD2 tile's local origin, which is 1.5 m off in y. The comparisons below shift the LoD2 data by −1.5 m in y.

### 3.2 Plan vs. LoD2

![Plan comparison](docs/img/cmp_plan.png)

| | LoD2 ground surface | Model section at z = 1.5 m |
|---|---|---|
| Footprint area | 880.0 m² | 875.5 m² |
| Intersection over union | | **0.984** |
| Symmetric difference | | 14.2 m² |

The outline follows LoD2 all round, including the stepped portal projection on the west front, the niche in the north aisle wall, the transept arms, the three apses and the sacristy with its angled corner. The 14 m² residual is spread thinly along the whole outline; no single part is shifted.

### 3.3 Heights vs. LoD2

![Elevations](docs/img/cmp_elevations.png)

Grey is the model's silhouette; blue lines are the LoD2 surfaces. Top-surface heights at matching plan points (`docs/img/metrics.json`):

| Point | LoD2 roof | Model top | Δ | Why |
|---|---|---|---|---|
| Nave ridge | 20.85 | 21.16 | +0.31 | Roof slab thickness (see below) |
| Nave roof, mid-slope | 17.77 | 18.08 | +0.31 | Same |
| Transept ridge | 20.81 | 21.16 | +0.35 | Same |
| Choir ridge | 20.67 | 21.16 | +0.49 | Same, plus LoD2's choir ridge sits 0.2 m low |
| Aisle roof, middle | 8.71 | 9.11 | +0.40 | Same, plus the bell-cast curve |
| Sacristy roof | 7.30 | 7.69 | +0.39 | Same |
| Main apse cone, near tip | 13.92 | 16.00 | +2.1 | **Deliberate**: LoD2's cones are too flat. All three cones are set to 50°, per the photos. |
| South side apse cone | 8.71 | 10.27 | +1.6 | **Deliberate**: 50° cone, and the eaves are raised from 7.45 to 8.3 m (the photos show them taller relative to the main apse) |
| Tower tops | pyramid, eaves 23.4, apex 39.2 | eaves 28.8, helm apex 36.7, cross 38.7 | | LoD2's tower pyramid is wrong; the tower heights come from the photo fit (§3.4) |

**Known systematic offset**: LoD2's ridge and eave heights are the outer roof surface. The model uses them as the top of the walls and the roof underside, then adds its 0.3 m slab on top. So every red roof stands about 0.3 m (1.2 mm at 1:250) higher than the LoD2 surface. Walls, eaves lines and footprint are unaffected. It could be fixed by lowering the roof slabs by `ROOF_T`, but that hasn't been done.

### 3.4 Photo overlay (solved camera)

![Photo vs. model from the solved camera](docs/img/cmp_photo2020.jpg)

The camera of the 2020 photo was solved from 11 LoD2 corners, with a mean reprojection error of 15 px on a 1920 px image. The camera stands about 1.5 m above ground, 30 m from the south-west corner. The right half is the model rendered from that camera, tinted over the photo with its outline in red (`tools/match_render.py`).

The gable, the nave and aisle roof lines, the west front shoulders, the transept and the window rows all line up. The towers are where the model departs from the photo:

- The photo fit gives tower eaves at 27.2–28.6 m, helm apex at 35.0–35.7 m and the cross at about 37.9 m.
- The model uses eaves at 28.8 m, helm apex at 36.7 m and the cross top at 38.7 m. The helms and crosses therefore reach slightly above the photo, which the overlay shows.
- The reason is the belfry layout. With a lower band at 20.3 m, two identical storeys, and a nearly square upper panel with an even 0.9 m margin, the eaves come out at 28.8 m. Wikipedia gives the towers as "36 m".
- The towers may also sit about 0.5 m east of reality. That's a residual in the overlay, within the fit error.

![Outline only](docs/img/cmp_photo2020_outline.jpg)

### 3.5 Drone frames (qualitative)

These viewpoints were picked by hand, not solved, so they're only for comparing shapes.

![Drone east](docs/img/cmp_drone_e.jpg)
![Drone south](docs/img/cmp_drone_s.jpg)

---

## 4. Colour split

![Exploded, south-west](docs/img/split_exploded.jpg)
![Exploded, north-east](docs/img/split_exploded_ne.jpg)

The colour split has 12 pieces: the stone body, five red roofs plus the sacristy roof, two copper helms and three copper apse cones.

How it's built:

- Every piece drops straight down onto the body and rests on sloped seats.
- The body is the master's own boolean pipeline with the roof and copper parts left out (`tools/split_parts.py`).
- Each piece is its parts minus the body minus wall blockers.
- Each helm has a square socket that fits over a peg on the tower top, and keeps a flat bottom to print on.
- **Print orientation:**
  - Copper pieces (helms, apse cones) print upright on a flat bottom. The clearance pass trims the eave lip that hung below the seat (0.8 mm on the helms, 0.2 mm on the cones).
  - The main roof prints upside down on its ridges. The nave, transept and choir ridges are cut flat in one plane, 0.84 mm down, which leaves a 1.2 mm (0.3 m, about a ridge-tile course) wide strip. That gives 324 mm² on the bed. Set it with `RIDGE_FLAT_MM` in `clearance.py`.
  - These trims are split-only; the one-piece prints keep the sharp ridge and eave lips.
- The 45° eave fillets stay on the body. In the split build (`SPLIT=True`) they stop 1 cm below the roof underside, so the roof pieces keep a solid underside.

**Clearance** (`tools/clearance.py`): runs offline with manifold3d, always on a fresh `split_parts.py` output, because the ridge cut isn't idempotent. Each piece is carved against the body shifted 0.2 mm in ±x, ±y and −z. Every contact that isn't a resting seat gets a 0.2 mm gap: vertical sliding faces, the peg sockets, and anything the body overhangs. The gap is in mm, so it holds at any scale. Use `clearance.py 0.3` for a looser FDM fit or `0.1` for resin.

![Split sections](docs/img/split_sections.png)

The sections through the finished STLs show the aisle eave on its fillet, the nave eave over the clerestory wall, and the south helm on its peg (0.2 mm on every side and on top).

| Piece | Size (mm) | Volume (cm³) | Settle (mm) |
|---|---|---|---|
| body_stone | 195.7 × 108.1 × 121.6 | 912.67 | |
| roof_main_red | 172.3 × 96.4 × 26.3 | 8.29 | 0.00 |
| roof_aisle_S_red / _N_red | 106.2 × 18.6 × 14.1 | 2.17 each | 0.08 |
| roof_sidechoir_S_red | 6.1 × 19.2 × 23.3 | 0.11 | 0.18 |
| roof_sidechoir_N_red | 5.6 × 16.6 × 20.5 | 0.09 | 0.20 |
| roof_sacristy_red | 38.3 × 26.4 × 15.8 | 0.78 | 0.00 |
| helm_S_copper / _N_copper | 27.8 × 21.7 × 40.6 | 5.85 each | 0.00 |
| apse_main_copper | 16.8 × 33.9 × 20.0 | 2.92 | 0.00 |
| apse_S_copper / _N_copper | 8.2 × 16.7 × 9.4 | 0.32 each | 0.00 |

*Settle* is how far a piece drops, when lowered onto the body, before its first down-facing face touches. A seat that isn't horizontal loses a little height to the sideways clearance carve. The aisle roofs therefore settle 0.08 mm and the small side-choir roofs 0.2 mm, which is invisible once assembled.

`tools/fit_check.py` checks every contact with the body and sorts it into a resting seat, a vertical face with zero gap, or an undercut:

- **Undercuts:** none on the roofs and helms. The apse cones show 1–3.5 mm² at the eave ring, where the cone sits on the corbel table.
- **Zero-gap vertical faces:** none larger than 15 mm² anywhere.

---

## 5. Rebuilding

The model is driven from Blender 5.2 through the Blender MCP add-on's socket (port 9876). `tools/bl.py` sends a script to it; the protocol is `{"type":"execute","code":..,"strict_json":..}` followed by a NUL byte.

```sh
python3 tools/bl.py blender/build_church.py      # build the master in the open Blender scene
./tools/export_all.sh                           # all variants + both splits + clearance + validation (26 files)
./tools/make_docs.sh                            # README figures in docs/img + docs/img/metrics.json
```

Variant switches go in front of the script, e.g. `{ echo 'SACRISTY=False'; cat blender/build_church.py; } | python3 tools/bl.py`. The switches are:

- `SACRISTY` (default True)
- `FINIALS` (default True)
- `SPLIT` (default False; set by `split_parts.py`)

All dimensions are constants at the top of `blender/build_church.py`.

| Path | |
|---|---|
| `blender/build_church.py` | Parametric generator: exact booleans (union of parts, then cutters, then details) |
| `blender/kloster_biburg.blend` | Saved scene of the default master |
| `tools/export_stl.py` | Bakes the booleans, checks manifoldness and writes the STL (`SCALE=`, `SUFFIX=`) |
| `tools/split_parts.py`, `tools/clearance.py`, `tools/fit_check.py` | Colour split, its assembly clearance, and the contact report |
| `tools/pnp_check.py` | Camera solve of the 2020 photo from LoD2 corners; back-solves the tower heights |
| `tools/match_render.py`, `tools/render_views.py`, `tools/render_exploded.py` | Renders from the solved camera, named views, and the exploded split |
| `tools/doc_plots.py` | Offline comparisons: plan and elevations vs. LoD2, photo overlay, split sections, metrics |
| `refs/` | LoD2 (`lod2/`), photos, drone videos and frames |
| `analysis/` | Earlier photo overlays and crops used while modelling, and the solved camera (`cam2020.json`) |
| `renders/` | Working renders from the modelling sessions |

---

## 6. Known simplifications and deviations

- The red roofs are about 0.3 m above the LoD2 roof surface (§3.3).
- The towers are 0.2–1.6 m taller than the photo fit, chosen from the belfry layout (§3.4). They may also sit about 0.5 m east of reality.
- The tower plan is kept at LoD2's 6.0 × 4.6 m, although some photos make it look squarer.
- The portal's structure is modelled, but not the carving on its capitals and impost.
- These are left out: the tower sawtooth friezes, the lion corbels at the gable feet, sculptures, and the figure at the west gable apex.
- There's one clock, on the south face of the south tower (the one the photos show).
- In the one-piece prints, the fillet under the west shoulder strip ends 10 cm (0.4 mm) short of the aisle roof, leaving a tiny bridge under that eave.
