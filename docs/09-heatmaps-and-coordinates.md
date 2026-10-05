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

### Aircraft attitude in replay tracks

Replay tracks give an aircraft's yaw, pitch and roll in radians for each
position sample. In world axes (`x` east, `y` up, `z` north):

- Nose: `f = (cos p · cos y, sin p, -cos p · sin y)`.
- Wings-level up: `u0 = normalize((0, 1, 0) - f · f.y)`.
- Up with bank: `up = cos r · u0 + sin r · (f × u0)`.

Checks on TSS air-duel tracks:

- The nose lies within 0.5 rad of the flight path in more than 80% of samples
  above 150 m/s. The rest are high angle-of-attack moments in hard turns.
- In every sample with more than 3 G of lift, `up` points along the lift:
  the normal part of `acceleration + g`. The mean cosine is 0.95. With the
  other roll sign, it is -0.07.

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

Aircraft meshes from the game use `+X` nose, `+Y` up, `+Z` right wing.
Example: the F-15A canopy is at `x` +5.1 m, the tail at -5.9 m, and the left
wing at `z` -5.5 m. [verified, 2.58]

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
