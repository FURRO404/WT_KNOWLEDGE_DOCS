# 08 — Vehicles and models

> Initial research: FURRO404, vehicle model extraction. https://github.com/FURRO404
> Contributors: Dagor-Asset-Explorer by Gredwitch, 2023-10-28 (model, mesh, and pack formats); DagorEngine by Gaijin Entertainment; War-Thunder-Datamine by gszabi99.

This section covers War Thunder vehicles as 3D data. It covers model formats,
camouflages, the X-ray and damage model, and turret and gun articulation.

The data source is the datamine: static `.blk` files and DagorEngine resource
packs on disk. The data does not change while the game runs.

For armor and penetration that consume the damage model, see
[06-ballistics-and-armor.md](06-ballistics-and-armor.md). For the raw pack and
BLK formats, see [02-file-formats.md](02-file-formats.md). For terrain props,
see [07-terrain-maps-and-missions.md](07-terrain-maps-and-missions.md). For replays that name
which vehicle a player drove, see [03-replays.md](03-replays.md).

---

## 1. Vehicle model formats and extraction

### 1.1 How the game stores models

War Thunder ships every playable vehicle as a DagorEngine **dynamic model**
inside a `.grp` resource pack. A dynamic-model resource carries class id
`0xB4B7D9C4` (`DYN_MODEL_CLASS_ID`). A skeleton carries class id `0x56F81B6D`
(`GEOM_NODE_TREE_CLASS_ID`).

The model extractor decodes these meshes into Wavefront **OBJ** geometry. The
viewer then draws the real vehicle.

Each vehicle class stores its packs in a different place:

| Class | GRP location | Layout |
|---|---|---|
| Tanks | `content/base/res/tanks/*.grp` | ~949 packs. One pack often bundles several variants. `_dmg` and `_xray` variants sit inline. |
| Aircraft | `content/base/res/aircrafts/*.grp` + `content/base/res/aircrafts.grp` | Family packs. One pack holds a whole family. ~400 packs, ~1,600 models. No `_xray`/`_dmg`/`_collision` inline. |
| Helicopters | `content/base/res/heliaircrafts.grp` | One mega-pack at the `res/` root, sibling of `aircrafts.grp`. ~110 models. |
| Ships | `content/base/res/ships/*.grp` + `content/base/res/ships.grp` | 589 packs, plus a root `ships.grp` with 146 more. 873 models. `_dmg`/`_xray`/`_collision` sit inline, like tanks. |

A tank pack bundles several variants. For example `usa_m4a3e8_76w_sherman.grp`
holds `m4a2_76w_sherman`, `m4a3_105_sherman`, and `m4a3e8_76w_sherman`. Extract
every bundled variant, not one per pack.

### 1.2 How a vehicle id becomes a mesh

All four classes resolve the same way: `unit BLK → model resource → GRP`.

1. **Unit to model resource.** Each unit `.blk` names its model resource in a
   `model` param. Read that param. The step is the same for every class. Unit
   BLK locations:
   - Tanks: `gamedata/units/tankmodels/<unit>.blk`
   - Aircraft and helicopters: `gamedata/flightmodels/<unit>.blk`
   - Ships: `gamedata/units/ships/<unit>.blk`
2. **Model resource to GRP.** A cached index maps each model resource to its
   GRP pack, because resources move between packs. Keep one such index per
   class (tanks, aircraft, ships). Rebuild an index with the `--reindex` option
   after a pack-scope change.

The BLK path needs no alias table. A pack-alias table and a resource-alias
table exist, but only replay mode uses them.

The helicopter index must scan both root packs, or every heli model drops:

```python
for name in ("aircrafts.grp", "heliaircrafts.grp"):
    root_grp = AIR_RES_DIR.parent / name
    if root_grp.exists():
        grp_paths.append(root_grp)
```

### 1.3 Two extraction modes

The model extractor has two modes:

- **Replay mode** (pass one replay id). It reads one replay, finds its
  vehicles, and exports them with camo textures. It writes a replay-scoped
  manifest JSON.
- **Bulk mode** (pass the `--all` option). It exports every tank, plane,
  helicopter, and ship, geometry only. It writes a catalog JSON (the bulk
  library index).

Bulk mode skips all texture work. The viewer draws each bulk vehicle as a solid
red or blue mesh, colored by team at render time. Texture resolution was ~60% of
the old script and its most failure-prone part.

### 1.4 Bulk enumeration and dedup

Many units share one mesh. The bulk target step dedups by model resource. On
the air side ~13,124 flightmodel BLKs resolve to ~1,600 meshes. On the tank
side ~2,400 tankmodel BLKs collapse onto fewer resources.

To build the bulk worklist for a class, do three steps:

1. Walk every unit `.blk` key under its prefix. Skip the `weaponpresets/`
   subdir. For ships, skip `debris/` too.
2. Resolve each unit to its model resource. Drop a unit with no `model` param or
   a model that no GRP holds.
3. Dedup by model resource. Produce `unit_id → model_resource` (the
   many-to-one lookup) and `grp_name → [model_resource…]` (the worklist,
   grouped by GRP so each pack opens once).

### 1.5 Parallelism

Mesh decode is CPU-bound on Oodle/zstd decompression. Bulk mode fans out across
a `ProcessPoolExecutor`. It partitions work by GRP, so there is no shared state
and each pack opens once. The per-class worker task shares one shape for tanks,
aircraft, and ships: open the pack once, then loop its targeted resources.

Each worker process must first initialize the DAE loader and repair the
real-resource class map. Run both once per worker, as the executor
`initializer`. The `--jobs` option defaults to `os.cpu_count()`. A full run
takes ~15 to 20 minutes on 16 cores for ~2,300 meshes.

### 1.6 LOD and skeleton

Choose **LOD1** by default (`min(1, lodCount-1)`). LOD0 carries the full vertex
cost. LOD2 and LOD3 often collapse the turret or hull. LOD1 keeps the
silhouette at a fraction of the LOD0 triangle count. Override with the `--lod N`
option.

Bind the model `<resource>_skeleton` geom-node tree (class `0x56F81B6D`)
through `setGeomNodeTree()`. Rigid nodes then land in world space.

Aircraft meshes from the game use `+X` nose, `+Y` up, `+Z` right wing.
Example: the F-15A canopy is at `x` +5.1 m, the tail at -5.9 m, and the left
wing at `z` -5.5 m. [verified, 2.58]

### 1.7 Skinned-object overlay

`Model.getOBJ()` skips every `obj.skinned` object. It has no per-vertex skin
weighting, so it would export at one point. This drops tracks, launcher racks,
and camo nets. To keep them, write a second OBJ (the track overlay) with every
skinned object. Catalog entries reference it under `trackOverlay`. Skinned
objects export in bind pose, which is the visible pose for vehicle attachments.

The overlay excludes these:

- `*_dmg` damage-state variants.
- Effect objects (`isEffectObject()`).
- Sunken bind poses (ground vehicles only). Drop a skinned object whose AABB
  dips more than 0.3 m below ground.
- Bind-pose ammo ribbons. Drop an object when its AABB dips below ground
  (`y_min < −0.05`) or when it is a thin long ribbon (min dimension < 6 cm and
  max dimension > 2 m).

Do not apply the sunken filter to aircraft or ships. On aircraft, `y = 0` is the
fuselage datum. On ships, `y = 0` is the waterline, and the filter would drop
the whole underwater hull.

### 1.8 The fmt-17/32 vertex-format fix

Camo netting used to export as self-intersecting blobs. The cause was a
vertex-format decode bug in Dagor-Asset-Explorer
`MatVData.VertexData.FORMATS[17][32]`. The entry read the position at byte
offset 8, but those bytes hold the bone indices and weights. The verified
32-byte layout is:

```
b0-3   per-byte 00/ff mask        b16-21 position (3 × int16 norm)
b4-7   UV set 0 (2 × int16/4096)  b22-23 const 0x7fff (position w)
b8-11  bone indices (4 × uint8)   b24-27 packed normal
b12-15 bone weights (4 × uint8,   b28-31 UV (2 × int16/4096)
       sum ≈ 255)
```

The corrected entry is `PADDING(16), SHORT_VERTEX(), PADDING(6), SHORT_UV()`.

### 1.9 Naval specifics

Ships are a fourth instance of the tank path:
`gamedata/units/ships/*.blk → res/ships/*.grp`. 706 ship unit BLKs resolve to
629 distinct meshes. The decoder needs no ship-specific change.

Note these naval facts:

- `y = 0` is the waterline. Fuso reaches −9.64 m, Chikugo −6.65 m. Turn the
  ground sunken filter off for ships.
- Ship skinned objects (gun masks, flags, antennas) decode to garbage. Skip the
  `_tracks` overlay for ships. This is a known gap.
- The per-vehicle export step takes an explicit vehicle class (`"ground"` /
  `"air"` / `"naval"`). It drives the sunken filter and the cancelled-pose
  switch (see section 3.6) from that value.
- The ship worker task exports the `_xray`, `_dmg`, and `_collision` resources
  direct from the same GRP.

### 1.10 Output

Bulk mode writes these artifacts:

- One OBJ file per mesh (one mesh per vehicle/model, LOD1, geometry only).
- A catalog JSON (the standalone bulk library index).
- A replay-scoped manifest JSON (replay mode only).

Each mesh file uses the model resource as its key. Resource names normalize
dashes to underscores. The catalog JSON holds these keys:

- `tanks` / `air` / `ships` — one entry per mesh, keyed by resource. Heli
  entries are `air` entries with `grp: heliaircrafts.grp`.
- `tankUnits` / `airUnits` / `shipUnits` — every unit id to its mesh key.
- `rigs` — per-unit articulation limits (see section 4).
- `failures` — per-model decode errors, collected not fatal.

Example catalog entry:

```json
{
  "tanks": {
    "m4a3e8_76w_sherman": {
      "obj": "m4a3e8_76w_sherman.obj",
      "resource": "m4a3e8_76w_sherman",
      "skeleton": "m4a3e8_76w_sherman_skeleton",
      "faces": 12345, "vertices": 6789, "lod": 1, "lodCount": 4
    }
  },
  "tankUnits": { "us_m4a3e8_76w_sherman": "m4a3e8_76w_sherman" }
}
```

Current library (2026-07-27): 1,103 tank meshes, 1,220 air meshes (1,124
planes + 96 helicopters), 627 ship meshes, 8 benign failures. The whole
`models/` tree is ~28 GB after brotli compression.

---

## 2. Camouflages and textures

The camo extractor adds the texture half that bulk model extraction skips. It
walks the catalog tanks and resolves each model's default camo diffuse from the
DXP texture packs.

### 2.1 The base layer and the overlay

The per-vehicle `_c` diffuse is the **unpainted** base layer. It is what a
destroyed wreck shows in game. The in-game paint is a separate tiled camo
overlay texture. The shader blends the overlay over the base, masked by the base
alpha channel. Hull plates read alpha ≈ 1 (painted). Tracks and tools read
alpha ≈ 0. A render of the `_c` alone looks like a dead tank.

### 2.2 Where the textures live

| What | Where |
|---|---|
| HQ per-vehicle packs | `content.hq/hq_tex/res/hq_tex_tanks/<grp-stem>.dxp.bin` (preferred) |
| Base-quality packs | `content/base/res/tanks/<grp-stem>.dxp.bin` (fallback) |
| Common nation camo overlays | `content/base/res/zzz-tq_pack.dxp.bin` + `content/base/res/tanks/gm.dxp.bin` |
| Per-unit skins | `skin` blocks in the unit BLK (`replace_tex` / `set_tex`) |
| Marketplace / live (UGC) skins | `cache/contentUGC/**/*.ddsx` |

Texture names split per part: `<model>_body_c` (diffuse), `_n` (normal), `_ao`
(ambient occlusion), plus `_turret_c` and `_gun_c`. Modern vehicles often ship
one whole-vehicle atlas, for example `challenger_mk_3_c`, with no part split.
Formats are DXT1/DXT5 (BC1/BC3). `DDSLoader` uploads them direct.

A texture pack does not always share the GRP stem. A texture-name to DXP-pack
index maps each texture name to its pack. HQ packs win a collision. Rebuild the
index with the `--reindex` option.

### 2.3 How a mesh gets its textures

`content/base/res/dynModelDesc.bin` is the game material description DB. It holds
15k+ models with exact per-slot diffuse bindings and shader classes. Load it in
each worker during bulk export, so exported OBJs carry real `usemtl` names, for
example `2s1_body_ussr_camo_green`. Key the per-resource material JSON
(`mtl.json`) by the same `model.getMaterialName(i)` call. The two sides agree by
construction.

Shader class drives slot behavior: `masked` → camo overlay, `glass` →
translucent, `atest`/`propeller`/`alpha_blend` → alpha-tested, `weapon_fire` →
hidden effect anchor, `decal` → hidden.

A model absent from the desc falls back to name inference. Vote each material
body/turret/gun by mesh-object name, then pick the `_<part>_c` map. For a
single-atlas vehicle, use the whole-vehicle texture and mark the entry
`"wholeTex": true`.

### 2.4 Output

Per resource, the camo extractor writes:

- A per-resource material JSON (`mtl.json`) — usemtl name to
  `{d, part, usage, decal, inferred}`.
- One DDS per texture — extracted once, deduped.
- A camos JSON — per-resource rows, the `units` map (unit id to default camo),
  `unitSkins`, `repaints`, and a `failures` map.

### 2.5 Skin kinds

There are two `skin` block kinds. They render through different viewer paths:

- **Camo-slot skin.** `replace_tex from=us_camo_olive* to=<camo>*`. It swaps
  the shared camo slot. The `<camo>` texture is a mask-blended overlay. It lands
  in `unitSkins` and renders as `camo:<tex>`.
- **Full-repaint skin.** `replace_tex from=<part>_c* to=<part>_skin_<name>_c*`
  for every part. It is a per-material diffuse replacement, not an overlay. It
  renders through the repaint path as `repaint:<name>`, which sets
  `camoTex=null`. The M1A1 "Kate" is the reference example.

A full-repaint default reads from two BLK sources: a signature `skin` block, or
a `default_skin` block with `set_tex` directives.

### 2.6 The camo overlay blend

The viewer injects the camo through `onBeforeCompile` and replaces the three.js
`map_fragment` chunk:

```glsl
mask  = smoothstep(0.03, 0.30, base.a);   // fresh-paint boost
paint = clamp(camo.rgb * (0.5 + 2.0 * luma(base)), 0.0, 1.0);
rgb   = mix(base.rgb, paint, mask);
```

The base alpha is a paint-wear map, mean ≈ 0.2. A linear mix leaves tanks as
wrecks, so the smoothstep boosts fresh paint. The paint color is the camo
modulated by base luminance detail.

### 2.7 Aircraft and cached skins

Aircraft paint differs from tanks. Every aircraft skin is a full painted
diffuse, with no overlay and no mask. The flightmodel BLK `user_skin` `from`
slot names the default. The `--only air` option wires aircraft and helis.

Downloadable skins are not in any pack. Two caches hold them:
`cache/contentUGC/` (marketplace, for example Maus X-1) and `cache/content/`
(official downloadable camos, for example jet unlockables). Both hold
content-addressed DDSx blobs with no name manifest. The vehicle of a
Marketplace skin is in `aces.vromfs.bin` `config/skins_market.blk`; see
[05 section 4.5](05-char-server-api.md#45-player-cosmetics-and-awards). The cached-skin recovery
step correlates each blob against each aircraft default diffuse by edge-map
cross-correlation, then writes a `cached<N>` repaint. UGC repaints carry
alpha = 0 everywhere, so the overlay blend disables itself on them.

---

## 3. X-ray and damage model

The X-ray shows internal modules, crew, and ammo. The damage model (DM) is the
data source. The aircraft X-ray extractor exports aircraft X-ray in the same
shape the tank pipeline
([06-ballistics-and-armor.md](06-ballistics-and-armor.md)) produces: a per-unit
damage JSON and an X-ray OBJ. The viewer consumes both classes the same way.

### 3.1 Tank armor data

Each tank `DamageParts` child declares `armorClass` and `armorThickness` direct.
The DM data feeds armor thickness into penetration. See
[06-ballistics-and-armor.md](06-ballistics-and-armor.md).

Commander cupola: no tank DM has a part named `cupola`. The cupola armor is the
part `turret_commander_dm` (an armor plate, class CHA or RHA, usually 20 to
100 mm, filed under the `turret`, `mask` or `hull` group). It is in about 565
ground collision models. Do not mix it up with `commander_dm` (the crew member)
or `commander_panoramic_sight_dm` (an optics module).

### 3.2 Aircraft armor data

Aircraft differ from tanks in five ways:

1. **Group name is the armor class.** Aircraft `DamageParts` group by
   armor-class name. The parts carry only `hp` and `genericDamageMult`:

   ```
   DamageParts
     armor10            <- this group name is an armor class
       armor2_dm { hp=40 }
     glass60            <- 60mm bulletproof glass
       armor1_dm { hp=100 }
     steel_pilot        <- pilot back-armor
       pilot_dm { hp=20, fireProtectionHp=20 }
     c_dural7           <- composite: 90% dural + 10% dural7
       fuse_dm { hp=44.5 }
   ```

   Class definitions resolve in `gamedata/flightmodels/dm/armorclasses.blk`
   (347 classes), NOT the tank file. Resolve a composite class to a
   probability-weighted `armorThickness` plus a `compositeMembers` map. The
   extractor synthesizes a pseudo-part per group in `partsByName`.

2. **No per-vehicle damage resources in the family GRPs.** Aircraft family GRPs
   hold only `<model>`, `_anim`, `_animtree`, `_char`, `_skeleton`. There is no
   dmg mesh, so the Armor mode stays disabled. The reader must assemble the
   X-ray.

3. **Real X-ray meshes exist for ~220 modern jets and helicopters only.** The
   dynmodel and its skeleton ship in different packs. The `<model>_xray`
   dynmodel sits in `res/aircraft_xray.grp` and the per-nation
   `*aircraft_xray.grp` packs. The `<model>_xray_skeleton` GeomNodeTree sits in
   the `*aircraft_logic.grp` packs. Attach the skeleton with `setGeomNodeTree()`
   before `getModel()`. Xray node rotations include a y↔z swap (det −1), so
   derive face winding from the total transform determinant.

4. **WW2 props have no real internal meshes anywhere.** The extractor
   synthesizes stand-ins: engines shaped from the FM
   (`gamedata/flightmodels/fm/<fmFile>.blk`), guns as a breech box plus barrel,
   and real seated pilot figures from `res/pilots.grp`. The pilot into-OBJ
   transform is `(x, y, z) → (−z, y−0.25, −x)` with winding reversed (det −1).

5. **Positions come from the plane skeleton and emitter aliases.** Resolve a
   part position in this order: the exact node `<part>_dm` or `<part>`; then
   aliases (`pilotN`, `emtr_fuel<N>` for `tank<N>`, `emtr_oil<N>` for oil
   coolers, `emtr_water<N>` for water radiators, `emtr_shellrejection<N>` for
   cowl guns, `cockpit`); then skip.

### 3.3 Collision hulls

Collision ships for aircraft in the `*aircraft_logic.grp` packs. There are 1,247
`<model>_collision` resources, and every one of the 1,557 air units resolves
one. The payload is the same `0xACE50001`-zstd node format that tanks use. The
collision-mesh parser reads it unchanged. Nodes are named exactly `<part>_dm`,
one convex hull per DM part.

Newer tank collision resources use a different class, `0xACE50003`. Its name
table is positional and correct: each 48-byte node record holds its own name
offset, the names equal the `dm_skeleton` node set (less `root`), and each
record's local bounding box equals the bounding box of its paired mesh. But one
node mesh can hold many DM plates. On a modern hull (tested on the M1A1 HC), the
node count fell and the triangle count rose against the older `0xACE50001`
file, and one node (`turret_02_top_dm`) covers most of the hull shell. Plates
such as `body_front_dm` and `superstructure_*` then have no node of their own.
The 16-bit value after each BVH leaf is a triangle edge-active mask, not a part
id. It holds 3 bits per triangle (up to 4 triangles per leaf, low triangle
first), and the top 4 bits are 0. Bit e is the edge from vertex e to vertex
e+1. A bit is set when the edge is a mesh boundary or a concave edge with a
dihedral angle above about 4 to 5 degrees. It is clear on flat and convex
edges. The resource holds no other per-triangle table, so a merged node mesh
carries no plate id. Do not assume that a node name names the plate under the
hit. Recover the plate from the layer geometry (thickness and position) or from
a live capture.

Each node also carries `CollisionNode` behaviour flags: the u16 at `+6` of the
node's 8-byte meta entry, which is also the u16 at `+8` of its 48-byte record.
The flags are TRACEABLE 0x1, PHYS_COLLIDABLE 0x2, SOLID 0x4, then
FLAG_ALLOW_HOLE, FLAG_DAMAGE_REQUIRED, FLAG_CUT_REQUIRED, FLAG_CHECK_SIDE,
FLAG_ALLOW_BULLET_DECAL and FLAG_ALLOW_SPLASH_HOLE. The order comes from the
client's enum name table. SOLID decides if a hit on the node is charged from
the mesh chord (see `06-ballistics-and-armor.md` section 4.6). On a T-80UE1,
the hull front layers are 0x7 and most other nodes are 0x3.

**Axis handedness.** Collision node vertices (after the node transform) are in
the game's native frame. A visual or X-ray mesh exported to OBJ through the DAE
`getOBJ()` path has z negated. So a raw collision export is the mirror image of
the visual model on z: on the M1A1 HC, `track_l_dm` sits at z = +1.32 in the
collision data, while the visual `wheel_l_*` sits at z = −1.36. To overlay the
two, negate the collision z and reverse its triangle winding. The winding
reversal keeps the native facing: tank collision meshes are wound inward
(negative signed volume).

### 3.4 How the X-ray OBJ is assembled

Assemble per unit, in this order. A later step skips a part base an earlier step
covered:

1. Real X-ray dynmodel objects, posed by the dedicated X-ray skeleton.
2. Base-mesh copies of `armor_*` and `radiator*` render objects.
3. Collision hulls for DM parts the earlier steps missed. Object names get a
   `_hull` suffix. Exclude crew, so the seated figure in step 4 wins. Hulls are
   authored with the opposite face orientation, so do not run them through the
   usual winding reversal.
4. Stand-ins for whatever remains. Object names get a `_standin` suffix.

The JSON carries `hasRealXray`, `hasCollisionHulls`, `collisionHulls`,
`standins`, `partsByName`, `armorClasses`, and `objectPartMap`.

### 3.5 Weapon loadouts

The loadout extractor reads the unit BLK `WeaponSlots` block. Each
`WeaponSlot` holds `WeaponPreset`s. Each preset lists `ShowNodes` (pylon and
rail meshes baked into the base model, hidden by default) and
`Weapon { blk, emitter }`, where `emitter` names the skeleton node the ordnance
hangs from. Each weapon BLK carries a `mesh` param naming the ordnance
dynmodel. Output is a per-unit loadout JSON.

### 3.6 Cancelled-pose rigids

Tanks and planes need opposite handling. A ground vehicle renders a
cancelled-pose node untransformed. An aircraft applies the wtm to it. Use a
per-class switch: untransformed for ground, apply the wtm for aircraft. The
per-vehicle export step sets it from the vehicle class.

---

## 4. Turret traverse and gun elevation

The primary gun barrel and turret angles come from two datamine sources, joined
per unit.

### 4.1 The two data sources

- **Unit BLK.** `gamedata/units/tankmodels/<unit>.blk` carries the primary
  weapon under `commonWeapons`. It gives the bone names, the slew rates, and the
  elevation limits:

  ```
  [commonWeapons][Weapon] trigger='gunner0'
    [turret]  head='bone_turret'  gun='bone_gun'  barrel='bone_gun_barrel'
    speedYaw = 40.0    speedPitch = 40.0
    [limits]      yaw=(-180,180)   pitch=(-9,20)
    [limitsTable] lim1=(-180,-105, 3,20)
                  lim2=(-105, 105,-9,20)
                  lim3=( 105, 180, 3,20)
  ```

  `limitsTable` rows are `(yawMin, yawMax, pitchMin, pitchMax)`. They model the
  hull-clearance depression limit over the engine deck. Select the `Weapon`
  whose `trigger` is `gunner0`. Otherwise select the first `Weapon` that has a
  `[turret]` block and whose `blk` is not `dummy_weapon.blk`. Seven vehicles
  name a mount other than `bone_turret`/`bone_gun`, for example the M113.

- **Skeleton.** The `<resource>_skeleton` GeomNodeTree gives the node
  hierarchy and the pivot origins. Node names match OBJ group names exactly,
  because `realres.py::getOBJ` calls `skeleton.getNodeByName(obj.name)`. Model
  +X is forward, +Y is up. Traverse rotates about Y at the head-bone origin.
  Elevation rotates about the lateral axis at the gun-bone origin.

### 4.2 Articulation math

Turret traverse and gun elevation reduce to a small set of angle operations on
top of the two data sources above, all in degrees:

- Normalize an accumulated heading to `(-180, 180]` before comparing it against
  a limit or slewing toward it — a turret that has spun three revolutions
  arrives near 1080 degrees.
- Clamp traverse to the yaw arc from `[limits]`.
- For a unit with a `limitsTable`, select the band whose yaw range contains the
  current yaw and clamp pitch to that band's range; fall back to the flat
  `[limits]` pitch arc when the unit has no table.
- Slew toward a target at no more than `rate * dt`, taking the shortest arc.

The turret is driven from `aimYaw`/`aimPitch`, which arrive as world-absolute
radians. The target turret yaw is `wrapAngle(aimYaw - hullHeading)`. The target
gun pitch is `aimPitch`, because ground hulls render flat. The recorded track is
the sight ray, not the gun, so it must still be clamped to the unit's limits: a
Leopard 2A4 elevates to +20 while the track reaches +50.

Articulation does not apply to aircraft, ships, or secondary turrets — a replay
records one aim direction per entity.

## 5. Battle rating

The battle rating (BR) is in `char.vromfs.bin/config/wpcost.blk`, one block per
unit id: `BR = economicRank / 3 + 1`, rounded to one decimal. Each mode has its
own key: `economicRankArcade` (AB), `economicRankHistorical` (RB) and
`economicRankSimulation` (SB). The plain `economicRank` key is not a mode BR.
Example: `us_m47_patton_II` has `economicRankHistorical` 19 (BR 7.3).
[verified, 2.58]

- Aircraft have a second set of keys for ground battles with aircraft (SQB,
  ground RB): `economicRankTankHistorical` and `economicRankTankSimulation`.
  Use them before `economicRankHistorical`. Example: `f_16c_block_50` has
  `economicRankHistorical` 38 (BR 13.7) but `economicRankTankHistorical` 35
  (BR 12.7). [verified, 2.58]
- A few aircraft (43 in the 2026-10 datamine, all jets near BR 9) also have
  keys for naval battles: `economicRankShipArcade` and
  `economicRankShipHistorical`. There is no ship simulator key. All of them
  have the value 25 (BR 9.3). Example: `f3h-2` has AB 9.3, RB 9.0, SB 9.3,
  ground 8.7 and naval 9.3. [verified, 2026-10 datamine]
- The ground keys exist on 521 aircraft. Ground battles have no arcade key
  for aircraft.
- The vehicle card writes the BR of the current mode, then the BRs of the
  other battle types that differ, in brackets and split by `" | "`, each after
  its unit-type glyph: `6.0 (▮ 6.3)`. It does not show a ship BR in simulator
  mode. The glyphs are text keys in `lang.vromfs.bin/lang/*.csv` that the
  game's symbol font (`symbols_skyquake.ttf`) draws: `icon/unittype/aircraft`
  `▭` (U+25AD), `tank` `▮` (U+25AE), `ship` `┚` (U+251A), `boat` `⋛`
  (U+22DB), `helicopter` `⋡` (U+22E1), `human` `╞` (U+255E).
  [read, `gui.vromfs.bin/scripts/airInfo.nut`, 2026-10 datamine]
- Some aircraft unit files have no `wpcost.blk` block at all. These are AI,
  tutorial and event units (for example `dummy_plane`, `fau-1`, `ju-52`,
  `spitfire_ix_tutorial`), not planes that a player can fly. A missing block
  is a simple filter for them. [verified, 2026-10 datamine]
- Every unit block in `wpcost.blk` has at least one `economicRank*` key. A
  lookup fails only when the unit id is wrong. Some ids are not the short
  name: the M1A2 SEP is `us_m1a2_sep_abrams` and the 2S6 is `ussr_zprk_2s6`.
  [verified, 2.58]
- The vehicle ids of the TSS tournament site are the same unit ids. All 245
  ids in six sampled tournaments were in `wpcost.blk`. See
  [10-sre-tss-api-info.md](10-sre-tss-api-info.md). [verified, 2.58]
- `wpcost.blk` holds only the BR of its patch. For a BR at an earlier date, read
  the `char.vromfs.bin` of that patch.

## 5a. Unit type tags (`unittags.blk`)

Each unit in `unittags.blk` carries a set of tags. The `type_*` tags give
the role, and the plain tags `air`, `aircraft`, `tank`, `helicopter`,
`ship` and `boat` give the class.

- `type_assault` is the attacker (ground-attack) aircraft class. It is
  never on a ground vehicle. Examples: Ayit (`a_4n`), Yak-130
  (`yak_130_early`). These units usually also carry
  `type_strike_aircraft`, but `type_assault` comes first in the tag order.
- Do not map `type_assault` to a tank role. If a classifier takes the
  first `type_*` tag it finds, a wrong `type_assault` entry wins over
  `type_strike_aircraft`.
- In one cache of about 3,000 units, 253 units carried `type_assault`.
  All 253 had `air` and none had `tank`. No unit had both `aircraft` and
  `tank`.
- Ground role tags: `type_light_tank`, `type_medium_tank`,
  `type_heavy_tank`, `type_tank_destroyer`, `type_spaa`,
  `type_missile_tank`, `type_football_tank`.

## 5b. Display names (`lang/units.csv`)

The display name of a unit is in `lang/units.csv` in `lang.vromfs.bin`.
The key is `<id>_shop` (the research tree name). The tanks that were
examined also have `<id>_0` and `<id>_1` with the same name, and `<id>_2`
with the class name, for example `MBT`.

- The game's own name can differ between two copies of the same vehicle
  in different nations. The Swedish `sw_t_80u` is `T 80 U` (spaces), but
  the Soviet `ussr_t_80u` is `T-80U`. Show the name from the table. Do not
  "correct" it. [verified, lang.vromfs.bin, Oct 2026]
- Names can carry decoration glyphs: country markers (`▄`, `▀`), event and
  premium markers (`◊`), and Private Use Area characters. A renderer whose
  font cannot draw them must strip them.

## 6. Aircraft flight model data

### 6.1 Where it is

The unit BLK `gamedata/flightmodels/<unit>.blk` names its flight model in the
`fmFile` param, for example `fm/f_5a.blk`. The flight model is
`gamedata/flightmodels/fm/<name>.blk`. Many units share one file: the F-5C
uses `fm/f_5a.blk`. [verified, 2.58]

There are two layouts:

- **Older layout.** `Areas` (wing panels `WingLeftIn` ... in m², `Fuselage`,
  `Stabilizer`, `Keel`), `Wingspan`, `Mass.WingCritOverload` (`[neg, pos]` in
  N), and `Aerodynamics` with `lineClCoeff` (lift slope per degree),
  `OswaldsEfficiencyNumber`, Mach multiplier sets 1 to 7, and polars
  `NoFlaps` / `FullFlaps` (`Cl0`, `alphaCritHigh`, `ClCritHigh`, `CdMin`).
- **Newer layout.** `Aerodynamics.WingPlane` holds `Span`, `Areas`,
  `FlapsPolar0` / `FlapsPolar1` (the same polar keys) and
  `Strength { CritOverload [neg, pos] N, VNE, MNE }`. `FuselagePlane`,
  `HorStabPlane` and `VerStabPlane` have their own polars.
  [verified, 2.58]

Engine data is in `EngineType0.Main`. The count of `Engine<N>` blocks gives the
engine count.

- `Type` (`Jet` for jets), `Thrust`, `AfterburnerBoost`.
- `ThrustMax` table: `Altitude_i` (m), `Velocity_j` (km/h, `VelocityType`
  `TAS`), `ThrustMaxCoeff_i_j` (dry) and `ThrAftMaxCoeff_i_j` (afterburner).
- `Mode0` ... `Mode5`: throttle position to `ThrustMult`. `Mode5` is
  `Throttle` 1.1 (afterburner).

`Passport` holds hangar-style performance: `Alt.maxSpeedWep` `[[alt_m, km/h]]`,
`Alt.minTurnTimeWep` `[alt_m, s]`, `IAS.maxRollRateLeft` `[[ias_kmh, deg/s]]`.
[verified, 2.58]

### 6.2 Template values for modern jets

For many jets the `Main.Thrust` and `Passport` values in the client files are
a template, not the aircraft's real performance:

- `EngineType0.Main.Thrust` is `2200` in 71 of 371 jet flight models and
  `2600` in 91 of them, for example the F-5C, F-16A, F-15A and MiG-29 9-12.
  The real F-16A engine gives about 6,500 kgf dry.
- The F-16A and F-15A `Passport` blocks are copies of the F-5 values
  (`maxSpeedWep` starts `[0, 1150.09]`).
- The live `aces.vromfs.bin` and the newer
  `cache/binary.<version>/aces.vromfs.bin` hold the same values.

The real dry thrust is in `EngineType0.Main.ThrustMax.ThrustMax0` (kgf for
each engine, static, sea level). All 371 jet flight models have it. It
matches the real engines: F-16A 6490, Su-27 7680, F-104G 4490, J-7E 4100.
`ThrustMaxCoeff_i_j` scales it by altitude and TAS. [verified, 2.58]

The client calculates the jet thrust as follows. [read, Linux client 2.58]

```
dry  = ThrustMax0 × 9.81 × ThrustMaxCoeff(alt, TAS)        (N, bilinear)
mult = ThrustMult(rpm / RPMMax)                            (Mode table)
ab   = AfterburnerBoost × ThrAftMaxCoeff(alt, TAS)         (bilinear)
thrust = dry × mult × (ab if the afterburner is on) × engine count
```

- The `Mode<N>` table maps `Throttle` to a target `RPM` fraction, and the RPM
  fraction to `ThrustMult`. The table key is the shaft speed as a fraction of
  `RPMMax` (the loader stores `RPMMax × π/30`), not the throttle. The usual
  jet table gives `ThrustMult` 1.0 at throttle 1.0 (RPM 0.99) and the `Mode5`
  value at throttle 1.1 (RPM 1.0). [read; the throttle-to-RPM step is a guess]
- The two tables use the same `Altitude_i` (m) and `Velocity_j` (km/h TAS)
  grid. The F-16A static values are 6490 kgf dry and 6490 × 1.26 × 1.1 =
  8995 kgf with the afterburner. `ThrAftMaxCoeff` rises with speed (1.55 at
  1,000 km/h at sea level, up to 4.05 at 12 km), so the static ratio is low
  but the ratio in flight is high.
- The modifications `hp_105_jet` (`thrustMult` 0.945) and
  `new_compressor_jet` (0.96) in `char.vromfs.bin/config/modifications.blk`
  scale `ThrustMax0` as `× (1 + (thrustMult − 1) × k)`. A stock jet is
  probably about 9% weaker than a jet with all modifications. [read; when
  k is 1 is a guess]

The wing polar values (`lineClCoeff`, `ClCritHigh`, `CdMin`, wing areas,
`CritOverload`) differ per jet and look real. [verified, 2.58 and 2.59]

`gamedata/flightmodels/performance/<unit>.blk` (663 files) gives `altSpecs`
per 1,000 m (`maxSpeed`, `optSpeed`, `maxClimb`) for props and early jets
only. [verified, 2.58]

For real performance, use the 8111 API in a test drive (see
[04](04-localhost-8111-api.md)), or fit from replay tracks.

### 6.2a How the client uses a polar

Each lifting surface (`WingPlane` `FlapsPolar0/1`, `FuselagePlane.Polar`,
`HorStabPlane.Polar`, `VerStabPlane.Polar`) is one polar. Angles are in
degrees. [read, Linux client 2.58]

**Flaps.** The client blends `FlapsPolar0` and `FlapsPolar1` by the flap
position: a linear blend for each key, clamped between the two values.

**Mach.** For `MachFactor` 3, each of the seven blocks `<N>` gives a
multiplier m(M):

- below `MachCrit<N>`: the base value (1; 0 for block 6)
- from `MachCrit<N>` to `MachMax<N>`: a cubic with f(MachCrit) = base,
  f′(MachCrit) = 0, f(MachMax) = `MultMachMax<N>`, f′(MachMax) =
  `MultLineCoeff<N>` (the loader solves the 4×4 system)
- above `MachMax<N>`: `MultMachMax + (M − MachMax) × MultLineCoeff`, limited
  by `MultLimit` (a maximum if the slope is positive or zero, a minimum if it
  is negative)

| Block | Scales |
|---|---|
| 1 | `CdMin` |
| 2 | `lineClCoeff` (with `CombinedCl`: × (m1 + 1 − m2) instead of × m2) |
| 3 | `ClCritHigh` and `ClCritLow`: Cl = m3 × (ClCrit − Cl0′) + Cl0 |
| 4 | `alphaCritHigh` and `alphaCritLow` |
| 5 | the induced factor k = 1 / (π × e × span² / area) |
| 6 | an extra term, 0 below `MachCrit6` [use not known] |
| 7 | `Cl0` (Cl0′ = Cl0 × m7) |

The client computes the cubic in float32. It builds the 4×4 matrix
[0, 0, 1, 1; 1, 1, c, mx; 2c, 2mx, c², mx²; 3c², 3mx², c³, mx³] (c =
`MachCrit`, mx = `MachMax`, all float32, c³ in double and rounded once),
inverts it by cofactors in double, and rounds the inverse to float32. The
coefficients are float32 of a dot product with (slope, base, `MultMachMax`),
and the cubic is evaluated in Horner form in float32. The coefficients are
large, so the rounding shows in the result. A singular matrix gives the
cubic 0·M³ + 0·M² + 0·M + base. [verified by emulation of the client code,
2.58]

A wing polar with another `MachFactor` value uses the polar with no Mach
change. A propeller blade polar is different, see 6.2b.

**Lift.** With s = `lineClCoeff` (per degree):

- From α1L to α1H: Cl = Cl0 + s·α.
- α1H = 2 × (ClCritHigh − Cl0) / s − alphaCritHigh. α1L is the same on the
  low side. If α1H < α1L, the two are set to their mean.
- From α1H to `alphaCritHigh`: a parabola, Cl = ClCritHigh − a·(αcrit − α)²,
  with a = (ClCritHigh − Cl0 − s·α1H) / (αcrit − α1H)². It reaches
  `ClCritHigh` at `alphaCritHigh` with zero slope.
- Past the critical angle: a parabola of width `AfterCritParabAngle` down
  to `ClAfterCritHigh × sin(α × π/80)`. It uses `AfterCritDeclineCoeff`,
  `AfterCritMaxDistanceAngle` (at least 40°) and a cosine to 180°.

**Drag.** Cd = CdMin + k × (Cl0 + s·α)². The linear lift is used, not the
stalled lift. Past the critical angle on each side, the client adds
`CxAfterCoeff × (α − αcrit)`. Cd is limited to
`|sin α| × ClCritHigh + 0.15`.

**Instructor limits (data only, rule not read).** The flight model has an
`Instructor` block with `critMult` [2 values], `overloadMult` [4 values],
`overloadTimeRange` and `limitOverload`. The loader stores them at struct
offsets +0xec, +0xf8 and +0x10c. Some unit files (84 in the 2026-10 datamine,
most of them late jets) also have `instructorCritMult` and
`instructorOverloadMult` at the top level, for example [0.8, 0.8] and
[0.6, 0.67, 0.85, 0.92]. These are smaller than the flight model's own
values (often [0.86, 0.86] and [0.85, 0.92, 0.85, 0.92]). A unit value is
probably an override of the flight model value.

A guess, not checked in the game: the instructor G limit is
`overloadMult[1]` × the wing strength G, and the wing strength G is
2 × `CritOverload[1]` / (m·g). For the F-16A at half fuel this gives
0.67 × 14.0 = 9.4 G, near the real F-16 limit of 9 G. The role of the other
values is not known.

**Wing strength per sweep.** A swing wing (`WingPlaneSweep<N>`) has its own
`Strength` block (`CritOverload`, `VNE`, `MNE`) for each sweep position. The
forward position has the lowest limits.

### 6.2b Piston engines and propellers

The rules below were read in the Linux client 2.58 and checked by emulation
of the client functions: 560 propellers and about 690 engines give the same
values. Items marked [guess] are not from the client code.

**Layouts.** A flight model holds its piston engines in one of three forms:

- Type layout: `Transmission<n>` links `Engine<i>.Type` to an `EngineType<k>`
  block and `Propeller<j>.Type` to a `PropellerType<k>` block.
- Inline layout: `Engine<n>` and `Propeller<n>` hold the blocks themselves
  (the engine stub has no `Type` key, and `Propeller<n>.Geometry` has
  `Radius`).
- Old layout: `Engine<n>.Propellor` holds the propeller, with
  `AdvancedPropRadius`, `PropPhi_i` (blade pitch), `PropWidth_i`, `Diameter`,
  `PhiMin`/`PhiMax` and `Reductor`. Each engine has its own transmission.
  The old loader reads the polar with the same function as the new one.
  `ShaftRPMMin`/`ShaftRPMMax` default to the `Propellor` keys
  `GovernorMinParam`/`GovernorMaxParam`, and `RPMAfterburner` defaults to
  `RPMMax`.

Some `Main`, `Compressor` and blade keys are lists in a few files. The first
value is probably the one that the client uses. [guess]

**Supercharger (`Compressor.Type` 1 and 2).** The inlet pressure is
p_in = (p + 0.5 × `SpeedManifoldMultiplier` × ρ × V²) / 101325. The client
picks the best stage from the `Altitude<i>`, `Power<i>`,
`AltitudeConstRPM<i>`, `PowerConstRPM<i>`, `Ceiling<i>` and
`PowerAtCeiling<i>` keys. Below a stage's rated altitude the power factor
is ((1 − p_in) / (1 − p_stage)) × (P − g) + g. When p_in goes above the
stage pressure (ram air at a very high speed), the divisor goes near zero
and the factor becomes very large: the Spitfire IX gives a factor of 276 at
p_in 1.3. This only occurs past the speed limit.

**Turbocharger (`Compressor.Type` 3).** In steady state the turbo speed is
n = min((nmax / x) × boost, nmax), with nmax =
`TurboChargerRPMMaxAllowed`, boost the manifold pressure that the throttle
asks for, and x the manifold pressure without the turbo (p_in × the
compressor RPM term × `ATA` / (k × `Altitude0`)). The meaning of k is not
known. The loader keeps `TurboChargerRPMMin`,
`TurboChargerRPMMaxAllowed`, `TurboChargerRPMMax` (rad/s) and
1 / `TurboChargerTimeConst`.

**Governor.** The engine runs at `GovernorMaxParam` (WEP:
`GovernorAfterburnerParam`). The prop turns at engine ω × the reductor. The
governor sets the blade pitch, between `PitchMin` and `PitchMax`, so that
the prop torque × ω equals the engine power. At a pitch stop the RPM moves
until the two balance. [the pitch-stop rule is a guess]

**Blade element.** The client cuts each blade into four elements at
r = (0.35 + 0.2i) × R, with width `BladeWidth<i>` × R and twist
`BladePitch<i>` (degrees). For each element:

```
tang = r × ω            W² = tang² + va²        phi = atan2(va, tang)
aoa  = pitch + twist − phi                      (degrees for the polar)
f    = width × 0.2R² × W² × ρ/2
T   += Cl·f·ml × tang/W − Cd·f·md × va/W
Q   += r × (Cd·f·md × tang/W + Cl·f·ml × va/W)
```

T and Q are × `NumBlades`. va = V + w/2, with the wake speed w from
momentum: w = √(2T / (ρA) + V²) − V, limited to ±150 m/s, A = π(D/2)².
A wake swirl s = Q / (0.5 × |V + w/2| × ρA × (D/2)²), limited to 0–20,
lowers the blade speed by 0.25 × s. The steady state is a fixed point. A
relaxation of 0.5 for 60 steps converges.

**Blade polar.** A blade polar takes its missing keys from defaults:
`lineClCoeff` 0.075, `Cl0` 0.4, `ClCritHigh` 1.4, `ClCritLow` −0.9,
`alphaCritHigh` 17, `alphaCritLow` −17, `CdMin` 0.012, `MachFactor` 2,
`CombinedCl` true. The aspect ratio for k is
`OswaldsEfficiencyNumber` / (0.2 × Σ width), or 55.5 when the key is
missing. A missing blade Mach key reads as 0, not as the wing default.

The blade Mach number is W / a. By `MachFactor`:

- 1: f = max(|1 − min(M, 0.9)²|^0.3, 0.2). Cd × 1/f, Cl × √(1/f).
- 2: the same, with no 0.9 limit. The blade also uses fixed stall corners
  from a default polar at Mach 0: α1H 9.6667, α1L −17.6667, kh 0.0051136,
  kl −0.0562501.
- 3: the seven Mach blocks of 6.2a.

**Check.** With these rules, the WEP top speed and climb from
`performance/<unit>.blk` `altSpecs` agree at 233 points: top speed median
−0.1% (10th to 90th percentile −3.8% to +8.2%), climb median +0.6%
(−13.7% to +23.7%). The airframe drag model adds part of this error.
[verified, 2.58]

### 6.3 What replay tracks show

Aircraft positions in replays sample at about 4 Hz (about 250 ms). A local
quadratic fit over ±0.8 s gives usable velocity and acceleration. In TSS
realistic and simulator air duels (jets, under about 3 km altitude) the load
factor normal to the flight path has a median of about 4 G and a 97th
percentile of about 10 G. The distribution does not change with a wider fit
window (±1.75 s), so the high values are real pulls, not noise. Top jets
(F-15A, F-16A) show turn rates of 26 to 28 deg/s at the 90th percentile.
[verified, 2026-10 data]

**Angle of attack and gun aim.** The angle between the nose and the flight
path, measured in the lift plane, grows with the load factor and stops at a
limit. In about 700 TSS duels (props and jets together) it stops near 12–14°.
Jets fly up to about 25° at low speed. The angle per g falls fast with speed:
for the F-15A it is about 10.7°/g at 50–75 m/s, 2.9°/g at 125–150 m/s and
0.55°/g at 250 m/s. A prop at high speed can fly a little nose-low, from its
wing incidence.

The guns fire along the nose, not along the flight path. At 1,381 gun hits in
those duels, the lead error of the nose had a median of 1.4–3.3° (by speed
band), and the lead error of the flight path had a median of 4–9°. At the
hits, the shooters flew a median 9.5° angle of attack at only 1.5 g: most gun
hits come from slow jets at high angle of attack. A model that aims along the
flight path misses most real gun solutions. [verified, 2026-10 data]

**Load factor at low speed.** F-15A and F-15J tracks pull a lift load of 1.43 g
at 40–50 m/s, 1.78 g at 50–60 m/s and 2.21 g at 60–70 m/s (97th
percentile). The path turns at most about 23–28°/s at every speed from 40 to
130 m/s. [verified, 2026-10 data]
