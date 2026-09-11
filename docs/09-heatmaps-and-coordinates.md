# 09 — Heatmaps and coordinate encoding

> Initial research: wt-heatmaps by maxsupermanhd (flexcoral), 2026-07-02. https://github.com/maxsupermanhd/wt-heatmaps
> Contributors: wrpl-inspector by maxsupermanhd (carve and ingest); War-Thunder-Datamine by gszabi99.

This section covers the coordinate math that turns a world position into a map
position, and a trajectory-compression codec for that data.

For the map itself and the height of the ground, see
[07-terrain-and-maps.md](07-terrain-and-maps.md). For the live source of world
positions, see [04-localhost-8111-api.md](04-localhost-8111-api.md) and
[03-replays.md](03-replays.md).

## World coordinates

The game uses a right-hand world in meters. A position has three axes:

- `x` runs west to east.
- `z` runs south to north.
- `y` is the height above sea level.

A tank map is flat, so a heatmap uses `x` and `z` only. It uses `y` for the
height of the ground.

## Per-level map extents

Each level names two boxes in world meters. The datamine holds them in the
level `.blkx` file. The `levelcoords` package reads these four fields:

```
mapCoord0      [x, z]   air map corner 0, in meters
mapCoord1      [x, z]   air map corner 1, in meters
tankMapCoord0  [x, z]   tank map corner 0, in meters
tankMapCoord1  [x, z]   tank map corner 1, in meters
```

A heatmap tool without a local copy can fetch this `.blkx` from the public
datamine mirror at
`https://raw.githubusercontent.com/gszabi99/War-Thunder-Datamine/refs/heads/master/aces.vromfs.bin_u/<level>.blkx`.

The tank map corners give the world box that the tank minimap covers. The air
map corners give the larger box that the air minimap covers.

## World to map transform

The heatmap paints a world position as a fraction of the tank map view. The
view grows down, so the `z` axis flips. `levelcoords.TankMapAreaToWorld`
inverts this transform. The inverse is:

```
originX = tankMapCoord0.x - 0.5
originZ = tankMapCoord0.z + 0.5
areaW   = abs(tankMapCoord0.x - tankMapCoord1.x)
areaH   = abs(tankMapCoord0.z - tankMapCoord1.z)

worldX  = originX + fracX      * areaW
worldZ  = originZ + (1 - fracZ) * areaH
```

`fracX` and `fracZ` are the view fractions from 0 to 1. The code clamps a
fraction outside 0 to 1 to the edge.

The 8111 API and the replay give normalized map coordinates from 0 to 1 for
some fields. Multiply a normalized coordinate by the map extents to get world
meters. Section 07 gives the full map-coordinate rules.

## Trajectory codec (coordencode)

A delta-and-varint codec packs a list of timed positions to a small byte
stream. A `SpaceTime` sample holds a `uint32` time in milliseconds and three
`float64` axes `X`, `Y`, `Z`.

The encode step does the following:

1. Round each axis to 1/16 meter. Multiply by 16. Round to the nearest whole
   number. This is 4-bit fixed point.
2. Take the delta of each axis and of the time against the previous sample.
3. Skip a sample when all three axis deltas are zero.
4. Write one version byte set to 0.
5. Write the sample count as a little-endian `uint64`.
6. Write four channels one after the other: time, then `X`, then `Y`, then `Z`.

Each channel is a run of variable-length integers. The time channel uses
unsigned varints. The three axis channels use signed varints. The channels are
separate, so like values sit together and pack well.

The decode step reverses this: it reads the version byte, the count, then the
four channels in order, sums each delta run, and divides each axis by 16 to get
meters back.

This codec is the `coordencode` package of
[wt-heatmaps](https://github.com/maxsupermanhd/wt-heatmaps), the Go server that
stores kill events per level and paints a heatmap over the level minimap.

A carve step in the same spirit as this codec turns a replay into kills, damage,
entities, and players. It is in
[wrpl-inspector](https://github.com/maxsupermanhd/wrpl-inspector).
