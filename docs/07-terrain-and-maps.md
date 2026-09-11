# 07 - Terrain and Maps

> Initial research: FURRO404, the initial 3D replay viewer and terrain decode. https://github.com/FURRO404
> Contributors: DagorEngine by Gaijin Entertainment (the landmesh source); wt-heatmaps by maxsupermanhd (coordinate math); War-Thunder-Datamine by gszabi99; Dagor-Asset-Explorer by Gredwitch (DBLD tags).

This document is a decode reference for War Thunder terrain, level props, terrain
color, coordinate systems, and the level catalog. The team reconstructs terrain
and props from the level `.bin` file. The team does not estimate color from the
map image.

The block framing, the codec names, and the coordinate math come from a
terrain extraction pipeline and from the DagorEngine source. Keep the exact
offsets and codec names in this file.

Read these related documents:

- [`02-file-formats.md`](02-file-formats.md) covers the `.blk`/`.blkx` and
  `vromfs` containers that hold level and mission data.
- [`04-localhost-8111-api.md`](04-localhost-8111-api.md) covers the localhost
  `8111` map API and the normalized map coordinates.
- [`08-vehicles-and-models.md`](08-vehicles-and-models.md) covers vehicle models
  and the shared model geometry pipeline.
- [`09-heatmaps-and-coordinates.md`](09-heatmaps-and-coordinates.md) covers the
  heatmap product and the position sample encoding.

---

## 1. Heightmap decode

A level `.bin` file is a Dagor `DBLD3x64` container. It holds two terrain
heightfields:

- The `HM2` block holds a fine heightmap for the 4 km battle crop.
- The `lmap` block holds a LandRayTracer dump for the whole level.

### 1.1 The Oodle (ooz/Kraken) codec

Both heightfields compress their payload with the Oodle Kraken codec. The team
decodes it on Linux with the vendored `ooz_linux` tool. The Dagor block header
marks the codec in its top two bits. Flag value `2` means OODLE (Kraken). Flag
value `1` means ZSTD.

The `HM2` payload is a raw Kraken stream. It has no size prefix. To decode it,
prepend an 8-byte little-endian `uint64` that holds the decompressed size, then
run `ooz_linux -d -f in out`.

The `RIGz` prop stream and the `dxp` texture stream use a different framing. See
section 2.

### 1.2 The HM2 block (battle crop)

The 4 km playable tank area uses a Dagor `HM2` `CompressedHeightmap`. Find the
`HM2` literal in the file. The header starts at `tag_offset+3`, because the NUL
of the 4-character tag overlaps the first byte of `cell`.

```
HM2 header (little-endian, starts at tag_offset+3):
  float32  cell          cell size in metres
  float32  hMin          minimum world height
  float32  hScale        height scale
  float32  ofsX          world X offset of the grid origin
  float32  ofsY          world Z offset of the grid origin
  int32    width  | (version << 24)
  int32    height | (mirror  << 31)
  int32[4] exclude bounding box
  int32    chunkSz       (present only when version == 2)

  chunkSz = 0x403 (Rheinland):
    block_shift = chunkSz & 0xFF          = 3
    hrb_subsz   = 1 << ((chunkSz>>8) & 0xF) = 16
    loadData chunk_sz = chunkSz & ~0xFFF  = 0  -> single block

Then one Dagor beginBlock frame:
  int32   (flags << 30) | len30    flags 2=OODLE, 1=ZSTD
  byte[len]  Kraken payload (raw, no size prefix)
```

Compute the decompressed size, prepend it, and decode with `ooz_linux`. For a
2048x2048 map with `block_shift=3` and `hrb_subsz=16` the size is 4543824 bytes:

```
size = ((bw*bh*(4+64)) + 0xF & ~0xF) + sHierGridOffsets[log2(w/hrb_subsz)] * 16
```

Reconstruct the `uint16` heightmap from the decompressed buffer:

```
Buffer layout:
  BlockInfo   : per 8x8 block, u16 mn, u16 delta
  variance    : per block, 64 u8 (cumulative-delta per block, u8 wrap)
  htRangeBlocks : ignore

Per cell:
  raw_u16 = (delta == 0) ? mn : mn + (v*delta + 127) // 255
  cells are row-major   cy*8 + cx
  blocks are row-major  by*bw + bx

World height:
  worldY = hMin + raw_u16 * hScale / 65535
```

The extractor reads `<WT>/levels/<stem>.bin`, decodes the single Oodle block,
reconstructs the 2048x2048 `uint16` grid, converts to metres, and downsamples by
2 to 1024x1024. It writes:

- `<stem>.f32`: row-major `float32` heights in metres, Z rows by X columns.
- `<stem>.json`: world extent, grid dimensions, `cellW`, `hMin`, `hScale`,
  `yMin`, `yMax`.

Verified: the terrain height matches the recorded tank height to about 0.03 m on
HM2 maps.

Limit: the decoder handles single-Oodle-chunk maps only (`chunkSz=0x403`). It
does not handle multi-chunk HM2 yet.

### 1.3 The LandRayTracer full-map heightfield

The `HM2` crop covers about 4 km. The level `.bin` also holds a LandRayTracer
dump inside the `lmap` (LandMeshManager) block. This dump covers the whole map.
Its per-sub-cell `gridHt` array is the terrain maximum-height field. The team
validated it against the HM2 area to mean -0.12 m and standard deviation 0.24 m.
The two fields share the replay/Dagor world frame with no flips.

```
Container path (all little-endian):
  Find the lmap tag. The dump starts at the following lndm magic.

  lndm header:
    char[4] "lndm"
    int32   ver = 4
    float32 gridCellSize
    float32 landCellSize
    int32[2] mapSize
    int32[2] origin
    int32    useTile

  baseDataOffset = lndm + 36   (right after useTile)

  Four ints, each RELATIVE to baseDataOffset (not to lndm):
    int32 meshOfs
    int32 detailOfs
    int32 tileDataOfs
    int32 rayTracerOfs

  At baseDataOffset + rayTracerOfs a Dagor beginBlock frame starts.
  The u32 header is the 4 bytes BEFORE that point (rayTracerOfs == tell()+4):
    fmt = (hdr >> 30) & 3     2=OODLE, 1=ZSTD
    len =  hdr & 0x3FFFFFFF
  For OODLE: the next u32 at block-data start is src_sz (decompressed size),
  then an Oodle stream of len-4 bytes.
```

To decode the Oodle case, prepend `<u64 src_sz>` and run `ooz_linux -d -f in
out`. This matches the HM2 convention.

```
Decompressed dump:
  int32   dump_sz
  char[6] "LTdump"
  int32   numCellsX
  int32   numCellsY
  float32 cellSize
  Point3  ofs   (3 float)
  BBox3   box   (6 float)
  Six Dagor writeTabs, each [int32 count][count x elem], packed, no padding:
    cellsD      64 B each
    grid        u32
    gridHt      f32   <- heights
    allFaces    u16
    allVerts    8 B
    faceIndices u16
```

```
LandRayCellD (64 B):
  vec4f ofs            (16)
  vec4f scale          (16)
  f32   maxHt
  u32   gridHtStart
  u32   gridStart
  u32   fistart_gridsize
  u32   facesStart
  u32   vertsStart
  u32   _resv[2]

  gridSize = fistart_gridsize & 1023   (8..32 -> 256..64 m/texel; 0 = empty)

Height query:
  px = X - ofs.x;  pz = Z - ofs.z
  cx = floor(px / cellSize);  cz = floor(pz / cellSize)
  ci = cx + cz * numCellsX
  g  = gridSize[ci]
  gx = floor(frac_x * g);  gy = floor(frac_z * g)
  height = gridHt[gridHtStart[ci] + gx + gy*g]
```

The `gridHt` value is the sub-cell maximum terrain height. It is a ray-cull
bound. It sits about 10 m above the true surface. The sentinel `-FLT_MAX` marks
an empty sub-cell. `LandRayTracer` is `BaseLandRayTracer<uint16,uint16>`.

The extractor decodes the `gridHt` field and writes `<stem>_full.{f32,json}` at
1024x1024. It fills holes (empty cells and the HM2 band) by an iterative
4-neighbour mean.

### 1.4 How HM2 relates to the full field

The `HM2` crop is fine. The LandRay field is coarse and covers the whole level.
The server attaches the full field as `terrain.full` when HM2 also exists. The
server serves the full field as the primary terrain when HM2 is absent
(LandRay-only levels).

The viewer blends the HM2 crop into the full field over 1.5 km. The blend hides
the seam where the finer HM2 surface meets the coarse LandRay maximum-height
field (a 5 m to 80 m step). This gives real heights to the far terrain under
aircraft. The empty diagonal band of LandRay cells is where the fine HM2 field
takes over.

LandRay-only levels include:

- `arcade_norway_fjords`: +/-16384 m, 32 m/texel.
- `arcade_phiphi_crater`: +/-16384 m, 32 m/texel, 7 landclasses.
- `kursk`: +/-32768 m, 64 m/texel, 7 landclasses, about 241k props.

Source of truth: DagorEngine `prog/gameLibs/landMesh/` (landRayTracer.cpp,
lmeshManager.cpp loadDump) and `prog/engine/ioSys/baseIo.cpp`. The DAE
`dbld.py` `lmap_add`/`ltdu` path is dead code. Its offsets are wrong. Use the
engine source for this block.

---

## 2. Props and rendinsts

Static props are buildings, trees, vehicles as scenery, debris, fences, and
rocks. War Thunder stores them as rendinsts in the level `.bin` under the `RIGz`
tag. The same `ooz_linux` Kraken decoder reads them.

### 2.1 The RIGz block

Scan for the `RIGz` literal. Validate the next `CompressedData` header, because
the first literal match is a false positive.

```
CompressedData header:
  u24 size
  u8  method     0x80 = Oodle, 0x40 = zstd
```

An Oodle `CompressedData` block has a 4-byte uncompressed-size prefix before the
Kraken stream. This differs from the raw HM2 stream. `ooz_linux` decodes it. The
team prepends the size as a `u64`.

After the tag there are up to 2 layers. Each layer is a `CompressedData`. Layer 0
decompresses to the `RendInstGenData` dump (about 7.0 MB for Rheinland).
Immediately after layer 0 there is `[int32 size][riDataRel block]`, which holds
the per-cell compressed instance streams.

### 2.2 Grid header and pool descriptors

The `RendInstGenData` dump holds the grid parameters and the pool table.

| Field | Description |
|---|---|
| `cellNumW` | grid width (32 Rheinland, 64 Sinai) |
| `cellSz` | cell size in grid units (256 Rheinland, 128 Sinai) |
| `grid2world` | grid-to-world scale (8.0 Rheinland, 16 Sinai) |
| `world0` | world origin (-32768 Rheinland, -65536 Sinai) |
| `perInstDataDwords` | extra per-instance seed dwords (1 for Rheinland) |
| `pregenEnt` tab | pool descriptors |

```
PregenEntPoolDesc (32 B):
  riRes                ptr
  riName               ptr -> asset name
  colPair              8 B
  flags                u32
  paletteRotationCount i32

Flags:
  posInst         =  flags & 1
  paletteRotation = (flags >> 1) & 1
  zeroInstSeeds   = (flags >> 2) & 1
```

`posInst==0` marks a building with a full transform. `posInst==1` marks a tree
with position and palette only. Read the flags raw from the dump at descriptor
`ofs + 24`, because DAE drops bit 2.

### 2.3 Per-cell instance stream

The DAE `getCellEntities` function is wrong for current War Thunder files.
Decode the per-cell stream directly.

- The counter table holds `(poolIdx:u32, count:u32)` pairs, not bit-packed
  counters. The `PregEntCounter.structSize=8` value is the hint. For sub-cell
  `i`, iterate `range(entCnt[i], entCnt[i+1], 2)` to read `pool, count`.
- Cell origin: `(g2w*x*cellSz + world0x, htMin, g2w*z*cellSz + world0z)`.
- Height delta: `htDelta = cell.htDelta or 0x2000`.
- Scale vector: `v482 = (cxz/32767, htDelta/32767, cxz/32767)`, where
  `cxz = cellSz * grid2world`.

```
Matrix instance (posInst == 0), 24 B base:
  int16 mat[12]         3x4 row-major (3 basis rows + 1 translation short per row)
  world pos = cellOrigin + (mat[3], mat[7], mat[11]) * v482
  3x3 basis = 9 non-translation shorts / 256

Pos instance (posInst == 1, trees), 8 B base:
  int16 pos[4]          x, y, z, palette
  world pos = cellOrigin + pos * v482
```

The seed stride is per-pool. When `zeroInstSeeds` is CLEAR, the stream adds
`perInstDataDwords*4` seed bytes after each instance, so the stride is 28 B or
12 B. When bit 2 is SET, there is no seed, so the stride is 24 B or 8 B.

The extractor writes `<level>_instances.{json,bin}`:

- `.bin`: packed `<12f` per instance = `(x, y, z, m00..m22)` in game metres,
  row-major. Trees get an identity basis.
- `.json`: grid parameters and `pools:[{name, posInst, count, byteOffset,
  byteLength}]`.

Counts: Rheinland 38254 instances / 488 pools. Sinai 27593 / 407.

The decoded `(x, y, z)` are game-world metres. They share the frame of the
terrain mesh and the replay entities. See section 4. The tree palette Y-rotation
is not decoded yet, so trees use an identity basis.

For pool geometry and textures see [`08-vehicles-and-models.md`](08-vehicles-and-models.md).
The pool name maps to a game resource pack (`*.grp`), and the model textures
come from `*.dxp.bin` packs.

### 2.4 Dynamic composits (airfield dynaf)

Air maps do not bake the airfield into the level `.bin`. A mission places a
`dynaf_*` composit (a dynamic airfield) through an `objectGroups` node. The node
holds a `unit_class` equal to the composit name and a world transform `tm`.

For Korea (the "38th Parallel" mission) the mission file is
`gamedata/missions/cta/tournament/korea_3_cap_jets_ad.blk`. The composit is
`gamedata/objectgroups/dynaf_korea_2k.blk` at world (16716, 106, 8729), yaw
152.5 degrees.

Only the red airfield is decodable, because it is the single `dynaf` composit in
the mission. The blue runway is baked into the static level texture, so there is
nothing to extract for blue.

The composit holds 659 nodes:

- 657 placeable nodes (buildings, hangars, towers, and 585
  `airfield_flight_light_*` nodes).
- 1 `++` helper box (skip it).
- 1 `^^` baked mesh `^^dynaf_korea_2k_mesh` (the runway surface).

The runway mesh is engine-generated at runtime from the `airfield` block rect
(start, end, width). It is not a shipped asset. The team reproduces it as a flat
quad from the decoded rect (Korea: width 210 m, length about 2080 m). The team
applies the shipped `asphalt_a_tex_d` texture, because the surface is
engine-generated.

The extractor composes the world transform as `placement_TM * node_TM` for every
node. It uses the same position-plus-row-major-3x3 layout as section 2.3. It
merges the airfield into `korea_instances.{json,bin}` as new pools. It dedups by
a position bounding box, so the real coastal port stays put.

The terrain flatten step belongs to the terrain extractor, which is the single
writer of `korea_full.f32`. It flattens an oriented box sized to the decoded
instance footprint down to the runway plane Y with a smoothstep blend. Without
the flatten step the coarse LandRay surface buries the flat runway.

---

## 3. Terrain albedo

War Thunder textures the terrain with the Dagor indexed-landclass biome system.
It does not use the map image. The team bakes a real albedo from this system.
The runtime viewer shader tiles the biome textures over the map.

### 3.1 The indexed landclass chain

The chain lives in the `lmap` block landclass `MetaDataBlock` at `detailDataOfs`.

```
loadLandClasses = beginBlock:
  int32 landClassCount
  per landclass:
    beginBlock
    readString name (u16 length prefix)
    embedded flat BLK, or an external gameres reference
```

The biome landclass is the one whose BLK shader equals
`landmesh_indexed_landclass`. Its BLK gives:

- `landClassTextures/indices`: the biome INDEX texture name (for example
  `avg_egypt_sinai_detailed_biome_tex_b`, 4096x4096, 1 byte per texel, fourcc
  `0x32` raw). Read the bytes after the 128-byte DDS header.
- A `details` block with the material defs. Each def has param0 `albedo` =
  `biome_detail_<name>_tex_d` and param1 `reflectance` = `_tex_r`.
- One `scheme` block, then 65 ordered `detail` entries.

```
Resolve a biome index value V to an albedo texture:
  V -> detail entry V
  detail entry has tex_a / tex_b params = name-map indices (mask val & 0x7FFFFFFF)
  name-map index -> material def -> albedo texture
```

Validated on Sinai: `V=4` (dominant) maps to `sand_dune_b`; `V=22` maps to
`rock_chunks_b`. The desert layout is correct.

Parse the flat binary BLK with a flat-BLK parser, because the DAE parser is
wrong for this variant.

```
Flat BLK layout:
  u8   fmt (0)
  VLQ  v0, v1, namesCount, namesDataSize
  bytes[namesDataSize]  NUL-separated names
  VLQ  blocksCount, paramsCount, dataSize
  bytes[dataSize]       paramsData pool
  paramsCount x 8-byte params:
    u32 flags
    u32 val
    nameId = flags & 0xFFFFFF   (no -1 for params)
    type   = flags >> 24        1=string@paramsData[val], 2/3=int,
                                 4=float bits, 9=bool
  per-block descriptors:
    VLQ nameId-1, pcount, bcount, (firstChild if bcount)
  params are concatenated in block order; block0 is the root.
```

### 3.2 World mapping and tiling

The biome index does not span the whole map. It covers `size.x` metres and tiles
(repeats). Dagor calls this "mega detail". The authoritative source is
DagorEngine `prog/gameLibs/landMesh/shaders/biomes.dshl` (`getBiomeIndices`) and
`lmeshLandClasses.cpp`.

```
Biome index UV (repeat-wrapped):
  tc = world.xz * mulOffset.xy + mulOffset.zw

Sinai: size = (4096, 4096) -> tile = 1/4096, 1 texel per metre.
The index repeats every 4096 m. The Z axis is flipped (mul.y and mul.w negative).

  mulOffset = [ tile,
               -tile,
                offx*tile + 0.5/indexW,
              -(offy*tile + 0.5/indexW) ]
  offx = -blkOffset.x - originX * landCellSize
```

The root `size` and `offset` are BLK type `0x04` (Point2). The `val` field is an
offset into `paramsData`. They are not floats. If you read them as float you get
0, which stretches the index over the whole map at the wrong scale.

The detail grain tiles by `landClassParams.detailMul1/2` (Sinai about
6.17/6.29 tiles per metre). The detail UV is `world.xz * detailMul`. The blend
is a 4-neighbour bilinear over the index.

The old baked `_albedo.png` path is superseded, because a single bake cannot
stay sharp over the map. The runtime viewer material tiles the textures.

### 3.3 LC_MEGA splatting

City and field materials that a simple landclass cannot cover use LC_MEGA
splatting. The extractor reads the `splattingmap`, the per-channel detail
textures, the tile sizes, and the per-cell `DetailMap`. It exports the splatting
map as an RGB blend-weight PNG and 4 detail albedo textures (R/G/B/K channels).
It computes the world-to-splatting UV transform (`mulOffset`). The viewer
implements the Dagor `get_mega()` fragment shader.

The `DetailMap` section holds 7-byte landclass IDs per cell (32x32 cells at
2048 m each). The blend-weight PNGs pack 4 class weights per RGBA texture. The
slot budget is 12 across up to three atlas PNGs. The parser merges duplicate
landclass entries, so a real class does not fall past the last slot.

---

## 4. Coordinate systems

### 4.1 World metres

The game world uses right-handed metres. The axes are X (east/west), Y (up), and
Z (north/south). The replay entity coordinates equal the Dagor world
coordinates. The decoded terrain heights, the prop positions, and the replay
positions all share this one frame.

### 4.2 The terrain sampling alignment (verified fix)

To sample the HM2 grid at a world position, use the header `ofsX`/`ofsY` and
`cell`. Do not swap or flip any axis.

```
col = (X - ofsX) / cell
row = (Z - ofsZ) / cell
```

This gave a mean error of 0.02 m against the recorded tank Y. The LandRay field
uses its own per-cell origin (section 1.3) in the same frame. A tank level spans
4096x4096 m in world coordinates (0..4096). The playable sub-region is a crop
inside that span.

### 4.3 Normalized 0..1 map coordinates

The localhost `8111` map API and the replay data use normalized map coordinates
in the range 0..1. See [`04-localhost-8111-api.md`](04-localhost-8111-api.md) for
the API fields. The map extent comes from the level catalog `map_coords` (section
5.2):

```
map_coords:
  mapCoord0 = [minX, minZ]     world metres, one map corner
  mapCoord1 = [maxX, maxZ]     world metres, the opposite corner
```

For `air_afghan` the extent is `mapCoord0 = [-65536, -65536]` and
`mapCoord1 = [65536, 65536]`.

### 4.4 The transform between world and normalized

Convert a normalized coordinate `t` in 0..1 to world metres:

```
worldX = mapCoord0.x + t.x * (mapCoord1.x - mapCoord0.x)
worldZ = mapCoord0.y + t.y * (mapCoord1.y - mapCoord0.y)
```

Convert world metres back to a normalized coordinate:

```
t.x = (worldX - mapCoord0.x) / (mapCoord1.x - mapCoord0.x)
t.y = (worldZ - mapCoord0.y) / (mapCoord1.y - mapCoord0.y)
```

Check the axis sign for the map image, because the image origin can differ from
the world origin. See [`09-heatmaps-and-coordinates.md`](09-heatmaps-and-coordinates.md)
for the heatmap pixel mapping.

### 4.5 The position sample encoding

A position time series encodes with a delta-and-varint codec. A sample is
`(Time uint32, X, Y, Z float64)` in world metres. The encoder:

1. converts each coordinate to fixed point with 4-bit precision (multiply by 16,
   round to the nearest integer);
2. writes the per-channel deltas of T, X, Y, Z as varints, and skips a sample
   when X, Y, and Z deltas are all 0;
3. writes 1 version byte set to 0;
4. writes the sample count as `uint64` little-endian;
5. writes the T, X, Y, Z channels in order.

The decoder reads the version byte, reads the sample count, then reads the four
channels back to `float64` by a running sum divided by 16.

See [`09-heatmaps-and-coordinates.md`](09-heatmaps-and-coordinates.md) for the
full codec detail.

---

## 5. The level catalog

### 5.1 Level naming

A level key is the Gaijin internal codename. It is the stem of the level path.
The path is `levels/<stem>.bin`. The key often looks nothing like the display
name. Examples: `avg_syria` is "Middle East", `avg_greece` is "Attica", `krymsk`
is "Kuban".

War Thunder reuses a location name across unrelated levels. "Vietnam" is both
`air_vietnam` (a 131 km air map) and `avg_vietnam_hills` (a coastal tank map).
Resolve every level by its stem, not by its display name. A ground level and a
plane-only level often share one display name, for example `avg_berlin` and
`berlin`.

### 5.2 Catalog schema

The catalog ships in this repository at
[`data/level_catalog.json`](https://github.com/FURRO404/WT_KNOWLEDGE_DOCS/blob/master/data/level_catalog.json). A build step reads the
datamine and writes it. The catalog has four top-level maps:

```
level_catalog.json:
  levels               map: level key -> level entry
  by_mission_path      map: mission .blk path -> level key
  by_name              map: display name -> [level key, ...]
  by_localized_name    map: localized name -> [level key, ...]
```

```
level entry:
  level_path        "levels/<stem>.bin"
  names             map: language -> localized level name
  name_key          localization key, e.g. "location/air_afghan"
  name_exact        bool
  level_def:
    present         bool
    map_coords:
      mapCoord0     [minX, minZ]   world metres (see section 4.3)
      mapCoord1     [maxX, maxZ]
    water_level     float
    average_ground_level  float or null
    custom_level_tank_map float or null
    custom_level_map      float or null
  mission_counts    map: branch -> count, plus "total"
  missions:
    <branch>:                     e.g. "tanks", "planes", "helicopters"
      <mission key>:
        mission_path  "gamedata/missions/.../<key>.blk"
        names         map: language -> localized mission name
        loc_keys      list of localization keys tried
        type          game mode, e.g. "domination"
        postfix       mission postfix, or null
        environment   e.g. "Day"
        weather       e.g. "hazy"
        allowed_unit_types  {isAirplanesAllowed, isTanksAllowed,
                             isShipsAllowed, isHelicoptersAllowed}
        use_alternative_map_coord  bool or null
        difficulties  list, e.g. ["realistic", "hardcore"]
        capture_areas [{name, type, x, z, radius}, ...]
        battle_areas  [{name, type, x, z, radius}, ...]
```

The `map_coords` block is empty for a level that defines no map extent (a test
or utility level). The build reads the datamine, so the file tracks the game
version. The current copy holds 170 levels (153 with localized names) and 1056
missions, built from datamine 2.58.0.24.

Use `by_mission_path` to map a replay mission to a level. Use `by_name` and
`by_localized_name` to map a display name to a level key.

---

## Repository status

- The raw-format decode notes in this file stay accurate; verify a file/line
  claim against the current engine source before you assert it as fact.
