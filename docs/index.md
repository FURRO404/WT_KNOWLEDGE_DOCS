# WT Knowledge Docs

A knowledge bank for War Thunder (WT) reverse-engineering work. It holds what we
found about how the game stores data, how it talks on the wire, how it computes
combat, and how the world and the units are built.

## Chapters

| # | Chapter | Topic |
|---|---|---|
| 01 | [Glossary](01-glossary.md) | Terms and abbreviations |
| 02 | [File formats](02-file-formats.md) | VROMFS, BLK/DataBlock, assets, the datamine |
| 03 | [Replays](03-replays.md) | The `.wrpl` replay format and parsers |
| 04 | [Localhost 8111 API](04-localhost-8111-api.md) | The local web API on port 8111 |
| 05 | [Char server API](05-char-server-api.md) | The online `char` server API and JWT auth |
| 06 | [Ballistics and armor](06-ballistics-and-armor.md) | Ballistics, penetration, armor |
| 07 | [Terrain and maps](07-terrain-and-maps.md) | Terrain decode, maps, coordinates |
| 08 | [Vehicles and models](08-vehicles-and-models.md) | Vehicles, models, camos, X-ray, damage model |
| 09 | [Heatmaps and coordinates](09-heatmaps-and-coordinates.md) | Heatmaps and coordinate encoding |
| 10 | [Tooling and repos](10-tooling-and-repos.md) | The repositories and tools |

## How the pieces fit

The game ships its data in VROMFS containers of BLK blocks (chapter 02). The
datamine is that data unpacked. A match writes a `.wrpl` replay of BLK plus a
packet stream (chapter 03). While a match runs, the game answers a local web API
on port 8111 (chapter 04) and talks to the online `char` server (chapter 05).

Chapter 06 covers the combat math. Chapters 07 and 08 cover the world and the
units that move in it, from the static datamine. Chapter 09 covers how we store
positions and paint heatmaps. Chapter 10 lists every repository and where to
read more.

## Data sources, in short

- Datamine: static game files. Truth for shell stats, armor, models, levels.
- Replay (`.wrpl`): the recorded state of one match.
- Port 8111: a live, local, read-only telemetry feed while you play.
- `char` server: the online account and inventory API.

## Data

Reference data files live in the `data/` directory of the repository:

- [`level_catalog.json`](https://github.com/FURRO404/WT_KNOWLEDGE_DOCS/blob/master/data/level_catalog.json)
  — every level's key, path, localized names, map extents, and per-mission
  lists. 170 levels and 1056 missions, from datamine 2.58.0.24. See
  [chapter 07](07-terrain-and-maps.md).

## Sources

These public repositories back the facts in this bank. Chapter 10 lists them
with their role, and each chapter names its own initial research and
contributors at the top.

Game engine and data:

- DagorEngine — https://github.com/GaijinEntertainment/DagorEngine
- War Thunder Datamine — https://github.com/gszabi99/War-Thunder-Datamine

Format tools:

- wt-tools — https://github.com/klensy/wt-tools
- Dagor Asset Explorer — https://github.com/quentin-dh/Dagor-Asset-Explorer
- wt_ext_cli (WOSF) — https://github.com/Warthunder-Open-Source-Foundation/wt_ext_cli
- wt_blk (WOSF) — https://github.com/Warthunder-Open-Source-Foundation/wt_blk
- WtFileUtils — https://github.com/LivingTheDagor/WtFileUtils
- WOSF organization — https://github.com/Warthunder-Open-Source-Foundation

Replays:

- WrplReplayParser — https://github.com/LivingTheDagor/WrplReplayParser
- wrpl-inspector — https://github.com/maxsupermanhd/wrpl-inspector (the carve and ingest work started in the now-archived https://github.com/maxsupermanhd/wrpl-inspector-private and moved here)
- wt_sensor (WOSF) — https://github.com/Warthunder-Open-Source-Foundation/wt_sensor

Ballistics:

- wt_ballistics_calc (WOSF) — https://github.com/Warthunder-Open-Source-Foundation/wt_ballistics_calc

Maps, heatmaps, stats:

- wt-heatmaps — https://github.com/maxsupermanhd/wt-heatmaps
- Minimap pictures — https://github.com/LivingTheDagor/WtMiniMapPictures

## Credits

- Compiled by FURRO404 (https://github.com/FURRO404).
- Reviewed and redacted by llamaz (https://github.com/llama-for3ver).
- Reviewed, with editorial advice, by Max (https://github.com/maxsupermanhd).

Each chapter names its initial research and its contributors at the top.
