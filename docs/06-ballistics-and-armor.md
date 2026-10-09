# 06 - Ballistics and Armor

> Initial research: FURRO404, armor and penetration reverse-engineering. https://github.com/FURRO404
> Contributors: wt_ballistics_calc by the Warthunder-Open-Source-Foundation, 2021-10-26 (drag cross-check); War-Thunder-Datamine by gszabi99.

This file documents War Thunder ground-vehicle ballistics, penetration, and
armor. It states the exact formulas, constants, variable names, and units. It
also states where each number comes from and how sure the number is.

## Scope and sources

These formulas were reverse-engineered from the game binary `linux64/aces` and
validated against live game data.

For the raw BLK fields per shell, see
[02-file-formats.md](02-file-formats.md). For shot and hit events in replays,
see [03-replays.md](03-replays.md). For armor geometry and the x-ray model, see
[08-vehicles-and-models.md](08-vehicles-and-models.md).

Confidence tags in this file:

- **Confirmed**: validated against the binary and against live in-game numbers.
- **Partial**: the BLK field is known, but the game mechanism is not fully
  solved.
- **Not reverse-engineered**: the game uses the field, but no formula was
  recovered.

Do not treat estimated or unsolved items as exact. This file marks each one.

## 1. Shell flight (external ballistics)

### Drag model

War Thunder decays the shell speed with an exponential drag law over range.
The stat-card range columns use the BLK fields directly.

```
V(d) = V0 * exp(-k * d)
k = rho_air * Cx * PI * ballisticCaliber_m^2 / (8 * mass_kg)
rho_air = 1.225
```

Variable definitions:

- `V(d)` is the impact speed in m/s at range `d`.
- `V0` is the BLK field `speed` in m/s (muzzle speed).
- `d` is the range in meters.
- `Cx` is the BLK field `Cx` (drag coefficient).
- `mass_kg` is the BLK field `mass` in kg.
- `ballisticCaliber_m` is the BLK field `ballisticCaliber` in meters. If that
  field is absent, use `caliber`. For APFSDS, this value is the long-rod
  diameter, not the gun caliber. Example: DM53 uses `0.023`, not `0.12`.
- `rho_air` is the air density in kg/m^3. It is a hardcoded constant.

### Constants

| Symbol | Value | Unit | Source |
|---|---|---|---|
| `rho_air` | 1.225 | kg/m^3 | Standard air density; used in the drag law |

### Worked example (BR-412D)

BR-412D uses `mass=15.88`, `caliber=0.1`, `Cx=0.395`, `V0=887`.

```
k = 1.225 * 0.395 * PI * 0.1^2 / (8 * 15.88)
  = 0.0001196582293

V(10)   = 885.94 m/s
V(100)  = 876.45 m/s
V(500)  = 835.49 m/s
V(1000) = 786.97 m/s
V(1500) = 741.26 m/s
V(2000) = 698.22 m/s
```

### Drop

The reverse-engineering notes do not give a separate projectile-drop formula.
The notes cover only the speed-versus-range curve and the penetration curve.
Treat trajectory drop as **not reverse-engineered** here.

### Confidence

The drag model is **Confirmed**. The project reproduced every tested stat-card
range value with no fitting. See the range tables in section 2.

An independent tool confirms the drag term.
[wt_ballistics_calc](https://github.com/Warthunder-Open-Source-Foundation/wt_ballistics_calc)
(Rust) is a missile flight simulator. It integrates
`drag_force = 0.5 * rho * v^2 * cxk * PI * caliber^2 / 4`, which is the same drag
term as our `k = rho * Cx * PI * caliber^2 / (8 * mass)` for a coasting body.
Two naming differences: it calls the drag field `cxk` (our `Cx`) and `caliber`
(our `ballisticCaliber`), and it varies `rho` with altitude, so `1.225` is the
sea-level value. This tool covers missile flight only. It has no penetration,
armor, De Marre, or Lanz-Odermatt code, so it does not source the rest of this
file.

## 2. Penetration model

War Thunder uses two kinetic penetration paths. The shell BLK selects the path.

- **Lanz-Odermatt** path: long-rod penetrators (APFSDS). The shell BLK carries
  `lanzOdermattWorkingLength`.
- **De Marre** path: full-caliber AP, APC, and APCBC. The shell BLK carries
  `demarrePenetrationK`.

A third path exists for about 85 legacy rounds (some AP, APDS, and legacy
APFSDS such as `120mm_l23`). These rounds carry an empty `kineticDamageParams`
block and define penetration only as an explicit `armorpower` table.

### 2.1 Top-level shape

The runtime dispatches on a material byte at struct offset `[rdi+0x0]`:

- `0` = steel
- `1` = depletedUranium
- `2` = tungsten

The core kinetic formula is:

```
Penetration(V) = A * exp(B / (V/1000)^2)
```

Variable definitions:

- `V` is the impact speed in m/s.
- The game converts `V` to km/s by a multiply with `0.001` before the square.
- `A` and `B` are two floats stored per shell at struct offsets `+0x28` and
  `+0x2c`. The BLK dumps these floats as `lanzOdermattCachedMults`.
- `A` is the asymptotic penetration coefficient.
- `B` is a negative per-round material constant.

The constant `0.001` sits at `.rodata` VA `0x81fa430`.

### 2.2 Lanz-Odermatt: how the game builds A and B

The parser builds `A` and `B` once per shell. The parser passes
`damageCaliber * 1000.0` as the diameter, so `D` is in mm.

For tungsten (`lanzOdermattMaterial:t="tungsten"`, material byte `2`):

```
A = 0.994 * L * sqrt(rhoP / 7850) / tanh(0.0656 * (L/D) + 0.283)
B = -24965.201171875 / rhoP
```

Variable definitions:

- `L` is `lanzOdermattWorkingLength` in mm.
- `D` is `damageCaliber * 1000` in mm.
- `rhoP` is `lanzOdermattDensity` in kg/m^3 (penetrator density).
- `7850` is the target (RHA) density in kg/m^3. It is a hardcoded constant.

### 2.3 Lanz-Odermatt constants

The project read all these constants from `.rodata`.

| Symbol | Value | Unit | Role |
|---|---|---|---|
| L-multiplier, steel/default | 1.104 | - | branch material byte 0 |
| L-multiplier, DU (byte 1) | 0.825 | - | depletedUranium branch |
| L-multiplier, tungsten (byte 2) | 0.994 | - | tungsten branch |
| tanh L/D coefficient | 0.0656 | 1/mm-ratio | shape term |
| tanh offset | 0.283 | - | shape term |
| 1/7850 (target density) | 0.00012738852 | m^3/kg | reciprocal of 7850 |
| hardness pow exponent (steel) | -0.2342 | - | steel B path only |
| final mult (steel) | -73013.0625 | - | steel B path only |
| B-numerator, DU (byte 1) | -17660.76 | - | DU B path |
| B-numerator, tungsten (byte 2) | -24965.2 | - | tungsten B path |

For the steel/default path (material byte `0`), the game builds `B` with the
Brinell hardness:

```
A = 1.104 * L * sqrt(rhoP / 7850) / tanh(0.0656 * (L/D) + 0.283)
B = (hardness^-0.2342 * -73013.0625) / rhoP
```

`hardness` is `lanzOdermattBrinellHardnessNumber`. The viewer defaults it to
`470` when the field is absent.

### 2.4 Lanz-Odermatt validation

The project validated the tungsten path against `protectionMapTestParams`
(L=510, D=26, rhoP=17500):

```
B = -24965.201171875 / 17500 = -1.426583   (dump: -1.42658, exact)
A = 0.994 * 510 * sqrt(17500/7850) / tanh(0.0656*19.615 + 0.283)
  = 0.994 * 510 * 1.4931 / tanh(1.5701)
  ~= 825.6                                  (dump: 825.423, match)
```

The project validated the full curve against live screenshots:

- DM53: `L=685`, `D=23`, `rhoP=17500`, `V0=1750` give `A=1040.08796`,
  `B=-1.42658286`, and `Pen(V0)=652.78 mm`. The screenshot 10 m value is `653`.
- DM43: `L=585`, `D=22`, `rhoP=17500`, `V0=1750` give `A=898.85465`,
  `B=-1.42658286`, and `Pen(V0)=564.14 mm`. The screenshot 10 m value is `564`.

### 2.5 De Marre path

The parser reads four BLK fields:

```
demarrePenetrationK
demarreSpeedPow
demarreMassPow
demarreCaliberPow
```

The parser precomputes a coefficient `C`:

```
C = 100 * demarrePenetrationK
      * (damageMass_or_warheadMass ^ demarreMassPow)
      * ((damageCaliber_m * 1000 * 0.01) ^ -demarreCaliberPow)
```

`damageCaliber` defaults to `caliber` if absent. The parser passes
`damageCaliber * 1000` to the parser function, then multiplies that by `0.01`
before the power. The mass input is `damageMass`, or `warheadMass`, or `mass`.

The runtime evaluates:

```
Penetration(V) = C * (V / referenceSpeed) ^ demarreSpeedPow
referenceSpeed = armorResistance = 1900.0
```

`referenceSpeed` equals the global `armorResistance` from
`config/damagemodel.blk`. That file ships:

```
maxArmorEffectiveScale = 20.0
armorBreachK           = 7.0
armorResistance        = 1900.0
```

### 2.6 De Marre validation (BR-412D)

BR-412D BLK fields:

```
mass = 15.88
caliber = 0.1
damageCaliber absent -> defaults to caliber
speed = 887
demarrePenetrationK = 1.0
demarreSpeedPow = 1.43
demarreMassPow = 0.71
demarreCaliberPow = 1.07
slopeEffectPreset = "apc"
```

```
C = 100 * 1.0 * 15.88^0.71 * (0.1 * 1000 * 0.01)^-1.07
  = 712.20309

Pen(10 m) = 712.20309 * (885.94 / 1900.0)^1.43 = 239.21 mm
```

The screenshot 10 m value is `239`.

### 2.7 Legacy armorpower path

Legacy rounds carry no kinetic block. They define penetration as a range table.

```
ArmorPower<N>m = (penetration_mm, range_m)
```

Example (L23): `410 @ 0 m`, `405 @ 500 m`, `300 @ 4500 m`. The viewer
interpolates penetration by range from this table. The armorpower value is the
flat (0 degrees) penetration. The game applies the slope effect on top.

### 2.8 Angle of impact and slope effect

The angle penetration is not a `cos^m(theta)` power law. War Thunder applies a
preset table from `gamedata/damage_model/slope_effect.blk`.

The displayed stat-card angle `theta_display` is measured from the plate normal.
`0 degrees` is a flat/normal hit. `60 degrees` is a highly sloped hit. The table
lookup uses the complement:

```
slopeKey = 90 - theta_display
```

For a single-row preset (`apds_fs_long`, used by APFSDS such as DM53 and DM43):

```
Pen_at_angle = Pen_flat / interpolateSlopeEffect(slopeKey)
```

Example preset `apds_fs_long`, row `caliberToArmor:r=1.0`:

```
slopeEffect0deg  = (0.0,  20.0)
slopeEffect10deg = (10.0, 5.30000019)
slopeEffect20deg = (20.0, 2.40000010)
slopeEffect30deg = (30.0, 1.73000002)
slopeEffect40deg = (40.0, 1.54999995)
slopeEffect50deg = (50.0, 1.305)        # the key appears twice in the row
slopeEffect50deg = (80.0, 1.01499999)   # second copy: name says 50, x value is 80
slopeEffect60deg = (60.0, 1.18499994)
slopeEffect70deg = (70.0, 1.06400001)
slopeEffect90deg = (90.0, 1.0)
```

DM53 validation at muzzle (flat `Pen_flat = 652.78`):

- Displayed `30 degrees`: key `60`, divisor `1.18499994`, result `550.87`. The
  screenshot value is `551`.
- Displayed `60 degrees`: key `30`, divisor `1.73000002`, result `377.33`. The
  screenshot value is `377`.

For full-caliber APC and APCBC presets with several `caliberToArmor` rows, the
stat-card value needs an implicit solve. `caliberToArmor` is the ratio of the
shell caliber in mm to the armor it can defeat:

```
slopeKey = 90 - theta_display
Find P_angle such that:
  P_angle = P_flat / S(slopeKey, caliber_mm / P_angle)
```

`S(angle, caliberToArmor)` is a bilinear interpolation over the preset rows and
each row's `slopeEffect*deg` points. The viewer solves `P_angle` by bisection.

BR-412D validation (10 m flat `P_flat = 239.21`, `caliber_mm = 100`):

- Displayed `30 degrees`: solve `P = 239.21 / S(60, 100/P)`, result `181.6`. The
  screenshot value is `182`.
- Displayed `60 degrees`: solve `P = 239.21 / S(30, 100/P)`, result `82.0`. The
  screenshot value is `82`.

A parser that keeps only the last copy of a repeated key loses the `(50, 1.305)`
point. Keep both points.

Live check (October 2026 build, per-part hit records, 125 mm APFSDS with the
`apds_fs_long` preset on an 80 mm `RHA_tank` hull side): the charge divided by
`nominal × quality` was 1.00, 1.09, 1.25 and 1.65 at geometric incidence angles
of 2.4, 22.7, 36.2 and 55.7 degrees. These are the preset values. Across 18
live points, a monotone cubic interpolation (PCHIP) over the angle fits within
0.24 %. Linear interpolation between the points overcharges by up to about 11 %
near 72 degrees.

### 2.9 Normalization

The shared projectile-type BLK carries a `normalizationPreset` field (see
`gamedata/damage_model/projectile_types/*.blk`). The reverse-engineering notes
did not recover a separate numeric normalization term. The stat-card angle
behavior is fully explained by the `slope_effect.blk` preset table above. Treat
a distinct normalization angle as folded into the slope table. For APFSDS with
the `apds_fs_long` preset, the live per-part records show no separate
normalization term: the slope value at the geometric incidence angle explains
the charge to within 0.24 %. Confidence: **Confirmed** for `apds_fs_long`,
**Partial** for full-calibre presets.

### 2.10 Ricochet probability

The shell BLK names a ricochet preset (`ricochetPreset`) and a ground ricochet
preset (`groundRicochetPreset`). The presets resolve into tables in:

- `gamedata/damage_model/ricochet.blk`
- `gamedata/damage_model/ricochet_of_ground.blk`

The row shape matches `slope_effect.blk`. The point keys are:

```
ricochetProbability<N>deg = (angle, probability)
```

The viewer reads `ricochet.blk` and interpolates the probability by the slope
key. Example: an L23 shot at AoA `81.3 degrees` uses the `apds_fs_long` table.
The table gives probability near `1.0` at slope key below `9 degrees`. The
viewer classifies that shot as a ricochet.

The native crosshair result carries a `ricochetProb` float and a `ricochet`
enum. War Thunder computes ricochet in a code path separate from the
penetration formula. Confidence: **Confirmed** for the table source and shape.

### 2.11 Overmatch rule

The reverse-engineering notes do not document an explicit caliber-versus-plate
overmatch rule with its own constants. War Thunder encodes the caliber-to-armor
behavior inside the slope-effect and ricochet preset tables through the
`caliberToArmor` row axis. Do not invent an overmatch constant. Confidence:
**Not reverse-engineered** as a standalone rule.

### 2.12 Penetration versus distance (validation tables)

The project reproduced these stat-card tables with no fitting. Distances are
in meters. Values are in mm at `0 degrees` (flat).

| Shell | 10 m | 100 m | 500 m | 1000 m | 1500 m | 2000 m |
|---|---:|---:|---:|---:|---:|---:|
| DM53 computed | 653 | 650 | 641 | 629 | 617 | 605 |
| DM53 screenshot | 653 | 650 | 641 | 629 | 617 | 605 |
| DM43 computed | 564 | 562 | 555 | 545 | 535 | 525 |
| DM43 screenshot | 564 | 562 | 555 | 545 | 535 | 525 |
| BR-412D computed | 239 | 236 | 220 | 202 | 185 | 170 |
| BR-412D screenshot | 239 | 236 | 220 | 202 | 185 | 170 |

Full-angle live reference tables (mm), read off the player client:

**DM53** (120 mm, muzzle 1750 m/s, caliber 120 mm, mass 5 kg):

| Angle | 10 m | 100 m | 500 m | 1000 m | 1500 m | 2000 m |
|---|---|---|---|---|---|---|
| 0 | 653 | 650 | 641 | 629 | 617 | 605 |
| 30 | 551 | 549 | 541 | 531 | 521 | 511 |
| 60 | 377 | 376 | 371 | 364 | 357 | 350 |

**DM43** (120 mm, muzzle 1750 m/s, caliber 120 mm, mass 4 kg):

| Angle | 10 m | 100 m | 500 m | 1000 m | 1500 m | 2000 m |
|---|---|---|---|---|---|---|
| 0 | 564 | 562 | 555 | 545 | 535 | 525 |
| 30 | 476 | 474 | 468 | 460 | 452 | 443 |
| 60 | 326 | 325 | 321 | 315 | 309 | 304 |

**BR-412D** (100 mm APCBC, muzzle 887 m/s, caliber 100 mm, mass 15.88 kg):

| Angle | 10 m | 100 m | 500 m | 1000 m | 1500 m | 2000 m |
|---|---|---|---|---|---|---|
| 0 | 239 | 236 | 220 | 202 | 185 | 170 |
| 30 | 182 | 179 | 168 | 155 | 143 | 132 |
| 60 | 82 | 81 | 76 | 71 | 66 | 62 |

## 3. Post-penetration

### 3.1 Fuse (fuze) delay and sensitivity

The shell BLK carries fuse fields. Example M61 APCBC (`75mm_m61`):

```
fuseDelayDist = 1.2
explodeTreshold = 14.0
checkIntegrityAfterExplosion = true
```

Variable definitions:

- `fuseDelayDist` is the fuse delay distance in meters after the shell passes
  the plate.
- `explodeTreshold` is the minimum armor in mm that arms the fuse. The BLK
  spells the key `explodeTreshold`.
- `checkIntegrityAfterExplosion` is a boolean flag.

The reverse-engineering notes do not give the full fuse arming and detonation
math. Confidence: **Partial** (fields known, mechanism not solved).

### 3.2 Spall cone

The shell BLK names a secondary shatter preset (`secondaryShattersPreset`). The
preset resolves into `gamedata/damage_model/secondary_shatter_presets.blk`. The
same presets are also in `config/damagemodel.blk` under `secondaryShatters`.
The BLK also carries a `stabilityThreshold` field.

The file holds 19 presets: `default`, `ap`, `ap_rocket`, `ap_large_caliber`,
`ap_small_arms`, `ap_solid_medium_caliber`, `apds_fs_long`, `apds_fs`,
`apds_fs_25_76mm`, `apds`, `atgm_ke`, `apcr`, `heat`, `heat_fs`, `atgm`,
`heavy_heat_warhead`, `170mm_heat_warhead`, `hesh`, `efp`.

Each preset is a set of cone sections plus scale curves. A section is:

```
sectionN {
  angles = [inner_deg, outer_deg]   # cone, or a ring when inner > 0
  shatter {
    distance = <m>
    count = <n>          # or countPortion = <fraction> in mass-based presets
    penetration = [a, b] # mm
    damage = [a, b]
    size, onHitChanceMult, onHitChanceMultFire, onHitChanceMultExplFuel,
    aggregateDamage, shellShatter
  }
}
```

Example, preset `ap`:

| Section | angles | distance | count | penetration | damage |
|---|---|---|---|---|---|
| 0 | [0, 10] | 5 | 8 | [11, 8] | [20, 15] |
| 1 | [0, 25] | 3 | 20 | [7, 5] | [15, 12] |
| 2 | [0, 40] | 1.5 | 40 | [4, 3] | [8, 6] |

Example, preset `apds_fs_long` (DM53): section 0 `[0,5]`, count 10, pen
`[17,10]`; section 1 `[7.5,14.5]` (a ring), count 45, pen `[10,8]`; section 2
`[5,50]`, count 50, pen `[4,3]`.

Scale curves in a preset:

- `residualArmorPenetrationToShatterCountMult`
- `residualArmorPenetrationToShatterPenetrationMult`
- `residualArmorPenetrationToShatterDamageMult`
- `caliberToArmorToShatterCountMult`
- mass-based presets (`ap_large_caliber`, `apds`, `apcr`): `armorMassToShatterCount`,
  `shellMassToShatterCount`, `residualPenetrationTo{Armor,Shell}Shatter{Penetration,Damage}Mult`.
  These presets split the fragments into `section_shellShatters*` and
  `section_armorShatters*` by `countPortion`.

Example `ap`: count curve `[20, 100, 0.5, 1.0]`. The 4-value curves look like a
clamped linear map `[x0, x1, y0, y1]`, with residual penetration in mm as `x`.
This reading is an inference, not confirmed in the binary.

Global shatter values in `config/damagemodel.blk`:

```
minSecondaryShatterAngleFromArmor = 15.0
shattersMinSolidArmorThicknessMult = 0.5
shatterProbeDist = 0.1
maxShatterEffectiveMult = 3.0
armorFragmentsThicknessThreshold = 3.3
armorFragmentsPierceThreshold = 90.0
secondaryShatterWithoutPenetration = [20, 5, 0, 0]
```

`secondaryShattersWithoutPenetration` holds a separate small cone for a hit
that does not penetrate (presets `default`, `ap`, `apds`).

Armor classes control the spall per plate:

- `createSecondaryShatters = false` stops a plate from making a cone. Many
  composite and high-hardness plates set it.
- `secondaryShatterArmorQuality` and `secondaryShatterEffectiveThicknessMax`
  set how a part stops fragments. A spall liner (`armour_aramide_fabric`) has
  `secondaryShatterEffectiveThicknessMax = 6.0`.

The binary strings include the debug line
`secondary shatters from %s in angles %f|%f`, and the parser checks that
`angles should be in the range from 0 to 180`.

#### Runtime behavior (confirmed live)

These rules come from live debugger captures of 57 mm APCBC (preset `ap`)
hits on a T-55A side in a test drive, build 2.59.0.54. They cover about 10
penetrations and about 260 fragments.

- **One cone for each perforated plate.** A shell that passes two plates makes
  two cones, each from its own exit point. A hit that does not penetrate (a
  stop or a ricochet) makes no secondary shatter cone in this path.
- **Cone axis = shell flight direction.** It is not the plate normal. On a side
  plate hit at 38 degrees off the normal, the axis was 38 degrees off the
  normal too. The axis stays the same on the second plate of the same shot.
- **Each section is a full cone from `angles[0]` to `angles[1]`.** The sections
  overlap; they are not rings unless `angles[0] > 0`. The parser stores
  `cos(angles[1])` and `cos(angles[0])`.
- **Directions are uniform in solid angle.** The value
  `u = (1 - cos(theta)) / (1 - cos(outer))` averages 0.49-0.50 over 134
  fragments (0.5 is uniform solid angle). The azimuth is uniform over 360
  degrees.
- **All fragments start at the hit point.** The origin offset is 0.
- **Fragment range = section `distance`**, exactly, with no random part.
- **Scale curves are clamped linear maps** `[x0, x1, y0, y1]`, with
  `x = residual penetration` in mm. Example `ap`: a residual of 53.5 mm gives a
  penetration multiplier of 0.7676 and a damage multiplier of 0.6514. Both values
  match the curves at the same `x`.
- **Fragment count** = `count * countMult(residual) * calMult(caliber/armor)`,
  then rounded (possibly at random). The default `caliberToArmorToShatterCountMult`
  is `[0.5, 1.0, 0.5, 1.0]`. At the clamps (residual <= 20 mm, ratio <= 0.5)
  the `ap` counts were exactly `8/20/40 * 0.25 = 2/5/10`.
- **Resolved section record (0x48 bytes):** `+0x04` count (int), `+0x08`
  cos(outer), `+0x0c` cos(inner), `+0x10` distance, `+0x14` penetration low,
  `+0x18` penetration high, `+0x1c` damage first, `+0x20` damage second,
  `+0x24` `onHitChanceMultFire`, `+0x28` `size`.
- **Fragment record (0x70 bytes):** `+0x04` world origin, `+0x10` world
  direction, `+0x1c` range, `+0x20` unit-local origin, `+0x2c` unit-local
  direction, `+0x38` range. The rest is zero before the trace stage. The
  fragment carries no own penetration or damage. Those come from the section.

More confirmed rules (125 mm APFSDS, HEAT-FS, and HE-FS on a Leopard 1 side):

- **The inner angle cuts a hole.** All 311 fragments of the `apds_fs_long`
  section `[7.5, 14.5]` fell between 7.5 and 14.5 degrees. Every cone type tested
  (`[0,5]`, `[0,10]`, `[0,25]`, `[0,40]`, `[5,50]`, `[7.5,14.5]`) is uniform in solid
  angle between its inner and outer angle.
- **Count rounding:** `round(count * countMult * calMult)` in float. Example
  `10 * 1.5 * 0.9` = 13.4999 gave 13; `45 * 1.5 * 0.9` = 60.75 gave 61.
- **Sabot petals make their own spall.** An APFSDS hit at short range on a thin
  side plate made three more cones from the `apfsds_sabot` bullet (preset `ap`,
  `segmentCount 3`) at the entry point.
- **A HEAT jet makes a spall cone at each plate it perforates** (preset `heat_fs`
  from `cumulativeSecondaryShattersPreset`). Section 0 has flag byte `0x00`
  (`shellShatter`, the jet itself) and section 1 has `0x01` (armor fragments).
  The values drop on later plates as the jet weakens.
- **Some fragments are removed after the draw.** A few cones held fewer
  fragments than their count (for example 54 of 90 on an internal plate). The
  rule is not known.

#### Warhead body fragments ("real shatters")

A shell with `damage.shatter { useRealShatters = true ... segment[] }` (HE,
HEAT) makes body fragments when the warhead bursts. The code path is
`prepare_real_shatters`, and it uses the same fragment generator. The axis is
the shell direction, and the origin is the burst point. Confirmed rules:

1. `m = explosiveMass * brisanceEquivalent` (the TNT equivalent for fragments).
2. `fill = m / mass`. The class is the first entry in
   `explosiveTypeToShattersParams` whose `fillingRatio >= fill`. There is no
   blend between classes.
3. Base range `R = explosiveMassToRadius(m)`, base penetration
   `P = explosiveMassToPenetration(m)`, damage `D = explosiveMassToDamage(m)`
   (linear interpolation over the points).
4. `N = bodyMassToShattersCount(mass - m) * shatter.countPortion`.
5. Each segment gets `round(N * segment.countPortion)` fragments in its
   `angles` band, range `R * radiusScale`, penetration `P * penetrationScale`,
   and damage `D * damageScale`. Directions are uniform in solid angle.

Checks: 125 mm 3BK18M (19 kg, 1.754 kg `ocfol`, brisance 1.47) gives
`m = 2.578`, class `he_heat`, `N = 1200` (24/60/816/240/60), `R = 23.24`,
`P = 6.824`, `D = 12.035`. 125 mm 3OF26 (23 kg, 3.402 kg `a_ix_2`, brisance 1.4)
gives `m = 4.763`, class `bombs_he_sap`, `N = 2099`, `R = 33.81`, `P = 5.881`,
`D = 9.514`. All values match the live capture.

#### APHE burst ("synthetic shatters")

Confirmed live with 75 mm PzGr 39/42 (6.8 kg, 0.017 kg `h10`, brisance 1.4)
into a KV-2 side:

- **The fuse delay starts at the first plate.** The burst was 1.210 m past the
  entry point (`fuseDelayDist = 1.2`).
- **The kinetic trace runs first.** In the same frame, the shell body went on
  past the burst point, perforated the far side 1.86 m from entry, and made a
  second spall cone. The burst came after both cones. This fits
  `checkIntegrityAfterExplosion = true`.
- **APHE uses synthetic (statistical) shatters, not fragment rays.** The shell
  has no `damage.shatter` block; the `testProperties` segments and their
  `countPortion` are not used. The game calls
  `damage_by_synthetic_shatters_processing` with a params struct:
  `+0x04` range R, `+0x08` count N, `+0x0c` penetration P, `+0x10` damage D,
  `+0x14` damage type. R squared is also stored next to R.
- The values come from the same rules as real shatters (steps 1-4 above,
  without `countPortion`). Prediction before the test: `m = 0.0238`, class
  `aphe_hc`, `R = 1.6816`, `N = 199.08`, `P = 3.69`, `D = 5.4358`. Live values:
  `1.68158, 199.076, 3.69, 5.43579`.

Still open: how the statistical model turns N, R, P, and D into hits on parts.

#### Fragment flight through parts (confirmed live)

After the draw, the game traces each fragment ray against the collision world.
Each trace hit is a 0x130-byte record, with the distance `t` at `+0x18` and a
hit type byte at `+0x28`. Type 2 is a hit on a vehicle DM part, and its handler
is `0x6164290`. Each fragment has a 0x50-byte state:

| Offset | Field |
|---|---|
| `+0x00` | fragment index |
| `+0x04` | range |
| `+0x08` | size |
| `+0x0c` | armor used so far, in mm |
| `+0x14` | stop point as a fraction of the range (`t / range`), -1 while flying |
| `+0x18`, `+0x24` | local and world direction |
| `+0x31` | stopped flag |
| `+0x48` | number of parts hit |

- Each part adds its thickness to the armor used. A module adds its
  `armorThrough` value. Example: a crew member (`steel_tankman`,
  `armorThrough 3.5`) adds 3.5 mm; a 75 mm hull side adds about 75 mm along the
  ray.
- **A fragment stops at the part where the armor used becomes greater than its
  penetration.** Live example (`ap` preset, 75 mm APHE in a KV-2): section 0
  fragments (penetration 11 to 8) went through two crew members (7 mm) and
  stopped in the far side armor. Section 1 fragments (penetration 7 to 5)
  stopped at the second crew member, at 7.0 mm.
- Not yet separated: whether a fragment's penetration falls linearly from
  `pen[high]` to `pen[low]` over its range, or stays at one end. Both fit all
  40 recorded hits.
- **Fragments near the plate surface are kept.** On a shot 51.5 degrees off
  the normal, fragments 6.4 and 7.8 degrees from the plate surface stayed.
  `minSecondaryShatterAngleFromArmor` (15) probably clamps the cone axis
  instead; this needs a penetration at more than 75 degrees to test.

#### Trace pattern (`traceStrategy`)

The parsed table has one 0x20-byte row for each pattern: `minCaliber`,
`circleCount`, `pointCount`, a pointer to the points, and their count. The
points are stored as `(sin, cos)` pairs already scaled by ring: ring `i` of
`circleCount` has radius `i / circleCount` (for example 6 points at 0.5 and 12
points at 1.0 for `circleCount 2`). At each shot, `0x6192ac0` picks the row by
caliber, copies its points, and stores `1000 * caliber` (the caliber in mm) as
the scale. Not yet confirmed: whether the outer ring sits at the full caliber
or at half the caliber.

Still open: how the `[a, b]` penetration and damage pairs apply to one fragment
(interpolation over range is likely), the random draw for counts, the 15-degree
`minSecondaryShatterAngleFromArmor` clamp (not yet seen at the angles tested),
and the RNG.

### 3.3 HE filler and TNT equivalent

The shell BLK carries the filler fields. Examples:

```
75mm_m61 APCBC:  explosiveType = exp_d,             explosiveMass = 0.065
75mm_m48 HE:     explosiveType = tnt,               explosiveMass = 0.666
75mm_m64 Smoke:  explosiveType = smoke_composition, explosiveMass = 0.05
```

Variable definitions:

- `explosiveType` names the filler material (for example `tnt`, `exp_d`,
  `smoke_composition`).
- `explosiveMass` is the filler mass in kg.

The filler factors are in `gamedata/damage_model/explosive.blk`, block
`explosiveTypes` (116 types). Each type has `strengthEquivalent` and
`brisanceEquivalent`. Examples: `tnt` 1.0/1.0, `a_ix_2` 1.54/1.4, `rdx`
1.6/1.4, `comp_b` 1.31/1.27, `hmx` 1.656/1.5.

The same file holds these curves:

- `explosiveTypeToSplashParams`: TNT-equivalent mass to inner radius, outer
  radius, penetration, and damage. Example: 0.1 kg gives inner 0.275 m, outer
  0.75 m, damage 110.
- `explosiveTypeToPressureParams`, `explosiveTypeToPressureOpenParams`: the
  overpressure curves.
- `explosiveTypeToShattersParams`: shell-body fragment classes `aphe_sc`,
  `aphe_hc`, `he_frag`, `he_heat`, `bombs_he_sap`, `bombs_he_frag`. Each class
  has a `fillingRatio` and the curves `explosiveMassToRadius`,
  `explosiveMassToPenetration`, `explosiveMassToDamage`, and
  `bodyMassToShattersCount`.

The binary checks the filler-to-mass ratio against the class maximum. Its error
text is `dm::shatter: fillingRatio %.3f >= max %.3f`. The debug line for an ammo
explosion prints `shellMass`, `strengthEquivalent`, `brisanceEquivalent`, the
splash radii, splash penetration and damage, and the shatter radius, count,
penetration, and damage.

`config/damagemodel.blk` also holds:

- `penetrationByExplosiveMassModifier`: filler ratio to a penetration
  multiplier, `[[0.0065,1.0],[0.016,0.93],[0.02,0.9],[0.03,0.85],[0.04,0.75]]`.
- `shellIntegrityAfterExplosionByExplosiveMass = [75, 400, 0.35, 0.85]`.

Confidence: **Confirmed** for the data. **Partial** for the runtime use. The
code that picks the fragment class and that converts the mass to TNT
equivalent is not traced.

### 3.4 HEAT standoff

The armor-class struct carries per-mechanism quality arrays. The mechanism keys
include `cumulative` (HEAT), `explosiveFormedProjectile` (EFP), and
`tandemPrecharge`. The native protection result reports these mechanisms in the
`penetratedArmor` sum.

The notes do not give a HEAT standoff-versus-penetration formula. Confidence:
**Not reverse-engineered**.

Live check (October 2026 build, 120 mm HEAT-FS `120mm_dm12`, `armorPower` 480 mm,
`cumulativeDamage.distance` 10 m, 6 shots on an IT-1):

- The shell bursts about 0.2 m before the plate on a direct hit.
- The jet loses about 88 to 91 mm of penetration per metre of travel. This is
  about twice `armorPower / distance` (48 mm per metre). Only three readable
  points support the value.
- At a plate, the jet is charged `nominal × quality / cos θ`. This shell has no
  slope preset.

The class field `cumulativeAirArmor` is a possible static source for the loss
per metre. It is not confirmed.

### 3.5 Module, crew, and ammo damage data

Each tank BLK (`gamedata/units/tankmodels/*.blk`) gives every DM part an `hp`,
an armor class, and damage multipliers. The values come mostly from shared
templates. Examples from a modern tank:

| Group | hp | Other fields |
|---|---|---|
| crew | 40 | `steel_tankman`, `genericDamageMult 3.0` |
| ammo | 300 | `armorThrough 10`, `genericDamageMult 2.0`, `fireProtectionHp 20` |
| fuel_tanks | 400 | `armorThrough 12`, `fireParamsPreset fuel_internal` |
| power_block | 100 | `armor_tank_engine`, thickness 150 |
| cannon_breech | 150 | thickness 150 |
| tracks | 300 | `genericDamageMult 1.8` |
| hull_spall_liner | 200 | `armour_aramide_fabric`, thickness 20 |

An `hp` below the root `hp` (10000) does not mark a module. A survey of the
`DamageParts` of 1256 tank units shows these points:

- Many protective parts set their own lower `hp`: screens (100 to 400), ERA
  blocks (250 to 350), spall liners (200), firewalls in `inner_armor` (150),
  tracks (250 to 300), road wheels (250 to 300), and stowage shields (1000).
- The module parts sit in a small fixed set of groups in every unit: `crew`,
  `ammo`, `fuel_tanks`, `fuel_tanks_exterior`, `power_block` (engine and
  transmission), `cannon_breech`, `gun`, `optics`,
  `commander_panoramic_sight`, and `equipment_body_turret` (turret drives,
  radio, fire control, electronics).
- A few units file the same kinds of part under rarer groups, such as
  `crew_turret`, `engine`, `machine_gun`, or optics under `mask`. Their armor
  class still marks them: `steel_tankman`, `armor_tank_engine`, `optics_tank`,
  and `tank_barrel` appear only on crew, engines, optics, and barrels.
- `armorThrough` alone does not separate modules from plates. Plates use the
  class default of 1, but some plates set a larger value (for example
  `armorThrough 100` on the IS-1 and IS-2 1943 mantlet and turret front).
  `cannon_breech` keeps the default of 1.
- The `tracks` group sets `allowRicochet: true` (its class `tank_traks` has
  `false`) and `armorEffectiveThicknessMax 20`. These are plate-model fields.

Confidence: **Confirmed** for the data. How the game itself decides which
parts are charged `armorThrough` is **Not reverse-engineered**.

`DamageEffects.part` holds the hit rules. Each rule has a damage type, a
damage threshold, and probabilities. Examples for ammo: `onHit {cumulative,
expl 0.4, fire 0.5, damage 75}` and `onKill {generic, expl 0.5, full_expl 0.1,
fire 0.4}`. A rule can also kill a linked part, for example a wheel kills the
track.

The `ammo` block sets the ammo explosion: `detonateProb`, `detonatePortion`,
`explodeHitPower`, `explodeArmorPower`, `explodeRadius`. `MetaParts` and
`compartments` spread pressure damage to the crew.

`config/damagemodel.blk` sets the global values `ammoExplosionProb`,
`ammoStowageDetonatePortion`, `fuelExplosionRangeK`, and the curve
`kineticEnergyToDamage` (32 points, from `[100, 2]` to `[5e8, 40000]`).

Confidence: **Confirmed** for the data. **Not reverse-engineered** for the
runtime use of the thresholds.

### 3.6 Saved hit files (`ReplayHits`)

The client saves a hit as a text BLK in the `ReplayHits` folder of the game
directory. The hit camera and Protection Analysis both write this format. The
Protection Analysis UI loads a file again with `repeat_shot_from_file` (see
`scripts/dmviewer/protectionanalysis.nut`). The UI shows the save button only
with the `HitsAnalysis` feature on a PC.

Fields:

```
version:i, time:r, damageRole:t ("victim" or "offender")
offender:t, victim:t                 # player names
object:t                             # victim unit
offenderObject:t, spawnerObject:t
weapon:t                             # weapon BLK path
ammo:t, ammoType:t                   # shell name and projectile type
bulletSetNo:i, ammoNo:i, isBelt:b, supportGun:b
lPos:p3, lDir:p3                     # hit point and direction, unit-local
pos:p3, dir:p3                       # world values
speed:r or startVel:p2               # impact speed, or muzzle speed and angle
startAltitude:r
travelDistance:r, distance:r, shotDistance:r
piercingShift:r, justExplosion:b, testProperties:b
seed:i                               # random seed for the hit
isSabot:b, isSecond:b
turretPos { pos:p2 ... }             # turret and gun angles
parts {
  size:i                             # part count of the victim
  part:ip3 = index, 65535, state     # parts that are not at full health
  disabled:i = index                 # parts that are dead or removed
}
```

A file from a battle hit has `version 8` and the `turretPos` and `parts`
blocks. A file saved in Protection Analysis has `version 0` and no part state.

The `state` value is a multiple of 4096 in the files seen (0 to 61440). It
looks like a part health value in 1/16 steps. This is an inference.

The `seed` field means the post-penetration result is a seeded random draw.
A file is a test case: the same shot, seed, and part state must give the same
result in the game.

### 3.7 Binary anchors (build 2.59.0.54)

The binary is non-PIE at base `0x400000`, so code loads string addresses as
32-bit immediates. These code addresses load the shatter strings. They change
with each patch.

| String | Code reference |
|---|---|
| `secondary shatters: angles should be in the range from 0 to 180` | `0x61e0353` |
| `caliberToArmorToShatterCountMult` | `0x61e0863`, `0x61e08bf` |
| `residualArmorPenetrationToShatterCountMult` | `0x61e08cc`, `0x61e2731`, `0x61e2819` |
| `armorMassToShatterCount` | `0x61e0961` |
| `shellMassToShatterCount` | `0x61e099c` |
| `secondaryShattersPreset` | `0x61e0b92`, `0x61e0bdc` |
| `minSecondaryShatterAngleFromArmor` | `0x6169b71` |
| `createSecondaryShatters` | `0x18698f5`, `0x61a89ed`, `0x61a89fd` |
| `fuseDelayDist` | `0x224ca14`, `0x224ca2c`, `0x61f70c9` |
| `explodeTreshold` | `0x224ca76`, `0x224ca8e`, `0x61f70e0` |
| `------SHATTER HIT------` | `0x2a7cb9a` |

Runtime functions (same build):

| Address | Role |
|---|---|
| `0x61e02b0` | section parser (stores cos of the angles) |
| `0x61e0840` | preset curve parser (residual mode or mass mode) |
| `0x6169b60` | global shatter config parser (stores `1 - cos(minSecondaryShatterAngleFromArmor)`) |
| `0x6166360` | `shatter__prepare_shatters`: makes the fragment rays from the resolved sections; axis at `ctx+0x130`, sections at `ctx+0x158`, count at `ctx+0x168` |
| `0x18580f0` | caller of `0x6166360` |
| `0x6169450` | `shatter__spawn_processing` (not called for AP spall in a test drive) |
| `0x619aeb0` | `prepare_real_shatters` (warhead body fragments); calls `0x6166360` from `0x619b0ea` |
| `0x185d330` | `do_splash_and_synthetic_shatters_damage` (burst entry) |
| `0x61ace90` | `damage_by_synthetic_shatters_processing` (APHE statistical shatters) |
| `0x615aac0` | `traceStrategy` parser |
| `0x620e3e0` | trace ring builder: ring `i` of `circleCount` gets `pointCount * i` points at equal angles |
| `0x6192ac0` | per-shot trace shape: picks the pattern by caliber, copies its points |
| `0x00b498a0` | traces the fragment rays against the collision world |
| `0x184c600` | applies fragment hits by type (0 and 1: other, 2: DM part, 3: rendinst, 4 and 5: destructibles) |
| `0x6164290` | fragment vs vehicle DM part |

## 4. Armor interaction

### 4.1 Line-of-sight thickness

The standard line-of-sight rule is:

```
LOS = plate / cos(angle)
```

Variable definitions:

- `plate` is the nominal plate thickness in mm.
- `angle` is the impact angle off the plate normal in degrees.
- `LOS` is the line-of-sight thickness in mm.

The project confirmed this rule against a live point:
`225 mm * secant(53.85 degrees) ~= 381 mm`. The obliquity genuinely lengthens
the path through a flat plate.

The viewer measures the real chord through the collision mesh instead of a
`plate / cos(angle)` scalar. War Thunder itself uses a native per-hit 3D
measurement, not a BLK scalar. See section 4.5 and
[08-vehicles-and-models.md](08-vehicles-and-models.md).

### 4.2 Effective thickness

Each DM part may declare `armorThickness` and `armorEffectiveThicknessMax`. The
`armorEffectiveThicknessMax` field is a real native cap, not a display hint. The
viewer clamps a measured LOS to this cap when the part declares one. Example:
`track_r_dm` declares `armorThickness=20` and `armorEffectiveThicknessMax=20`,
but its collision hitbox spans the whole track loop.

### 4.3 Armor class and material modifiers

The armor classes live in `gamedata/damage_model/armor_classes.blk` (347
classes). The armor-class struct fields are:

| Offset | Field | Meaning |
|---|---|---|
| +0x04 | armorThickness | base thickness |
| +0x0c | armorEffectiveThicknessMax | effective-thickness cap |
| +0x10 | armorThrough | through-armor knob |
| +0x14 | armorQuality | scalar quality |
| +0x18 | {mech}ArmorQuality[] | per-mechanism quality (generic, cumulative, EFP, tandem) |
| +0x38 | {mech}EffectiveThicknessMax[] | per-mechanism cap |
| +0x58 | {mech}ThicknessEquivalentMax[] | per-mechanism equivalent |

Every effectiveness field is a scalar. No field in the BLK is angle-dependent.
The game combines the scalar quality with the incidence angle at runtime.

The armor classes are simulation categories, not always plain metallurgy
labels. Examples: `RHA_tank` (rolled), `CHA_tank` (cast), `RHA_tank_modern`,
`RHAHH_tank` (high hardness), `tank_structural_steel`. The class exposes an
optional `physMaterial` string.

The `armorQuality` scalar is the cast-versus-rolled style modifier. The
reverse-engineering notes do not publish the exact per-class quality numbers in
this file. Read them from `armor_classes.blk`. Confidence: **Partial** for the
runtime combine, **Confirmed** for the struct layout.

### 4.4 Composite and NERA directionality

Composite and NERA armor effectiveness is directional. The effectiveness is
low for a plunging or near-normal hit on the NERA sandwich. The effectiveness
is high for an oblique or frontal hit. A single scalar quality factor cannot
represent this behavior.

An `armorThrough` value below 0.1 marks a part as mesh-charged. Live records
show it on more than the class `leopard_2a5_turret_nera`: the M1A1 HC lower
front composite (360 mm nominal, quality 0.377) and two Leopard 2A5 turret
composite blocks (440 mm at quality 0.75 and 520 mm at quality 0.55) also carry
`armorThrough = 0.01`. The per-part charge rule for these parts is in
section 4.6. Do not use a flat `sqrt(genericArmorQuality)` factor for composite
classes.

### 4.6 Per-part charge and penetration carry (confirmed live)

Source: per-part hit records read live from the October 2026 Linux client. The
records were cross-checked against the spall-cone residuals, which match
`penetration on arrival − charge` exactly. Shell: 125 mm APFSDS with the
`apds_fs_long` preset. Targets: T-62, M1A1 HC, Leopard 2A5.

Let `T` be the nominal `armorThickness`, `q` the armor quality, `θ` the
geometric incidence angle between the shell path and the entry face normal,
`S(θ)` the slope value of the shell's preset, and `chord` the path length
through the collision mesh.

- **Plain parts:** `charge = q × T × S(θ)`. The game does not use the mesh
  thickness for these parts. Add-on skirts and screens of class
  `hull_side_special_armor` follow this rule from their nominal value, even
  where the mesh is thinner than the nominal. Examples: an M1A1 HC heavy skirt
  (65 mm, q 0.4) took 35.3 mm, and a Leopard 2A5 turret screen (80 mm, q 0.9)
  took 86.3 mm.
- **Mesh-charged parts:** `charge = q × chord × cos θ × S(θ)`. This covers
  classes with `armorThrough < 0.1` (composites and NERA), parts with
  `variableThickness`, and engine parts of class `armor_tank_engine`. The
  `chord × cos θ` term is the mesh thickness along the face normal. Errors were
  below 0.15 % on all composite records.
- **Thin crew, equipment and ammo parts:** `charge = q × T`, with no slope.
- **Caps:** the per-mechanism `{mech}EffectiveThicknessMax` of the class applies
  after the slope (for example 15 mm for wheels, 20 mm for tracks, 1.1 mm for
  crew), together with the part's `armorEffectiveThicknessMax`.
- **Cost:** the shell's penetration drops by the charge on mesh-charged parts,
  and by `max(charge, armorThrough)` on all other parts. Thus thin modules with
  `armorThrough = 10` cost 10 mm each, although their charge is below 1 mm.
- **Carry:** the game does not pass the residual on unchanged. It converts the
  residual to a speed state and computes the penetration again at the next
  part, with a random factor. The measured spread of
  `arrival / previous residual − 1` was −3.9 % to +2.3 % (mean −0.6 %, standard
  deviation 1.4 %, 32 pairs). This fits a uniform spread of about ±2.5 %, for
  example from a `pierceDispersion` of 0.05. The first penetration value also
  gets this spread.

The static read of this build found the armor class fields at `+0x04`
(`armorThickness`), `+0x18` (`armorThrough`) and `+0x1c` (`armorQuality`). These
offsets differ from the table in section 4.3, which comes from an older build.
Confidence: **Static** for these offsets.

### 4.5 Structural and volumetric checks (native)

War Thunder does not decide penetration from a BLK scalar. The game runs a
native per-hit 3D measurement against the collision mesh. The crosshair result
is a native struct that War Thunder serializes to the UI each frame. The struct
fields include:

```
isHovered, ricochetProb, penetratedArmor, realPenetration,
armorHit, headingAngle, needAngle, sightX0/Y0/X1/Y1
```

The UI value "Equivalent protection against the specified ammo" is
`params[src][id].generic` plus the sibling mechanism sums. The Squirrel combiner
is:

```
penetratedArmor = max over src of (
    generic + genericLongRod + explosiveFormedProjectile + cumulative,
    explosion,
    shatter )
```

`src` is `["lower","upper"]` for a penetrating result, or `["max"]` for a
blocked result. For simple kinetic AP, APFSDS, and APCBC rounds, `generic`
dominates and the other mechanisms are `0`.

Live confirmations (read off the game client):

| Value | UI result | Confirmed native field |
|---|---|---|
| 381 mm | possible | r8+0x214, exact |
| 469 mm | possible | r8+0x214, exact |
| 174 mm | possible | r8+0x214, ~3.5% off (cursor jitter) |
| 738 mm | not possible | generic = 737.765320 |

The viewer computes its own from-scratch value (collision-mesh LOS plus the
Lanz-Odermatt and De Marre formulas plus the slope tables). The viewer targets
these native numbers as calibration points.

## 5. Source and confidence summary

| Item | Source | Confidence |
|---|---|---|
| Drag law `V(d)=V0*exp(-k*d)` | binary + stat-card reproduction | Confirmed |
| `rho_air = 1.225` | drag law | Confirmed |
| Core kinetic `A*exp(B/(V/1000)^2)` | binary trace `0x5926378` | Confirmed |
| `0.001` km/s constant | .rodata `0x81fa430` | Confirmed |
| Lanz-Odermatt A, B (tungsten/DU) | binary + `protectionMapTestParams` | Confirmed |
| Lanz-Odermatt steel B path | binary decompile | Confirmed |
| `7850` target density | .rodata `0x888cf9c` (1/7850) | Confirmed |
| De Marre C and runtime | binary + BR-412D reproduction | Confirmed |
| `armorResistance = 1900.0` | `config/damagemodel.blk` | Confirmed |
| `maxArmorEffectiveScale = 20.0`, `armorBreachK = 7.0` | `config/damagemodel.blk` | Confirmed |
| Slope-effect tables | `slope_effect.blk` + reproduction | Confirmed |
| armorpower legacy tables | shell BLK `armorpower` | Confirmed |
| Ricochet tables/shape | `ricochet.blk` + live classify | Confirmed |
| Normalization term | `projectile_types/*.blk` field | Partial |
| Overmatch standalone rule | not found | Not reverse-engineered |
| Fuse `fuseDelayDist`, `explodeTreshold` | shell BLK | Partial |
| Spall cone data layout | `secondary_shatter_presets.blk` | Confirmed |
| Spall cone runtime (axis, random draw) | not traced | Not reverse-engineered |
| HE filler `explosiveMass`, `explosiveType` | shell BLK | Partial |
| Filler strength and brisance factors | `explosive.blk` `explosiveTypes` | Confirmed (data) |
| Module hp and hit rules | tank BLK `DamageParts`, `DamageEffects` | Confirmed (data) |
| Saved hit file format | `ReplayHits/*.blk` | Confirmed |
| HEAT standoff formula | not found | Not reverse-engineered |
| LOS `plate/cos(angle)` | live point + physics | Confirmed |
| `armorEffectiveThicknessMax` cap | binary parser `0x59748d0` | Confirmed |
| Armor-class struct layout | binary parser `FUN_059748d0` | Confirmed |
| Per-class quality numbers | `armor_classes.blk` | Partial |
| Composite/NERA directionality | live meow10/13/14 data | Not reverse-engineered |
| Native equivalent-protection value | live gdb capture | Confirmed |

Notes on estimated values:

- The Brinell hardness default `470` is a viewer fallback when the shell BLK
  omits `lanzOdermattBrinellHardnessNumber`. Mark it estimated for such shells.
- The `slopeEffect50deg` key stores an x value of `80.0`, not `50.0`. This is a
  game-data quirk, not a transcription error.
- The binary virtual addresses go stale on each weekly game patch. Verify the
  `aces` MD5 before any binary or debugger work.

## Aircraft note

Aircraft armor uses a different data model. The `DamageParts` group name is the
armor class. The parts carry only `hp` and `genericDamageMult`. The classes
resolve in `gamedata/flightmodels/dm/armorclasses.blk` (347 classes), not the
tank file. A composite group holds member weights (for example
`protected_controls = {steel: 0.3, armor5: 0.7}`). The extractor resolves a
group to a probability-weighted `armorThickness` plus a `compositeMembers` map.
See [08-vehicles-and-models.md](08-vehicles-and-models.md) for the geometry
side.

## Repository status

The formula constants in this file match the confirmed reverse-engineering
notes above. The composite and NERA directional case stays inaccurate, as
section 4.4 states.
