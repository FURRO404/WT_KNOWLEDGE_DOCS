# 12 — Squadron Realistic rating

This chapter summarizes the War Thunder rating used in Squadron Realistic
Battles (SRE, also called SQB): where its rating values are stored, the
relevant datamined settings, observed win/loss changes, and what is still
unknown about the calculation.

Evidence labels:

- **[datamine]**: a value present in unpacked game files.
- **[API]**: a field present in the game's `char` server response.
- **[reported]**: a match-award observation shared by players; not independently
  reproduced from raw before/after API captures here.
- **[inferred]**: a conclusion consistent with current evidence, but not
  established as the server's exact calculation.

For `char` server transport and BLK response details, see
[05 — Char server API](05-char-server-api.md).

---

## 1. Personal rating and squadron rating

The `char` server's `cln_clan_get` response contains the squadron roster in
`members`, per-member ratings in `member_ratings`, and the aggregate squadron
rating in `astat`. Personal and aggregate ratings use the field
`dr_era5_hist`. [API]

The personal SRE rating is `member_ratings[uid].dr_era5_hist`. The squadron
rating is `astat.dr_era5_hist`. They are different ratings. A player's TSS
tournament rating is also a separate value and should not be used as their SRE
rating. [API]

## 2. Relevant datamined settings

The unpacked file `char.vromfs.bin_u/config/game_settings.blkx` has a
`clanDuel` block with these settings: [datamine]

| Setting | Value |
|---|---:|
| `useSingleEra` | `true` |
| `fastGrowthLimit` | 1500 |
| `tier1Limit` | 2100 |
| `tier2Limit` | 2400 |
| `tier1EloK` | 32 |
| `tier2EloK` | 24 |
| `tier3EloK` | 16 |

The block also contains three periodic diminishing multipliers: 0.9, 0.8,
and 0.5, each with a seven-day period. [datamine] The settings identify rating
parameters and thresholds. They do not by themselves specify the complete
per-match personal-rating calculation or how each diminishing setting is
applied.

The K values are not fixed awards for wins or losses. A K value of 32 does not
mean every player receives +32 for a win or loses exactly 32 for a loss.
Expected score, opponent or team ratings, rounding, and other server-side
details may change the awarded amount. [inferred]

## 3. Reported win and loss awards

Player-reported examples show the general pattern below. The ranges are
approximate examples, not a complete rating schedule. [reported]

| Player points | Reported points per win | Reported points per loss |
|---:|---:|---:|
| 0–800 | about +32 | about −1 |
| 1500 | about +16 | about −16 |
| 1850 | about +4 | about −28 |
| 1865 | about +3 | about −29 |
| 2000 and above | about +1 | about −31 to −32 |

The examples suggest wins become smaller and losses larger as personal points
rise. Awards near a threshold can vary between matches; this table should not
be treated as a deterministic lookup table. [reported]

Players have also reported that the relative standing of the two teams affects
the win/loss change. The size and exact use of that effect have not been
established from the settings file or a controlled sample of before/after
personal ratings. [reported; unknown mechanism]

## 4. What remains unknown

The `clanDuel` data is configuration, not the rating implementation. The
sources checked so far do not reveal:

- the full equation used to calculate a personal award;
- whether the calculation compares individual ratings, team averages, or both;
- the exact effect of the opponent's rating and the team's combined rating;
- how the periodic diminishing values affect personal ratings;
- all rounding rules, caps, or special cases.

Therefore an exact number of wins or matches to reach a target cannot be
derived from the datamine alone. Any estimate needs match-by-match personal
ratings before and after games, results, and both teams' ratings. Samples
across rating levels and both wins and losses are needed to separate personal
rating effects from opponent strength and time-based changes.

---

## Sources

- Unpacked datamine: `char.vromfs.bin_u/config/game_settings.blkx`,
  `clanDuel` block. [datamine, checked 2026-10-16]
- War Thunder `char` server: `cln_clan_get` BLK fields `members`,
  `member_ratings`, and `astat`. [API; see chapter 05]
- Player-reported award examples and relative-team-standing note, shared
  2026-10-16. These have not been independently reproduced from raw match
  records. [reported]
