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
see [07-terrain-and-maps.md](07-terrain-and-maps.md). For replays that name
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
content-addressed DDSx blobs with no name manifest. The cached-skin recovery
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
