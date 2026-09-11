# 01 — Glossary

This section gives the terms and abbreviations used in the bank. Each entry
names the section that covers the term in full.

## Engine and files

- **Dagor** — the WT game engine. The source is in the `DagorEngine`
  repository. See [02](02-file-formats.md).
- **VROMFS** — a Dagor container file (`.vromfs.bin`, unpacked as `.bin_u`). It
  holds many BLK files, often zstd-packed. See [02](02-file-formats.md).
- **BLK / DataBlock** — the Dagor block data format. It holds a tree of named
  parameters. It has a text form and a binary form. See [02](02-file-formats.md).
- **FAT** — a binary BLK layout. The first byte is `0x01`. See [02](02-file-formats.md).
- **BBF3** — a binary BLK layout that starts with `\0BBF`. The `char` server
  answers this form. See [02](02-file-formats.md), [05](05-char-server-api.md).
- **`.blkx`** — a JSON copy of a BLK file, used by the public datamine mirror.
  See [09](09-heatmaps-and-coordinates.md).
- **DDSx / dxp** — the Dagor texture format and its pack. See [02](02-file-formats.md).
- **clog** — an encrypted log/stream form in a replay. See [03](03-replays.md).
- **datamine** — the game files unpacked to a folder tree. The local copy is the
  `War-Thunder-Datamine` repository. See [02](02-file-formats.md), [10](10-tooling-and-repos.md).

## Replays and live feeds

- **`.wrpl`** — the WT replay file. It holds a header, settings BLK, results,
  and a per-tick packet stream. See [03](03-replays.md).
- **8111** — the local web server the game runs while you play. It answers
  telemetry as JSON. See [04](04-localhost-8111-api.md).

## Online API

- **`char` server** — the online account, unlock, and inventory API. See
  [05](05-char-server-api.md).
- **`cln_*`** — the action names the `char` server accepts, for example
  `cln_buy_resource`. See [05](05-char-server-api.md).
- **JWT** — the JSON Web Token that authenticates a `char` request. See
  [05](05-char-server-api.md).

## Combat math

- **DeMarre** — the base equation family for shell penetration. See
  [06](06-ballistics-and-armor.md).
- **APHE / APDS / APFSDS / HEAT / HE** — shell types. See [06](06-ballistics-and-armor.md).
- **line-of-sight thickness** — plate thickness divided by the cosine of the
  hit angle. See [06](06-ballistics-and-armor.md).
- **X-ray / DM** — the damage model: modules, crew, and ammo inside a vehicle.
  See [08](08-vehicles-and-models.md).

## World and units

- **HM2** — a heightmap block. It decodes with the ooz/Kraken (Oodle) codec.
  See [07](07-terrain-and-maps.md).
- **LandRayTracer / lmap / gridHt** — the full-level heightfield. See
  [07](07-terrain-and-maps.md).
- **RIGz / rendinst** — the prop block: buildings and trees placed by matrix.
  See [07](07-terrain-and-maps.md).
- **landclass / albedo** — the biome-to-texture chain that bakes the ground
  color. See [07](07-terrain-and-maps.md).
- **dynaf composit** — the dynamic airfield placed on air maps. See
  [07](07-terrain-and-maps.md).
- **TMatrix** — a Dagor 4x3 transform matrix. It is BLK param type `0x0b`
  (`FLOAT12` / `m4x3f`), 48 bytes. See [02](02-file-formats.md).
- **ECS** — the entity component system the game uses. Replays carry net ECS
  messages. See [03](03-replays.md).

## Tools

- **wt-tools** — the Python format decoders. See [02](02-file-formats.md).
