# 13 — Missions and battle rules

> Initial research: FURRO404. https://github.com/FURRO404
> Contributors: War-Thunder-Datamine by gszabi99.

This chapter covers the rules that a mission sets for a battle. For the level
and its terrain, see [07-terrain-and-maps.md](07-terrain-and-maps.md). For the
replay objects that carry mission state, see [03-replays.md](03-replays.md).

## 1. Air battle bases (bombing areas)

### 1.1 The bombing area

- A base is a "bombing area". A mission makes one with the
  `missionSetBombingArea` action. Its keys include `target`, `army`, `hp`,
  `use_variable`/`var_value` (take `hp` from a mission variable), `airfield`,
  `isAirfield`, `isUnit`, `hpFireMult`, `fireSpeed`, `spawnEffect`, and
  `runwayWidth`. Other actions are `missionGetBombingAreaHP`,
  `missionBombingAreaDamage{damageHP}`, and `missionIsBombingAreaDestroyed`.
  [verified, datamine 2026-10]
- Base bleed: `hpFireMult` is the integrity fraction below which the base
  burns down by itself, and `fireSpeed` is the burn rate as a fraction of full
  health per second. The base templates use `hpFireMult 0.1` and
  `fireSpeed 0.03`: below 10% the base loses 3% per second, so it dies in
  about 3 s. Replays show the same: the bleed starts only below 0.100, and it
  removes 0.00246 per 0.082 s step (0.030 per second). [verified, datamine and
  11 server replays, 2026-10]
- Thus a base dies when the bombs remove more than 90% of its health.
  [verified]
- Event and PvE missions set a fixed `hp` in the mission file (8000 to 30000
  for most events; 105000 and 320000 for the Korea "Black Thursday" events).
  [verified, datamine 2026-10]
- `aces.vromfs.bin_u/config/gameparams.blkx` holds
  `bombingZoneHpToTntEquivalentTons: 0.000125`. Its use is not known.
  [verified key only]

### 1.2 Base health by battle rank

Random air battles import a base template. Each template reads the battle's
balance level with `missionGetBalanceLevel` and sets the health variable.
[verified, datamine 2026-10]

`templates/enduring_confrontation/bdt_bases_destroy_template.blk` (the
`*_bfd_norespawn` Air Realistic missions, respawning bases):

| Balance level | Base HP |
|---|---|
| 0–3 | 4000 |
| 4–7 | 6000 |
| 8–11 | 10000 |
| 12–16 | 16000 |
| 17–20 | 22000 |
| 21+ | 25900 |

- The template comments say "dlya istorii" (for Realistic). The template has
  no Arcade factor. In helicopter mode (`bdt_mission_mode = "heli"`) it
  divides the health by 10.
- Template defaults: `bdt_t1_total_bases_max_count 3`,
  `bdt_t1_active_bases_max_count 2`, `bdt_respawn_time 240`. Missions change
  the total count (seen 7, 8, 9, 11, 13, 17 to 21) and the respawn time (seen
  120). A destroyed base comes back after the respawn time.
- If the balance level is the economic rank (BR = 1.0 + level / 3), the
  bracket edges fall between BR 2.0/2.3, 3.3/3.7, 4.7/5.0, 6.3/6.7, and
  7.7/8.0. This mapping is not proven here.

`templates/destroy_bomb_areas_template.blk` (the older `*_gs` ground strike
missions, bases that do not respawn):

| Balance level | Base HP (Realistic) | Arcade factor | Zones |
|---|---|---|---|
| 0–3 | 6000 | 2.5 | 3 |
| 4–7 | 8000 | 3.2 | 3 |
| 8–11 | 10000 | 3.2 | 3 |
| 12–16 | 12000 | 4.2 | 4 |
| 17+ | 12000 | 4.2 | 4 |

- In Arcade the template multiplies the health by the factor (for example
  6000 × 2.5 = 15000). It also multiplies by `bomb_areas_spawns_count` when
  that variable is above 0.
- The datamine does not show which of these missions are in the current
  match rotation.

### 1.3 Bomb damage against a base

- `char.vromfs.bin_u/config/wpcost.blkx` gives each aircraft weapon preset a
  `weaponDamage`: the sum of the base damage of its bombs. For example, Tu-4
  presets: 40 × FAB-100 = 55760, 20 × FAB-500 = 118800, 8 × FAB-1500 = 97504,
  4 × FAB-3000 = 79200. [verified, datamine 2026-10]
- A bomb removes `weaponDamage / baseHP` of the integrity. Server replays at
  the 25900 bracket give exact matches (measured drop → value × 25900):

  | Bomb | Damage | Drop measured | Expected |
  |---|---|---|---|
  | Mk 82 / AGM-154A1 | 2464 | 0.09513 | 0.09514 |
  | LS-6 500 | 3808 | 0.14702 | 0.14703 |
  | FAB-500M-62 (×2) | 6307 | 0.48699 | 0.48703 |
  | Grom-2 | 8051 | 0.31086 | 0.31085 |
  | Mk 84 / GBU-64 | 10983 | 0.42404 | 0.42405 |
  | FAB-1500M-54 | 12188 | 0.47056 | 0.47058 |
  | FAB-3000 UMPK | 24236 | 0.93812 | 0.93575 + one bleed step |

  [verified, 11 server replays, 2026-10]
- The damage does not scale linearly with explosive mass. Many small bombs do
  more base damage than one large bomb of the same explosive mass: 4 × FAB-500
  (4 × 325 kg TNT) = 23760, but one FAB-3000M-46 (1400 kg TNT) = 19800.
  [verified, datamine]
- Incendiary bombs: the `weaponDamage` value is the total of the impact and
  the burn. The impact gives about 65–70% of it, and the fire gives the rest
  over about 30 s (the bomb's `fireDamage.lifeTime` is 30). ZB-500 and BLU-27/B
  (12943): impact 0.34916 = 9043, then 0.00502 (130 HP) per bomb per second.
  Mk 77 mod 4 (10860): impact 0.27375 = 7090. [verified, server replays
  2026-10]
- Some integrity drops (0.0597 steps, about 1 s apart) had no bomb near them.
  Their cause is not known.

### 1.4 Reward multiplier for bases

`gui.vromfs.bin_u/globals/econweaponutils.nut` (`getPresetRewardMul`)
calculates the multiplier that the loadout screen shows, with the
`BombingRewardMultipliers` block of `char.vromfs.bin_u/config/warpoints.blkx`
(`presetDmgMin 18000`, `presetDmgMax 97500`, `bombingRewardModifier 2.0`,
`fighterBombingRewardMul 0.8`, `premBombingRewardMul 1.2`). D is the preset
`weaponDamage`. [verified, datamine 2026-10]

```
if D >= 200000: mul = interpolate(piecewiseLinearTable, D)
                # [200000, 0.3], [1200000, 0.17], [50000000, 0.017]
else:
    scale = 1 + (2.0 - 1) * (D - 18000) / (97500 - 18000)
    mul   = scale * 18000 / D
    if the unit has costGold (premium): mul *= 1.2
    mul = min(mul, 1.0)
if unitClass == "exp_fighter": mul *= 0.8
```

The UI shows `mul × 10`. Thus the cap is 10, and 8 for fighters. A smaller
preset gets a higher multiplier. The formula gives the community chart's value
for 11 of 11 checked loadouts (for example Tu-4 20 × FAB-500: 3.44; IL-28
4 × FAB-500: 8.12; a fighter with 2 × BLU-27: 6.1).

### 1.5 Base integrity in replays

The replicated `BombingZone` object (zone kind 5) carries `curZoneIntegrity`
(reflection field 0x43, `float`). It is 1.0 for a full base and 0.0 when the
base is destroyed. The server sends it on each change, so each bomb hit shows
as one step. Join the steps to bomb entities by their end time (within about
0.1 s) to get the damage of each bomb. [verified, server and client replays,
2026-10]

### 1.6 Community chart: claims that the game files do not support

A community bomb chart (Google Sheets, version 2.28, 2026-10-11,
https://docs.google.com/spreadsheets/d/1oNwp_MXszU5J2dcaz5IoCtSAQ-infPdOWhwtJXqtrwU)
uses the `wpcost` damage values, the bdt health table of 1.2, and
`ceil(baseHP × 0.9018 / damage)` bombs for each base. These parts agree with
1.1 to 1.4. Two claims do not agree with the templates:

- "On 3-base maps a base takes about half the payload." The gs template
  (1.2) gives 6000, 8000, 10000, 12000, 12000 HP. That is more than the bdt
  health at low rank and about half only at the top ranks.
- "In Arcade, bases that do not respawn have two times the health." The gs
  template uses factors of 2.5 to 4.2, not 2.
