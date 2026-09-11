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
slopeEffect50deg = (80.0, 1.01499999)   # name says 50, x value is 80
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

### 2.9 Normalization

The shared projectile-type BLK carries a `normalizationPreset` field (see
`gamedata/damage_model/projectile_types/*.blk`). The reverse-engineering notes
did not recover a separate numeric normalization term. The stat-card angle
behavior is fully explained by the `slope_effect.blk` preset table above. Treat
a distinct normalization angle as folded into the slope table. Confidence:
**Partial**.

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
`ap` preset carries residual-penetration and caliber-to-armor multipliers for
post-penetration shatter. The BLK also carries a `stabilityThreshold` field.

The notes do not give an explicit spall-cone half-angle or fragment-count
formula. Confidence: **Not reverse-engineered** as a geometric cone.

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

The notes do not give the TNT-equivalent conversion factor per filler type. Do
not invent a conversion factor. Confidence: **Not reverse-engineered**.

### 3.4 HEAT standoff

The armor-class struct carries per-mechanism quality arrays. The mechanism keys
include `cumulative` (HEAT), `explosiveFormedProjectile` (EFP), and
`tandemPrecharge`. The native protection result reports these mechanisms in the
`penetratedArmor` sum.

The notes do not give a HEAT standoff-versus-penetration formula, and they do
not give a cumulative jet decay constant. Confidence: **Not reverse-engineered**.

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

The class `leopard_2a5_turret_nera` is the only class of 347 with
`armorThrough = 0.01`. All other classes have `armorThrough >= 1.0`. The
`armorThrough` field at offset +0x10 is the suspect runtime knob for NERA. The
exact directional formula is **Not reverse-engineered**. Do not use a flat
`sqrt(genericArmorQuality)` factor for composite classes as an exact number.

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
| Spall cone geometry | `secondary_shatter_presets.blk` (fields only) | Not reverse-engineered |
| HE filler `explosiveMass`, `explosiveType` | shell BLK | Partial |
| TNT-equivalent factor | not found | Not reverse-engineered |
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
