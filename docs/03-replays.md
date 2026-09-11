# 03 — War Thunder replays (`.wrpl`) and replay tooling

> Initial research: wrpl-inspector by maxsupermanhd (flexcoral), 2025-09-23. https://github.com/maxsupermanhd/wrpl-inspector
> Contributors: WrplReplayParser by LivingTheDagor; wt_sensor by the Warthunder-Open-Source-Foundation.

This page documents the War Thunder replay file format (`.wrpl`) and the tools
that read it. It uses real field names, byte offsets, and packet types from the
source code of two projects:

- `WrplReplayParser` — a C++ parser with Python bindings.
- `wrpl-inspector` — a Go library and GUI.

For the Dagor `BLK` (DataBlock) and `VROMFs` container formats that the header,
settings, and results sections use, see
[02-file-formats.md](02-file-formats.md).

---

## 1. The `.wrpl` container

### 1.1 File identity and versions

A `.wrpl` file starts with two `uint32` values:

- `header` at offset 0. Its value is `0x1000ACE5`. On disk the first four bytes
  are `E5 AC 00 10` (little-endian). Every parser checks these four bytes. Do
  not confuse it with the next field.
- `magic` at offset 4. This is the format version, and it changes each major
  game version. The current value is `0x00018C0B`. `WrplReplayParser` calls it
  `CURR_MAGIC`. The dev-server value is `0x00018C0A`. The parsers name the
  supported version "18c0b".

The C++ and Go parsers check `magic == CURR_MAGIC` and reject an unknown
version.

### 1.2 The fixed header (1234 bytes)

Every `.wrpl` file, finished or live, starts with a packed C struct of exactly
1234 bytes. `WrplReplayParser`'s `ReplayHeader` (in `ReplayStructs.h`) is the
authority. The struct uses `#pragma pack(push, 1)`, so there is no padding.
`static_assert(sizeof(ReplayHeader) == 1234)` fixes the size.

| Offset | Type | Field | Meaning |
|---|---|---|---|
| 0 | `uint32` | `header` | File identifier `0x1000ACE5`. |
| 4 | `uint32` | `magic` | Format version (`0x00018C0B`). |
| 8 | `char[128]` | `level_path` | Level asset path, for example `levels/avg_guadalcanal.bin`. NUL-terminated. |
| 136 | `char[260]` | `mission_file` | Mission `.blk` path. |
| 396 | `char[128]` | `mission_name` | Mission or game-mode name. |
| 524 | `char[128]` | `environment` | Environment name. |
| 652 | `char[32]` | `weather` | Weather name. `offsetof(weather) == 0x28C` is asserted. |
| 684 | `uint32` | `footer_blk_offset` | Byte offset of the results/footer BLK. It is 0 when the file has no results block. |
| 688 | `uint64` | `difficulty_part_1` | Difficulty settings, part 1. |
| 696 | `uint64` | `difficulty_part_2` | Difficulty settings, part 2. |
| 704 | `char[20]` | `unk0` | Unknown. |
| 724 | `uint32` | `SessionType` | Session type. |
| 728 | `uint32` | `player_count` | Player count. |
| 732 | `uint64` | `session_id` | Match identifier. Every part of one match shares it. |
| 740 | `uint8` | `replay_part_number` | Ordinal of this file in a server replay part sequence. |
| 741 | `uint8` | `unk1` | Unknown. See the server-detection note below. |
| 742 | `uint16` | `segmentLengthSec` | Server segment length in seconds. |
| 744 | `uint32` | `skiesInitialRandomSeed` | Sky random seed. |
| 748 | `uint16` | `settings_blk_size` | Size in bytes of the settings BLK after the header. |
| 750 | `char[29]` | `unk3` | Unknown. |
| 779 | `bool` | `isWorldWar` | World War mode flag. |
| 780 | `char[128]` | `location_name` | Localized location name. |
| 908 | `uint32` | `start_time` | Match start time, Unix seconds. |
| 912 | `uint32` | `time_limit` | Match time limit, seconds. |
| 916 | `uint32` | `score_limit` | Match score limit. |
| 920 | `uint32` | `killLimit` | Match kill limit. |
| 924 | `uint32` | `gameType` | Game type. |
| 928 | `uint32` | `restoreType` | Restore type. |
| 932 | `int32` | `playerNo` | Index of the player who recorded the file. A server replay uses the sentinel `0x80000000`. |
| 936 | `uint32` | `unk4` | Unknown. |
| 940 | `uint32` | `numAttempts` | Attempt count. |
| 944 | `uint32` | `maxAttempts` | Maximum attempts. |
| 948 | `bool` | `isAttempts` | Attempts flag. |
| 949 | `bool` | `isLimitedAmmo` | Limited-ammo flag. |
| 950 | `bool` | `isLimitedFuel` | Limited-fuel flag. |
| 951 | `char[13]` | `unk5` | Unknown. |
| 964 | `uint32` | `gameMode` | Game mode. |
| 968 | `char[128]` | `chapterName` | Chapter name. |
| 1096 | `char[128]` | `battle_kill_streak` | Battle kill-streak string. |
| 1224 | `uint16` | `snapshotPeriodSec` | Snapshot period in seconds. |
| 1226 | `uint64` | `gameVersion` | Game version. |

`wrpl-inspector`'s Go `WRPLHeader` struct maps the same layout with different
field names (for example `Raw_Level`, `Raw_LevelSettings`, `ResultsBlkOffset`,
`SettingsBLKSize`, `StartTime`).

**Server-replay detection uses two different methods.** `wrpl-inspector` tests
the byte at offset 742 for `0x5A` (`isServer`). `WrplReplayParser` tests
`playerNo == 0x80000000` instead. A server replay has no local player.

### 1.3 Section layout

The header defines the position of every later section:

```
[0, 1234)                                   ReplayHeader (fixed)
[1234, 1234 + settings_blk_size)            settings BLK  (optional)
[zlib_offs, footer_blk_offset or EOF)       zlib packet stream
[footer_blk_offset, EOF)                     results/footer BLK (optional)
```

`WrplReplayParser` computes:

- `zlib_offs = sizeof(ReplayHeader) + settings_blk_size` (that is `1234 +
  settings_blk_size`).
- `zlib_size = footer_blk_offset - zlib_offs` when `footer_blk_offset` is set.
- `zlib_size = file_size - zlib_offs` when `footer_blk_offset == 0` (no results
  block; the stream runs to the end of the file).

### 1.4 The datablock parts (settings and footer)

Two sections are Dagor `BLK` (DataBlock) blobs. See
[02-file-formats.md](02-file-formats.md) for the BLK format.

- **Settings BLK.** It sits right after the header, and its length is
  `settings_blk_size`. It holds the mission and match settings. `WrplReplayParser`
  loads it into `header_blk` with `DataBlock::loadFromStream`. `wrpl-inspector`
  reads `SettingsBLKSize` bytes into `Settings`.
- **Footer / results BLK.** It exists only when `footer_blk_offset != 0` — that
  is, only after the game finalizes the match. It holds the post-match results
  (players, scores, awards). `WrplReplayParser` loads it into `footer_blk`.
  `wrpl-inspector` seeks to `ResultsBlkOffset` and reads to the end. A client
  replay recorded locally may have no footer.

---

## 2. The packet stream

### 2.1 Compression

The section between the settings BLK and the footer is a raw **zlib deflate**
stream. Each parser inflates it with a standard library:

- `WrplReplayParser` uses `libdeflate` (`libdeflate_zlib_decompress`). It can
  decompress the whole stream at once (`FullDecompressReplayReader`) or stream
  it packet by packet (`CompressedReplayReader`).
- `wrpl-inspector` uses `compress/zlib` (`zlib.NewReader`) as a streaming
  reader.

### 2.2 Packet framing

The inflated stream is a sequence of packets. Each packet has a variable-length
size prefix, then a body.

**Size prefix.** `getPacketSize` in `WrplReplayParser` decodes it as follows:

1. Read the first byte.
2. If bit `0x80` is set, the size is `first & 0x7F` (one byte, values 0–127).
3. Otherwise the highest set bit among `0x40`, `0x20`, `0x10` selects a 1, 2, or
   3 byte big-endian continuation. Accumulate the value from the first byte
   forward, then XOR out the length selector: `0x4000` for one byte, `0x200000`
   for two, `0x10000000` for three.
4. If none of those bits is set, the next four bytes are a raw little-endian
   `uint32`.

`writePacketSize` in `WrplReplayParser` is the inverse and writes the smallest
form that fits. A prefix of size 0 is padding, not a packet.

**Body.** The first two bytes of the body are a `uint16` `type_t` (the packet
type). The timestamp follows a rule that saves space:

- If `(type_t & 0x10) == 0`, the next four bytes are a little-endian `uint32`
  millisecond timestamp. It becomes the new running time.
- If `(type_t & 0x10) != 0`, the parser strips the `0x10` bit and the packet
  inherits the running time of the last timestamped packet.

So two packets with the same timestamp encode the time only once, on the first.
The packet body (after the type and the optional timestamp) is the payload.

### 2.3 Packet types

`WrplReplayParser`'s `ReplayPacketType` enum and `wrpl-inspector`'s name table
agree:

| Value | Name | Meaning |
|---|---|---|
| 0 | `EndMarker` | Last packet in a replay. |
| 1 | `StartMarker` | Start marker. Meaning not fully known. |
| 2 | `AircraftSmall` | Aircraft flight-model state. |
| 3 | `Chat` | Chat message. |
| 4 | `MPI` | MPI network message. Carries unit movement and battle messages. |
| 5 | `NextSegment` | Names the next server replay file. Usually the last packet of a part. |
| 6 | `ECS` | Network ECS message (entity/component state). |
| 7 | `Snapshot` | Snapshot. |
| 8 | `ReplayHeaderInfo` | ECS message hashes for synchronization. Seen in older or server replays. |

### 2.4 Per-tick unit state

Timing works in milliseconds. Each packet carries `timestamp_ms`, either its own
or the inherited running time. A parser records each unit position as a
time-stamped sample. `wrpl-inspector`'s `game.SpaceTime` is `{Time uint32, X,
Y, Z float64}`. `WrplReplayParser`'s `unit::Unit` keeps a `positions` vector of
`SpaceTime{time_ms, Point3 location}`. `snapshotPeriodSec` and
`segmentLengthSec` in the header set the snapshot and segment cadence.

**Ground vehicles.** Movement rides in MPI (type 4) packets. `wrpl-inspector`'s
movement parser matches a fixed byte pattern at the packet start, reads a
compressed entity id, then reads three little-endian `float64` values at byte
offsets 11, 19, and 27 (plus the byte offset that the compressed id consumed).
`wrpl-inspector`'s README calls this "full precision ground unit movement".

**Aircraft.** Type 2 packets carry flight-model records: position and
orientation samples, plus one sensor-state record per onboard sensor. Sensor
type 1 is radar-like, type 2 is IRST-like, type 4 is unknown, and type 3 is not
seen in captured replays. Each sensor record ends with an optional contact list:
up to 63 `uint32` entries, each `0xFFFF0000 | unit_uid`, which name the units
that the sensor detects. `WrplReplayParser`'s `PositionSync.cpp` decodes the
same records and unpacks quantized fields with `netutils::UNPACKS<int16_t>` at a
scale (for example `PI` for angles).

The numeric type codes above are the replay runtime layer. The static sensor
definitions live in the datamine. [wt_sensor](https://github.com/Warthunder-Open-Source-Foundation/wt_sensor)
parses those BLK files. It models a radar as a set of transceivers with types
`pulse`, `pulseDoppler`, `hprf`, and `mprf`, and it models IRST as a transceiver
with `visibilityType: infraRed`. The datamine names the kinds by string, not by
the replay's numeric code.

**Guided weapons.** Rocket, bomb, and torpedo sync rides in the MPI/flight
stream. Positions use bit-packed quantized values (`netutils::read_vector`,
`UNPACKS`). Weapon and armor context
is in [06-ballistics-and-armor.md](06-ballistics-and-armor.md).

**ECS (type 6).** ECS packets define entities, templates, and components, and
carry incremental per-entity updates. `wrpl-inspector`'s `ecs2` package decodes
this wire format. Key points:

- Components are named by hash. `WrplReplayParser` loads hashes from templates
  and, where needed, from `char.vromfs.bin` (see
  [02-file-formats.md](02-file-formats.md)).
  [wrpl-inspector](https://github.com/maxsupermanhd/wrpl-inspector)
  ships the same table as `ecshashes.json`: a `components` map (186 entries,
  `hash -> type name`, for example `0xbf9bf563 -> net::Object`) and a
  `dataComponents` map (`hash -> {name, comp}`, for example
  `0x6c81acdd -> {name:"eid"}`).
- Some ECS snapshots are LZ4-compressed.
- Field tables use an `IdFieldSerializer` (32-field and 255-field variants). A
  field size is a 3-bit selector into `[0, 1, 8, 16, 32, 64, 96, 128]` bits; a
  selector of 0 means a varint size follows. The `idfieldserializer` package in
  wrpl-inspector confirms this table. It also shows both variants start
  byte-aligned: the 32-field variant reads a `uint16` offset then a compressed
  bitmask, and the 255-field variant reads a `uint16` offset then a `uint16`
  where the low 12 bits are the field count and the top 4 bits are the
  bits-per-index.
- An entity id (`eid`) carries generation bits, because the engine recycles
  index numbers. Parsers keep the full `eid`, not the bare index.
- ECS carries the domain identity: a unit `uid`, an owner `playerId`, the unit
  class or mission name, and the loadout in a `*StorageComponent`.

**Other in-packet compression.** LZ4 covers ECS snapshots as noted above.

### 2.5 The clog decryptor is not part of the packet stream

`WrplReplayParser` ships a separate tool, `ClogDecryptor`. It decrypts Gaijin
encrypted client debug logs (`.clog`), not the `.wrpl` packet stream. It XORs
the bytes with a fixed 128-byte key and a rolling index (`data[i] ^
xor_key[index % xor_key_len]`). It stops at the marker string
`flush_all_std_and_debug`. Keep it separate from replay parsing; it helps
reverse-engineering only.

### 2.6 Multi-part server replays

The game splits a server-recorded match into several `.wrpl` part files.

- Every part shares the same `session_id`. A parser rejects a set with mixed
  session ids.
- Server parts sort by `replay_part_number`. Part 0 must exist.
- The game interleaves short state parts (even numbers) with packet-stream parts
  (odd numbers). The odd parts form the continuity sequence 1, 3, 5, and so on.
  A parser checks that the odd parts increase by two with no gap.
- Each part has its own zlib stream and its own running timestamp. A parser
  inflates and parses each part on its own, then concatenates the packet lists.
  It must not byte-concatenate the raw streams first, because the inherited-time
  state must not leak across a part boundary.
- Only the last part carries the results BLK.

`wrpl-inspector`'s `OpenPartedReplay` and `WrplReplayParser`'s
`ServerReplayReader` both follow this rule. A client replay is a single
self-contained file; `isServer` is false and there are no parts.

---

## 3. The two parsers compared

### 3.1 `WrplReplayParser` (C++, with Python bindings)

The most complete parser. It reconstructs the whole match into a `ParserState`:
players, teams, mission zones, chat, battle messages, ECS entities, and unit
positions from the FM (flight) and GM (ground) sync streams. It reads client
replays and segmented server replays (`ServerReplayReader`). It offers a full
decompress reader and a streaming compressed reader. It loads `VROMFs`
containers for templates and translation. It exposes the whole API through
`pybind11` bindings for prototypes and test oracles. It also ships the standalone
`ClogDecryptor`. Its supported version is `18c0b`. Its `README` still lists
`char.vromfs.bin` loading and a VROMFs repacker as TODO items.

### 3.2 `wrpl-inspector` (Go, with a dear-imgui GUI)

A Go library (`wrpl`) plus a GUI (`inspector`). The library parses the header,
the settings and results BLK, and the packet stream. It has pluggable parsers
for chat, most of the ECS system, awards, kills, full-precision ground movement,
aircraft state, camera angles, critical and fatal damage, and player
information. The GUI adds a kill log and a map view. It downloads a server
replay from a session id and combines the segments. It shares the packet-stream
and ECS reverse-engineering approach with `WrplReplayParser`. It does not build a
single unified domain model as large as the C++ `ParserState`; it exposes
per-parser results instead.

### 3.3 How they differ

- **Language and target.** C++ (native and Python) and Go (native and GUI).
- **Depth.** The C++ parser builds the fullest domain model and loads VROMFs.
  `wrpl-inspector` gives per-parser results and an inspection GUI.
- **Server replays.** Both read and combine segmented server parts, with the
  same even/odd part rule and the same per-part timestamp handling.
- **The framing is shared.** Both implement the same magic check, the same
  1234-byte header, the same variable-length size prefix, and the same
  timestamp-inheritance rule. They agree on the packet-type numbers.

### 3.4 The carve model (wrpl-inspector)

[wrpl-inspector](https://github.com/maxsupermanhd/wrpl-inspector)
(Go) carves one match out of the replay parts into a `CarvedReplay`. It is the
ingest backend behind the heatmap stats
(see [09-heatmaps-and-coordinates.md](09-heatmaps-and-coordinates.md)). Its
data model is a good summary of what a replay yields:

- `Kill`: time, killer and victim (player id, model, entity index, position),
  and weapon.
- `Damage`: time, a variant (`Hit`, `Critical`, `Severe`), offender and
  offended, and a fire flag.
- `Entity`: player id, entity index, model name, and the position path.
- `Player`: id, name, clan tag, team, crafts, and the scoreboard stats from the
  results BLK (kills, deaths, assists, score, capture, and more).

Its `cmd/service` exposes an HTTP ingest API: `POST /api/0/carve/bundle` takes a
tar of replay parts and returns a tar of `carve.json` and `carve.gob`. The repo
is AGPL-3.0.

---

## Repository status

- **`WrplReplayParser`** — C++ with Python bindings. The most complete parser.
  Supported version `18c0b`. Working.
- **`wrpl-inspector`** — Go library plus a GUI. Working.
