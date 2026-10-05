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

Server replay parts downloaded in 2026-10 (game 2.59) have `magic`
`0x00018C1C` (`1C 8C 01 00` on disk). See 2.1 for the compression change that
came with it. [verified, 2026-10]

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

**A client replay carries the match's real session ID.** A `.wrpl` that the
game client saves in its `Replays` folder has the same `session_id` at offset
732 as the server-side record of that match. Checked on squadron battles: the
hex value matched the match ID of the server data. The client can split one match into
several files, and each file has the same `session_id`. Read it as a
little-endian `uint64`, then format it as hex. To read only this ID, you do not
need to decompress the file. [verified, 2026-10]

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

In version `0x00018C1C` the stream is **zstd**, not zlib: it starts with the
zstd magic `28 B5 2F FD`. The span and offsets are the same (from
`1234 + settingsSize` to `resultsOffset`, or to the end of the file). After a
zstd decompress, the packet stream parses with the old framing. One full
server replay (12 parts, 18,802 packets) decoded with the old packet and
WeaponSync rules after this one change. A zlib-only parser fails with
"incorrect header check". [verified, 2026-10]

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

**Sensor record fields.** Two 2.59 server replays (a 4v4 top-tier jet battle
and a combined-arms battle) gave these results. [verified, 2026-10]

- The first byte after the leading bit holds the sensor kind in the high nibble
  and the sensor slot in the low nibble. The slot is the index of the sensor in
  the vehicle's `sensors { sensor {...} }` list (aircraft `flightmodels/*.blk`,
  ground `units/tankmodels/*.blk`). An RWR in that list sends no record, but it
  keeps its slot number.
- The leading bit is "on". When it is 0 the record carries no values.
- In a kind-1 record one more bit follows the type byte. When it is 0, the
  record stops there and carries no state, also when "on" is 1.
- A kind-2 record (a laser, for example a tank's) has a different layout: a
  bit, an `int16` angle at scale `PI`, then two blocks of 96 bits. A decoder
  that keeps one struct for all kinds must not read the kind-1 fields from it.
- In a kind-1 record the packed `int16` holds three indexes into the sensor's
  own BLK (`gamedata/sensors/*.blk`), each in the key order of its block:
  bits 0–3 index `transivers`, bits 4–9 index `scanPatterns`, bits 10–13 index
  `signals`. All three read 15, 63, 15 for a sensor that has no state.
- The scan pattern tells the mode. A pattern of `type: "no"` (named `track`,
  `hmdTrack`, `radarTrack` and similar) is a single-target track. Patterns of
  type `pyramide`, `cone` or `cylinder` are scans (search, TWS, ACM or HMD
  lock acquisition).
- The `float` after the packed `int16` is the battle time in seconds of the last
  mode change.
- The two `int16` values at scale `PI` are the scan-centre azimuth and
  elevation in radians, relative to the vehicle. In search they hold the
  scan-zone offset that the player set. In track they follow the target.
- The `int16` at scale 1 is a value in [0, 1] with no known meaning.
- In the target-designation records of the same sync, a record whose first
  byte is 6 carries the tracked target in its trailing `uint32`
  (`0xFFFF0000 | unit_uid`). It appears less than 1 s after the target first
  shows in the sensor's contact list.
- A unit uid is unique only per unit kind. An aircraft and a ground vehicle in
  the same battle can share one uid.
- Only a designation record whose trailing `uint32` has `0xFFFF` in its high
  16 bits names a target. Other values occur in the same record kind and are
  not unit uids. A radar in TWS also sends the designated target.
- The scan-centre angles are relative to the full body frame (yaw, then
  pitch, then roll of the vehicle). They stop at the antenna limits of the
  scan pattern (`azimuthLimits`, `elevationLimits`), also while the target is
  outside those limits. Client replays of the 2.59 game carry the same
  records for both aircraft of a duel. [verified, 2026-10]

**Seeker blocks of a guided missile in flight.** The weapon sync of a missile
carries a seeker block of a fixed bit length for each seeker kind. Read the
bits MSB first in each byte. A multi-byte number is little-endian from its bit
offset. [verified, 2026-10]

- Radar seeker, 607 bits. Bits 8–10 are `111` in track and `001` in search.
  Three `float` values at bits 11, 43 and 75 are the seeker's estimate of the
  target position in world axes. In track it was a median of 34 m from the
  true target. Three `int16` values at bits 340, 356 and 372, divided by 32767,
  are the unit line of sight from the missile in world axes. A `uint16` at bit
  454 is the range in metres. In track it read 0 to 15% (median 10%) above the
  true distance.
- Radar seeker, 639 bits. This block occurs one time per change from search to
  track. Bits 8–10 are `100`, then 32 bits follow whose meaning is not known.
  After them the 607-bit layout continues at an offset of +32 bits (line of
  sight at 372, 388 and 404, range at 486).
- IR seeker, 283 bits. The line of sight is at bits 58, 74 and 90 (same
  scale). No lock bit was found.

**Sensor kind in the sensor BLK.** The `type` of most sensor BLKs is `radar`,
also for IRSTs and optical trackers. The transceiver tells the kind: its
`visibilityType` is `infraRed` for an IRST, `optic` for a TV tracker,
`radarIntercept` for an ESM receiver, and absent for a radar. One sensor can
mix kinds: a radar BLK with an `irst` transceiver and `irst*` scan patterns.
The transceiver index in the replay record thus tells radar from IR for each
sample. An IR transceiver can give `range0` to `range7` in place of `range`.
[verified, 2026-10]

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

### 2.7 Client replays in version `0x00018C1C`

Two client replays of custom air duels (game 2.59, 1.8 MB and 2.5 MB, header
`version` `0x00018C1C`) gave these results. [verified, 2026-10]

- **The zstd frame has no content size.** `ZSTD_getFrameContentSize` gives
  "unknown". A decoder that then uses a fixed output buffer fails when the
  stream is larger. `@bokuweb/zstd-wasm` `decompress()` uses a 1 MiB default
  and fails with error code -70 (destination too small). Use a streaming
  decoder, or give a larger buffer. Server parts are small, so they did not
  show this problem.
- **The ECS uid link does not decode.** The `aircraft+player_unit` entities
  give no `uid`, `playerId`, or unit name with the 2.58 component layout. The
  flight stream (type 2) still decodes and gives one track for each aircraft
  unit id. One unit id holds all the rounds of a duel.
- **The kill record ties a unit id to a player.** The kill message is an MPI
  (type 4) packet whose payload starts with `02 58 58 F0`, then a 32-field
  `IdFieldSerializer` table. The fields that were checked:

  | Field | Type | Meaning |
  |---|---|---|
  | 1 | `uint32` | Killer's player slot index (the slot table index). `0xFFFFFFFF` when there is no killer. |
  | 2 | string | **Killer's** vehicle name, for example `f_16a_block_15_adf`. Empty when there is no killer (a crash). |
  | 3 | `uint16` | Victim unit id (low 11 bits), the same id as the flight stream. |
  | 4 | `uint16` | Killer unit id (low 11 bits). `0xFFFF` for a crash with no killer. |
  | 10 | string | Weapon or round name, for example `ap_i_t` or `he_frag_i`. |
  | 11 | `uint32` | Not a player id. Values 0 to 10 were seen. Meaning not known. |

  Fields 1 and 4 together give the unit id of each player who scores a kill.
  The kill counts that this gives agree with the kills and deaths in the
  results BLK.

  Field 2 names the killer's vehicle, not the victim's, although decoders
  often call it the victim unit. Five client replays of duels were checked
  against the pilots' own report of who flew what. With field 2 read as the
  victim's vehicle, the two pilots got each other's aircraft in every file.
  Read as the killer's vehicle, every file was correct. Crash records, which
  have no killer, have an empty field 2. [verified, 2026-10]
- **Two MPI messages carry hits.** They use the same 32-field table after a
  4-byte signature.
  - `02 58 56 F0` is damage with an attacker. Field 1 is the victim unit id,
    field 3 the victim vehicle name, and field 4 the attacker unit id
    (`0xFFFF` when there is no attacker, then field 5 is 1). It occurs in both
    directions, but only a few times in each round.
  - `02 58 18 F1` is a hit by the replay author (the hit marker). Field 1 is
    the target unit id, and field 2 is a `uint16` with an unknown meaning
    (maybe the part that was hit). It comes in bursts, often several messages
    in the same millisecond. In a duel where the author died three times to
    gunfire, no message named the author's unit, and all of them named the
    opponent. So a client replay gives the author's hits on others, but not
    the hits that others make on the author.
- **The ECS create record names the vehicle.** In the type 6 packets that
  create a player aircraft, the vehicle name (a length byte, then the name) is
  followed by a mission slot name such as `t2_player03_0` (also with a length
  byte). There is one record for each player aircraft. A player who never dies
  has no kill record with a vehicle name, so this record is the only source of
  that vehicle name that was found.
- **The results BLK of a client replay** holds `timePlayed`, `authorUserId`,
  `author`, an empty `matchingInfo`, a `player` list (`name`, `clanTag`,
  `userId`, `team`, `kills`, `deaths`, `assists`, `score`, and more; unused
  rows have `userId` `-1`), and `uiScriptsData`. It has no `crafts_info`, so it
  does not name the vehicles.
- **The settings BLK of a client replay** (binary BLK, the same format as the
  results BLK) holds the mission settings: `name`, `level`, `type` (for example
  `domination`), `chapter`, `environment`, `weather`, `timeLimit`,
  `scoreLimit`, `userMission`, `allowedUnitTypes`, `missionType` flags, and
  `stars` (date, time and position). It has no gun-lock or weapon-delay value.
- **A mission's gun lock is not in the replay.** Two client replays of a
  custom air-duel mission with a TSS-style gun lock (25 rounds) were checked.
  No packet kind marks the unlock: none occurs 28 to 32 s after the round
  starts more often than at control offsets, and no packet text names a lock,
  a timer or a countdown. The mission script enforces the lock on the server.
  It shows only in the hits: the earliest hit in a round came 21.5 s after the
  MPI message `02 58 37 F0` and about 29 s after the previous round's kill.
  `02 58 37 F0` occurs once per round, 6 to 8 s after the kill that ended the
  previous round, so it is probably the respawn. [verified, 2026-10]

### 2.8 Kill credit in a mid-air collision

In a mid-air collision that one aircraft survives, the game gives the kill to
the aircraft that survives. The kill record has no weapon and no crash flag.
At the same moment, the victim gets a damage record with no attacker
(attacker id 0). In the clearest case, the death reason was "burn" ("Plane
burnt down"), 0.7 s after a head-on pass with an estimated miss distance of
2 m. The guns of that duel were still locked, and neither aircraft fired. The
scoreboard counts the collision as an air kill for the survivor.

Thus a kill with no weapon is not always a crash or a shoot-down. A check for a
near pass (tens of meters) in the second before the death finds these
collisions. In about 700 TSS air duels, 4 more such kills were found.
[verified on one battle in detail, 2026-10]

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
