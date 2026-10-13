# data

Reference data files that back the docs. These are datamine-derived, not code.

| File | Description | Doc |
|---|---|---|
| `level_catalog.json` | Every level: key, level path, localized names, map extents, and per-mission lists. 170 levels, 1056 missions, from datamine 2.58.0.24. | [../docs/07-terrain-and-maps.md](../docs/07-terrain-and-maps.md) |
| `dm_part_names_2.59.json` | Global damage-model part id to part name (5,076 names), built from `config/damagemodelparts.blk` of game 2.59. Replay part-kill messages use these ids. | [../docs/03-replays.md](../docs/03-replays.md) |

Put a new reference file here and add a row above. Keep the file datamine-derived
and non-sensitive.
