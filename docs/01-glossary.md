# 01 — Glossary

This section gives the terms and abbreviations used in the bank. Most entries
name the chapter and the section that cover the term in full. A general game
term that no chapter covers has no link.

## Game terms

- **WT**: War Thunder, the online combat game of Gaijin Entertainment. Players
  fight in aircraft, helicopters, ground vehicles and ships.
- **Gaijin**: Gaijin Entertainment, the developer of War Thunder and of the
  Dagor engine.
- **AB / RB / SB**: the three difficulty modes: Arcade Battles, Realistic
  Battles and Simulator Battles. The game files call them `arcade`,
  `historical` and `simulation`. Some mission files and replay data call SB
  `hardcore`. See [08 §5](08-vehicles-and-models.md#5-battle-rating),
  [10 §6.1](10-sre-tss-info.md#61-air-duel-missions).
- **HB (Historical Battles)**: the TSS name for Simulator Battles (SB). Do
  not confuse it with the `historical` key in the game files: there it means
  Realistic Battles (RB), for example `economicRankHistorical`. See
  [10 §2](10-sre-tss-info.md#2-tournament-list-getactivetournaments).
- **BR (battle rating)**: the number that sets which vehicles meet in a battle.
  Each mode has its own BR. `BR = economic rank / 3 + 1`, rounded to one
  decimal. See [08 §5](08-vehicles-and-models.md#5-battle-rating).
- **economic rank**: the integer behind the BR. `char.vromfs.bin`
  `config/wpcost.blk` holds it per unit, with one key per mode
  (`economicRankArcade`, `economicRankHistorical`, `economicRankSimulation`).
  Aircraft have more keys for ground and naval battles. See
  [08 §5](08-vehicles-and-models.md#5-battle-rating).
- **balance level**: the value that a mission reads with
  `missionGetBalanceLevel`. The air battle base templates set the base health
  from it. A link to the economic rank is not proven. See
  [07 §6.2](07-terrain-maps-and-missions.md#62-base-health-by-battle-rank).
- **rank / tier / era**: the stage of a vehicle in the research tree, I to
  VIII. "Tier" is the player word for it. `wpcost.blk` and the TSS `rank` field
  hold it. See [10 §4](10-sre-tss-info.md#4-tournament-detail-detailtournament).
- **top tier**: the highest ranks and BRs of the game.
- **research / research tree**: the progress system. A player earns research
  points (RP) in battle and unlocks vehicles and modifications for each nation.
  The lang key `<id>_shop` gives the research tree name of a unit. See
  [08 §5b](08-vehicles-and-models.md#5b-display-names-langunitscsv).
- **nation**: one of the countries of the research tree. TSS lists them as
  `usa`, `germany`, `ussr`, `britain`, `japan`, `china`, `italy`, `france`,
  `sweden` and `israel`. See
  [10 §4](10-sre-tss-info.md#4-tournament-detail-detailtournament).
- **Silver Lions (SL)**: the main in-game currency. Players earn it in battle
  and pay for repairs, vehicles and ammo with it. The game files call it
  warpoints (`warpoints.blk`).
- **Golden Eagles (GE)**: the premium currency, bought with real money. The
  `char` server calls it gold (`goldBalance`, `costGold`). TSS prize pools pay
  in it. See [05 §4.1](05-char-server-api.md#41-the-profile-blob).
- **premium vehicle**: a vehicle that a player buys and does not research. Its
  `wpcost.blk` block has `costGold`. See
  [07 §6.4](07-terrain-maps-and-missions.md#64-reward-multiplier-for-bases).
- **premium account**: a paid time period that gives higher battle rewards.
  TSS rewards include it. See
  [10 §4](10-sre-tss-info.md#4-tournament-detail-detailtournament).
- **crew**: the persons in a vehicle. Each crew member is a damage-model part
  with 40 hp, for example `commander_dm`, `driver_dm`, `gunner_dm` and
  `loader_dm`. A tank needs `tank_crew.minCrewMemberAliveCount` crew alive
  (default 2). See [06 §3.5](06-ballistics-and-armor.md#35-module-crew-and-ammo-damage-data).
- **crew skills**: the trained values of a crew. `char.vromfs.bin` holds them
  in `crew_skills`. Mission units carry a `crewSkillK`. See
  [02 §1.5](02-file-formats.md#15-the-datamine-file-set).
- **modification**: an upgrade that a player researches for one vehicle, for
  example a new shell, a part or an engine upgrade. `char.vromfs.bin`
  `config/modifications.blk` holds them. A modification can add, show or hide
  damage-model parts. See [06 §4.6](06-ballistics-and-armor.md#46-per-part-charge-and-penetration-carry-confirmed-live),
  [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **stock**: the default state. A stock vehicle has no researched
  modifications. A stock skin or decal is one that every player can get. See
  [05 §4.5](05-char-server-api.md#45-player-cosmetics-and-awards).
- **loadout / weapon preset**: the weapons and ammo that a player takes into
  battle. Aircraft presets are in the unit BLK `WeaponSlots`. See
  [08 §3.5](08-vehicles-and-models.md#35-weapon-loadouts).
- **spawn / respawn**: the entry of a vehicle into a battle. The mission value
  `maxRespawns` limits the respawns (`-1` is no limit). See
  [03 §1.2](03-replays.md#12-the-fixed-header-1234-bytes),
  [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **spawn points (SP)**: the points that a player spends to spawn another
  vehicle in ground Realistic and Simulator battles. Kills, assists and
  captures earn them.
- **test drive / test flight**: an offline practice session from the hangar.
  The client log names its mission `testFlight_...`. See
  [02 §3.6](02-file-formats.md#36-clog-encrypted-logs-clog),
  [04](04-localhost-8111-api.md).
- **hangar**: the main menu, where a player picks vehicles, loadouts and skins.
  The `char` profile holds a `hangar` block with the state of each vehicle. See
  [05 §4.5](05-char-server-api.md#45-player-cosmetics-and-awards).
- **Random Battles**: the main matchmade PvP mode. The replay CDN also keeps
  their server replays. See [10 §7a](10-sre-tss-info.md#7a-warthundercom-replay-page).
- **Custom battles**: sessions that a player hosts. A user mission runs there
  from a mission URL. See [02 §3.10](02-file-formats.md#310-mission-files-blk-missions-user-missions).
- **Domination / Conquest**: battle types where teams hold capture zones.
  Mission keys end in `_dom` or `_Conq<N>`. See
  [07 §5.2](07-terrain-maps-and-missions.md#52-catalog-schema),
  [10 §6](10-sre-tss-info.md#6-schedule-results-and-replays).
- **Air Domination**: an air battle type with capture zones. Its mission keys
  end in `_ad`. TSS team air battles use it. See
  [10 §6.1](10-sre-tss-info.md#61-air-duel-missions).
- **ground strike (`_gs`)**: older air battle missions whose bases do not
  respawn. See [07 §6.2](07-terrain-maps-and-missions.md#62-base-health-by-battle-rank).
- **base**: a ground target area on an air map. Bombers destroy it for points.
  The mission data calls it a bombing area. See
  [07 §6.1](07-terrain-maps-and-missions.md#61-the-bombing-area).
- **capture zone**: a map area that a team takes by presence. The 8111 map
  type is `capture_zone`. The level catalog lists them as `capture_areas`. See
  [04](04-localhost-8111-api.md#get-map_objjson),
  [07 §5.2](07-terrain-maps-and-missions.md#52-catalog-schema).
- **airfield**: a runway where aircraft spawn, land and repair. On air maps a
  `dynaf` composit places it. See
  [07 §2.4](07-terrain-maps-and-missions.md#24-dynamic-composits-airfield-dynaf).
- **light / medium / heavy tank, tank destroyer, SPAA**: the ground vehicle
  roles. SPAA is a self-propelled anti-aircraft gun. The tags are
  `type_light_tank`, `type_medium_tank`, `type_heavy_tank`,
  `type_tank_destroyer` and `type_spaa`. See
  [08 §5a](08-vehicles-and-models.md#5a-unit-type-tags-unittagsblk).
- **MBT**: main battle tank. `lang/units.csv` uses it as a class name. See
  [08 §5b](08-vehicles-and-models.md#5b-display-names-langunitscsv).
- **attacker**: a ground-attack aircraft. Its tag is `type_assault`, which is
  never on a ground vehicle. See
  [08 §5a](08-vehicles-and-models.md#5a-unit-type-tags-unittagsblk).
- **squadron / clan**: a player group. The `char` server calls it a clan
  (`clanId`, `clanTag`, `clanName`). See
  [10 §9.1](10-sre-tss-info.md#91-cln_clan_get-roster-and-ratings).
- **World War**: a strategic campaign mode. `wwdata.vromfs.bin` holds its data,
  and the replay header has the flag `isWorldWar`. See
  [02 §1.5](02-file-formats.md#15-the-datamine-file-set).
- **event / PvE**: an event is a mode or mission for a limited time. PvE is a
  battle against AI units. Event and PvE missions set a fixed base health. See
  [07 §6.1](07-terrain-maps-and-missions.md#61-the-bombing-area).
- **skin / camouflage**: the paint of a vehicle. See
  [08 §2](08-vehicles-and-models.md#2-camouflages-and-textures).
- **decal / decoration**: cosmetic items for a vehicle. A decal is a picture
  on the surface. A decoration is a 3D item on the vehicle, and the `char`
  server calls it an attachable. See
  [05 §4.5](05-char-server-api.md#45-player-cosmetics-and-awards).
- **workshop skin (UGC)**: a skin that a player made. Its resource id is a
  UUID. The client caches it in `cache/contentUGC/`. See
  [05 §4.5](05-char-server-api.md#45-player-cosmetics-and-awards),
  [08 §2.7](08-vehicles-and-models.md#27-aircraft-and-cached-skins).
- **Marketplace**: the Gaijin trade site for tradable items, for example some
  skins and decals. See [05 §4.6](05-char-server-api.md#46-marketplace-and-inventory-reads).
- **warbonds / trophies**: a warbond is a currency for a special shop. A
  trophy is a reward container. The profile blob holds `warBonds` and
  `trophies`. See [05 §4.1](05-char-server-api.md#41-the-profile-blob).
- **unlock / award / title**: account achievements. The `unlocks` dict holds
  achievements, challenges, medals and Steam trophies. See
  [05 §4.5](05-char-server-api.md#45-player-cosmetics-and-awards).
- **hit camera**: the view that shows the path and the effect of a hit. It
  can save the hit as a file. See
  [06 §3.6](06-ballistics-and-armor.md#36-saved-hit-files-replayhits).
- **Protection Analysis**: the hangar tool that fires test shots at a chosen
  vehicle. See [06 §3.6](06-ballistics-and-armor.md#36-saved-hit-files-replayhits).
- **CDK**: the War Thunder CDK, the official kit for game mods. It includes the
  Mission Editor. See [02 §3.10](02-file-formats.md#310-mission-files-blk-missions-user-missions).
- **user mission**: a text `.blk` mission that the CDK Mission Editor writes.
  A multiplayer user mission has a cap of 512 KB and 512 units. See
  [02 §3.10](02-file-formats.md#310-mission-files-blk-missions-user-missions).

## Engine and files

- **Dagor**: the WT game engine. The source is in the `DagorEngine`
  repository. See [02](02-file-formats.md).
- **VROMFS**: a Dagor container file (`.vromfs.bin`, unpacked as `.bin_u`). It
  holds many BLK files, often zstd-packed. See [02](02-file-formats.md).
- **BLK / DataBlock**: the Dagor block data format. It holds a tree of named
  parameters. It has a text form and a binary form. See [02](02-file-formats.md).
- **FAT**: a binary BLK layout. The first byte is `0x01`. See [02](02-file-formats.md).
- **BBF3**: a binary BLK layout that starts with `\0BBF`. Some `char` read
  answers use this form, for example `cln_get_meta_blk`. Most other answers
  use FAT. See [02 §2.7](02-file-formats.md#27-the-modern-bbf3-format-leading-bytes-0bbf-version-3),
  [05 §2.1](05-char-server-api.md#21-success-response).
- **`.blkx`**: a JSON copy of a BLK file, used by the public datamine mirror.
  See [02](02-file-formats.md).
- **DDSx / dxp**: the Dagor texture format and its pack. See [02](02-file-formats.md).
- **clog**: an XOR-encrypted log file (`.clog`), for example the client debug
  log. It is not part of the `.wrpl` packet stream. See
  [02 §3.6](02-file-formats.md#36-clog-encrypted-logs-clog),
  [03 §2.5](03-replays.md#25-the-clog-decryptor-is-not-part-of-the-packet-stream).
- **datamine**: the game files unpacked to a folder tree. The local copy is the
  `War-Thunder-Datamine` repository. See [02](02-file-formats.md), [09](09-tooling-and-repos.md).
- **VROMFS groups**: the main containers. `aces.vromfs.bin` holds the game
  data, `char.vromfs.bin` the economy and unit config, `game.vromfs.bin` the
  game scripts, `gui.vromfs.bin` the UI, `lang.vromfs.bin` the text and
  `mis.vromfs.bin` the missions. See
  [02 §1.5](02-file-formats.md#15-the-datamine-file-set).
- **VRFs / VRFx**: the two VROMFS magics. A `VRFx` file adds an 8-byte header
  with the format version. See [02 §1.1](02-file-formats.md#11-header).
- **ZSTD_OBFS / PLAIN**: the VROMFS body compression types. A zstd body has a
  16-byte XOR key on its head and on its tail. See
  [02 §1.2](02-file-formats.md#12-body-compression).
- **SLIM**: a binary BLK layout with no built-in name map. Its first byte is
  `0x03`, `0x04` or `0x05`. The reader must supply the shared name map. See
  [02 §2.3](02-file-formats.md#23-slim-layout-leading-bytes-0x03-0x04-0x05).
- **name map (`nm`)**: the shared list of block and parameter names in a
  VROMFS. SLIM blocks refer to names by an index into it. See
  [02 §2.4](02-file-formats.md#24-the-shared-name-map-nm-file).
- **zstd dictionary (`.dict`)**: the shared zstd dictionary of a VROMFS. BLK
  flavour `0x05` needs it. Its file name is the hex of a SHA-256 digest. See
  [02 §2.5](02-file-formats.md#25-per-file-blk-packing-inside-vromfs-new-versions).
- **BBF / BBz**: the oldest binary BLK format (`\0BBF`, versions 2 and 3, read
  by wt-tools) and its zlib wrapper (`\0BBz`). See
  [02 §2.6](02-file-formats.md#26-the-old-bbf-format-leading-bytes-0bbf-and-the-0bbz-zlib-wrapper).
- **text BLK**: the plain-text BLK form, `name:type = value;` in nested blocks.
  The short type names are `t`, `i`, `r`, `p2`, `p3`, `p4`, `ip2`, `ip3`, `b`,
  `c`, `m` and `i64`. See [02 §2.8](02-file-formats.md#28-text-blk-blk-as-plain-text).
- **ParamType**: the numeric type id of a BLK parameter, from `0x01` (string)
  to `0x0d` (IPoint4). See
  [02 §2](02-file-formats.md#2-dagor-blk-datablock-binary-format).
- **ULEB128**: an unsigned variable-length integer. FAT BLK uses it for counts
  and offsets. See [02 §2.2](02-file-formats.md#22-fat-layout-leading-byte-0x01).
- **zstd / zlib / LZ4 / LZMA**: general compression codecs. zstd packs VROMFS
  bodies, BLKs and the replay stream of version `0x00018C1C`. zlib packs older
  replay streams. LZ4 packs some ECS snapshots. See
  [02](02-file-formats.md), [03 §2.1](03-replays.md#21-compression).
- **Oodle (Kraken, Leviathan)**: a compression codec. Level terrain, props and
  some textures use it. See
  [07 §1.1](07-terrain-maps-and-missions.md#11-the-oodle-oozkraken-codec).
- **ooz**: an open Kraken and Leviathan decoder. It decodes Oodle data with no
  game DLL, also on Linux. See [02 §3.2](02-file-formats.md#32-ddsx-textures-ddsx).
- **DXP2**: a texture pack (`*.dxp.bin`, magic `DxP2`) that holds many DDSx
  textures. See [02 §3.1](02-file-formats.md#31-dxp2-texture-packs-dxpbin).
- **GRP / GRP2**: a game resource pack (`*.grp`, magic `GRP2`). It holds
  models and other assets. A class id selects the resource kind. See
  [02 §3.4](02-file-formats.md#34-game-resource-packs-grp2-grp-and-descriptors),
  [08 §1.1](08-vehicles-and-models.md#11-how-the-game-stores-models).
- **GameResDesc**: the material and texture names of the models
  (`riDesc.bin`, `dynModelDesc.bin`). See
  [02 §3.4](02-file-formats.md#34-game-resource-packs-grp2-grp-and-descriptors),
  [08 §2.3](08-vehicles-and-models.md#23-how-a-mesh-gets-its-textures).
- **DBLD**: the packed level file `levels/<stem>.bin` (magic `DBLD3x64`). It
  is a stream of tagged blocks, for example `HM2`, `LMAP`, `RIGZ` and `DXP2`.
  See [02 §3.5](02-file-formats.md#35-the-dbld-binary-level-dump-bin-dbld).
- **CompressedData**: the generic Dagor compressed block: a 3-byte size, a
  method byte (`0x20` LZMA, `0x40` zstd, `0x60` zlib, `0x80` Oodle), then the
  data. See [02 §3.3](02-file-formats.md#33-the-generic-dagor-compressed-block).
- **beginBlock frame**: a Dagor block header. The top 2 bits give the codec
  (`2` Oodle, `1` zstd) and the low 30 bits give the length. See
  [07 §1.2](07-terrain-maps-and-missions.md#12-the-hm2-block-battle-crop).
- **aces**: the game binary (`linux64/aces` on Linux). The main data container
  `aces.vromfs.bin` has the same name. See [06](06-ballistics-and-armor.md#scope-and-sources),
  [11](11-misc-game-info.md).
- **game version / build**: the 4-part version, for example `2.59.0.54`. The
  datamine `version` file, the replay header and the `char` header
  `gameVersion` carry it. See [02 §1.5](02-file-formats.md#15-the-datamine-file-set),
  [05 §3.1](05-char-server-api.md#31-headers).
- **`wpcost.blk`**: the per-unit economy file in `char.vromfs.bin`. It holds the
  economic ranks, the rank, `costGold` and the `weaponDamage` of each weapon
  preset. See [08 §5](08-vehicles-and-models.md#5-battle-rating),
  [07 §6.3](07-terrain-maps-and-missions.md#63-bomb-damage-against-a-base).
- **`config/damagemodel.blk`**: the global damage-model values, for example
  `armorResistance`, `maxArmorEffectiveScale` and the spall globals. See
  [06 §2.5](06-ballistics-and-armor.md#25-de-marre-path).
- **lang CSV**: the localization tables in `lang.vromfs.bin`, as `;`-separated
  quoted CSV. A row key such as `location/air_afghan` is a loc key. See
  [02 §3.9](02-file-formats.md#39-the-wosf-rust-toolchain),
  [08 §5b](08-vehicles-and-models.md#5b-display-names-langunitscsv).
- **`icon/*` glyph keys**: lang keys whose value is a glyph of the UI symbol
  font `symbols_skyquake.ttf`. See
  [02 §3.8.2](02-file-formats.md#382-the-icon-glyph-keys-verified-2026-10-client).
- **Squirrel / Quirrel (`.nut`)**: the UI script language. Quirrel is the
  Gaijin dialect of Squirrel. Examples are `scripts/dmviewer/protectionanalysis.nut`
  and the Squirrel combiner of the armor value. See
  [06 §4.5](06-ballistics-and-armor.md#45-structural-and-volumetric-checks-native).
- **daScript (`.das`)**: the compiled Dagor script language. Game logic such as
  the ammo stowage rules and the network events is daScript, in
  `game.vromfs.bin` `gamecommon/**/*.das`. See
  [06 §3.5](06-ballistics-and-armor.md#35-module-crew-and-ammo-damage-data),
  [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **daNet**: the Dagor network layer. The datamine folder `danetlibs` in
  `aces.vromfs.bin` holds libraries of the engine's daNetGame framework. See
  [02 §1.5](02-file-formats.md#15-the-datamine-file-set).

## Replays and live feeds

- **`.wrpl`**: the WT replay file. It holds a header, settings BLK, results,
  and a per-tick packet stream. See [03](03-replays.md).
- **8111**: the local web server the game runs while you play. It answers
  telemetry as JSON. See [04](04-localhost-8111-api.md).
- **server replay**: the replay that the game server records. It is a set of
  parts, and its `playerNo` is `0x80000000`. See
  [03 §2.6](03-replays.md#26-multi-part-server-replays).
- **client replay**: the replay that the game client saves in its `Replays`
  folder. It is one file. Only it holds the cockpit data of its author. See
  [03 §2.7](03-replays.md#27-client-replays-in-version-0x00018c1c).
- **replay part**: one `.wrpl` file of a server replay. Even parts hold a
  state, odd parts hold the packet stream. All parts share one session id. See
  [03 §2.6](03-replays.md#26-multi-part-server-replays).
- **session id**: the 64-bit id of a match, at header offset 732. Web pages
  show it in hex. TSS gives it in decimal. See
  [03 §1.2](03-replays.md#12-the-fixed-header-1234-bytes),
  [10 §7a](10-sre-tss-info.md#7a-warthundercom-replay-page).
- **replay CDN**: the download host of server replay parts,
  `wt-game-replays.warthunder.com/<hex session id>/NNNN.wrpl`. It keeps parts
  for about two weeks. See [10 §7a](10-sre-tss-info.md#7a-warthundercom-replay-page).
- **format version (`CURR_MAGIC`)**: the `uint32` at offset 4 of a `.wrpl`. It
  changes with each major game version. `0x00018C1C` is game 2.59. See
  [03 §1.1](03-replays.md#11-file-identity-and-versions).
- **settings BLK / results BLK**: the two BLK parts of a replay. The settings
  BLK holds the mission settings. The results (footer) BLK holds the players,
  scores and awards after the match. See
  [03 §1.4](03-replays.md#14-the-datablock-parts-settings-and-footer).
- **packet**: one record of the replay stream: a size prefix, a `uint16` type,
  an optional millisecond time, then the payload. See
  [03 §2.2](03-replays.md#22-packet-framing).
- **packet type**: 0 `EndMarker`, 1 `StartMarker`, 2 `AircraftSmall`, 3 `Chat`,
  4 `MPI`, 5 `NextSegment`, 6 `ECS`, 7 `Snapshot`, 8 `ReplayHeaderInfo` (the
  table of message hashes). See [03 §2.3](03-replays.md#23-packet-types).
- **MPI message**: a network message in a type 4 packet. It has a 16-bit
  message id, for example `0xF058` for a kill, and it goes to an object id.
  See [03 §2.4c](03-replays.md#24c-other-mpi-messages).
- **object id / object kind**: the target of an MPI message. The kind is
  `object id >> 11`: 0 aircraft, 1 ground unit or ship, 11 global, 16 and 17
  damage state. See [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **uid (unit id)**: the id of a unit in a battle, in the low 11 bits. It is
  unique only per unit kind, and it is not fixed per player. Do not mix it up
  with the account uid. See [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **eid**: an ECS entity id. It carries generation bits, because the engine
  reuses index numbers. See [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **mission slot**: the mission name of a player position, for example
  `t1_player05_0`. See [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **`dummy_plane`**: the placeholder entity that each player slot gets at
  battle start. See [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **flight-model sync (FM sync)**: the type 2 aircraft record, about every
  250 ms. It holds the position, the attitude, the controls, the engines and
  the sensor states. See [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **ground sync (`0xF074`)**: the MPI state of ground vehicles and ships. It
  uses Dagor net delta compression. See
  [03 §2.4a](03-replays.md#24a-ground-vehicles-cameras-and-missiles).
- **store sync (`0xF11A`)**: the MPI state of missiles and rockets in flight.
  See [03 §2.4a](03-replays.md#24a-ground-vehicles-cameras-and-missiles).
- **kill record (`0xF058`)**: the MPI kill message. Field 2 names the vehicle
  of the killer, not of the victim. See
  [03 §2.7](03-replays.md#27-client-replays-in-version-0x00018c1c).
- **`UnitDetected` (`0xF037`)**: the spot message. Unit `A` spots unit `B`. See
  [03 §2.7](03-replays.md#27-client-replays-in-version-0x00018c1c).
- **cockpit message (`0xD04A`)**: `ReplayCockpitParams`, the instruments of the
  author of a client replay. See
  [03 §2.7](03-replays.md#27-client-replays-in-version-0x00018c1c).
- **IdFieldSerializer**: the field table format of many messages (32-field and
  255-field forms), with 3-bit size codes. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **reflection variables**: the replicated variables of an object, sent in
  `0xF02D`, `0xF0AA` and `0xD136`. See
  [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **damage-state object (DVM)**: object kinds 16 and 17. They carry the packed
  part health of a unit (`DvmUnreliableHpReflectionData`). See
  [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **local / global part id**: the two ids of a damage-model part in a replay.
  The global id indexes the names of `config/damagemodelparts.blk`. The local
  id indexes the `DamageParts` leaves of the unit. See
  [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **ECS entity message / `NetMsg`**: an ECS network event. Its class name is
  the event name plus `NetMsg`. The replay carries the 32-bit FNV-1 hash of
  the name. See [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **`DasEventMsg`**: an ECS message that carries a daScript event. The event
  type is the FNV-1a hash of the event name. See
  [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).

## Localhost 8111 API

- **`allowWebUi`**: the option that turns on the 8111 server. It is off by
  default. See [04](04-localhost-8111-api.md#limits).
- **`/state`**: the flight state of an aircraft (speeds, AoA, controls,
  engines). It is invalid in a tank. See [04](04-localhost-8111-api.md#get-state).
- **`/indicators`**: the instruments of the current vehicle. See
  [04](04-localhost-8111-api.md#get-indicators).
- **`/map_obj.json`**: the live map objects, with normalized `x` and `y`. See
  [04](04-localhost-8111-api.md#get-map_objjson).
- **`/map_info.json`**: the world extent of the map picture, the grid, and
  `map_generation`. See [04](04-localhost-8111-api.md#get-map_infojson).
- **`map_generation`**: a counter that goes up at each new battle and at a
  respawn. A client polls it to find a map change. See
  [04](04-localhost-8111-api.md#get-map_infojson).
- **`/hudmsg`**: the HUD event and damage lines, for example the kill lines.
  See [04](04-localhost-8111-api.md#get-hudmsg).
- **`/map.img`**: the current minimap picture, as a JPEG. See
  [04](04-localhost-8111-api.md#get-mapimg).
- **`valid` flag**: a field of some endpoints. When it is `false`, no other
  field is present. See
  [04](04-localhost-8111-api.md#valid-state-versus-invalid-state).

## Online API

- **`char` server**: the online account, unlock, and inventory API. See
  [05](05-char-server-api.md).
- **`cln_*`**: the action names the `char` server accepts, for example
  `cln_buy_resource`. See [05](05-char-server-api.md).
- **JWT**: the JSON Web Token that authenticates a `char` request. See
  [05](05-char-server-api.md).
- **TSS**: the Tournament Service System, the tournament site
  `tss.warthunder.com`. See [10](10-sre-tss-info.md).
- **SRE / SQB**: Squadron Realistic Battles and its rating. See
  [10](10-sre-tss-info.md).
- **`ano_*`**: public read actions of the `char` server, for example
  `ano_get_bin` and `ano_get_public_userstat`. See
  [05 §4.5](05-char-server-api.md#45-player-cosmetics-and-awards).
- **read path / write path**: `GET /json` reads data. `POST /char` writes data
  with a FAT body. The action name and the JWT go in headers. See
  [05 §2](05-char-server-api.md#2-read-path-get-json),
  [05 §3](05-char-server-api.md#3-write-path-post-char).
- **`token` header**: the HTTP header that carries the JWT. It is the only
  credential. See [05 §1.4](05-char-server-api.md#14-how-the-client-presents-the-jwt).
- **circuit blk**: the config that the client gets from
  `public-configs.warthunder.com`. It names the `char` host of a region. See
  [05](05-char-server-api.md).
- **profile blob**: the account state that the server sends after a write.
  See [05 §4.1](05-char-server-api.md#41-the-profile-blob).
- **`!ERROR:<CODE>`**: the text body of a failed write. See
  [05 §3.4](05-char-server-api.md#34-failure-response).
- **account uid (`userId`)**: the id of a player account. The JWT `uid` claim
  holds it. Do not mix it up with the unit uid of a replay. See
  [05 §1.2](05-char-server-api.md#12-jwt-claims).
- **inventory service / itemdef**: the Gaijin item store of tradable items.
  An item definition (`itemdefid`) describes one item. See
  [05 §4.6](05-char-server-api.md#46-marketplace-and-inventory-reads).
- **hash name**: the Marketplace key of an item, for example
  `ugcitem_<itemdefid>`. See
  [05 §4.6](05-char-server-api.md#46-marketplace-and-inventory-reads).

## TSS and squadron battles

- **`functions.php`**: the single TSS endpoint. The field `action` selects the
  call. See [10 §1](10-sre-tss-info.md#1-transport).
- **single / double elimination, Swiss**: the TSS tournament formats. The site
  spells them `single-elumination` and `double-elumination`. In Swiss, teams
  with equal scores meet each round, and no team drops out. See
  [10 §2](10-sre-tss-info.md#2-tournament-list-getactivetournaments).
- **Buchholz points**: a Swiss tie-break value, from the scores of the
  opponents of a team. See [10 §6](10-sre-tss-info.md#6-schedule-results-and-replays).
- **confirmed team**: a team whose captain confirmed the roster. See
  [10 §5](10-sre-tss-info.md#5-teams-and-registration).
- **technical victory**: a forfeit result. Its battle has no replay. See
  [10 §6](10-sre-tss-info.md#6-schedule-results-and-replays).
- **`pvp_ratio`**: the TSS PvP rating of a player. It is not the SRE rating.
  See [10 §5](10-sre-tss-info.md#5-teams-and-registration).
- **gun lock**: the rule of TSS air duels that locks guns for the first 30 s of
  each round. The replay does not show it. See
  [10 §6.1](10-sre-tss-info.md#61-air-duel-missions),
  [03 §2.7](03-replays.md#27-client-replays-in-version-0x00018c1c).
- **duel missions**: the `gladiators_*` missions of TSS air duels. See
  [10 §6.1](10-sre-tss-info.md#61-air-duel-missions).
- **`dr_era5_hist`**: the SRE rating key. `member_ratings[uid].dr_era5_hist` is
  the personal rating. `astat.dr_era5_hist` is the squadron rating. See
  [10 §9.1](10-sre-tss-info.md#91-cln_clan_get-roster-and-ratings).
- **squadron rating**: the sum of the 20 best member ratings plus the sum of
  the other member ratings divided by 20, rounded down. See
  [10 §9.2](10-sre-tss-info.md#92-squadron-rating-formula).
- **squadron points**: the personal SRE points of a player. A win adds points
  and a loss removes points. They reset at the season start. See
  [10 §9.5](10-sre-tss-info.md#95-personal-awards).
- **`clanDuel`**: the block of SRE rating settings in `char.vromfs.bin`
  `config/game_settings.blk`. See
  [10 §9.4](10-sre-tss-info.md#94-datamined-clanduel-settings).
- **season / BR cap**: an SRE season lasts two months and starts on the 1st of
  an odd month. The maximum BR (the cap) steps down once a week. See
  [10 §9.6](10-sre-tss-info.md#96-season-and-br-cap-timing-verified-2026-match-and-rating-history).
- **slot (US slot, EU slot)**: a daily time window when SQB is open, one for
  each region. See
  [10 §9.6](10-sre-tss-info.md#96-season-and-br-cap-timing-verified-2026-match-and-rating-history).

## Combat math

- **DeMarre / De Marre**: the penetration formula for full-caliber AP, APC and
  APCBC shells. The BLK fields are `demarrePenetrationK` and the three
  `demarre*Pow` powers. See [06 §2.5](06-ballistics-and-armor.md#25-de-marre-path).
- **APHE / APDS / APFSDS / HEAT / HE**: shell types. Each type has its own
  entry under Shell types. See [06](06-ballistics-and-armor.md).
- **line-of-sight thickness**: plate thickness divided by the cosine of the
  hit angle. See [06](06-ballistics-and-armor.md).
- **X-ray / DM**: the damage model: modules, crew, and ammo inside a vehicle.
  See [08](08-vehicles-and-models.md).
- **penetration**: the armor thickness in mm that a round can defeat. The
  stat card gives it at 0, 30 and 60 degrees, from 10 m to 2000 m. See
  [06 §2](06-ballistics-and-armor.md#2-penetration-model).
- **Lanz-Odermatt**: the penetration formula for long-rod rounds (APFSDS). The
  BLK field `lanzOdermattWorkingLength` selects it. See
  [06 §2.2](06-ballistics-and-armor.md#22-lanz-odermatt-how-the-game-builds-a-and-b).
- **armorpower**: an explicit penetration-by-range table. About 85 legacy
  rounds use it in place of a formula. A HEAT shell gives its jet penetration
  as `armorPower`. See [06 §2.7](06-ballistics-and-armor.md#27-legacy-armorpower-path).
- **drag (`Cx`)**: the air resistance of a shell. The speed falls as
  `V(d) = V0 * exp(-k * d)`, with `V0` the muzzle speed (BLK `speed`). See
  [06 §1](06-ballistics-and-armor.md#1-shell-flight-external-ballistics).
- **`ballisticCaliber` / `damageCaliber` / `damageMass`**: BLK fields that
  replace `caliber` and `mass` for the flight or for the hit. For APFSDS and
  APDS they give the rod or the core, not the gun bore. See
  [06 §1](06-ballistics-and-armor.md#1-shell-flight-external-ballistics),
  [06 §2.5](06-ballistics-and-armor.md#25-de-marre-path).
- **impact angle**: the angle between the shell path and the plate normal.
  0 degrees is a flat hit. See
  [06 §2.8](06-ballistics-and-armor.md#28-angle-of-impact-and-slope-effect).
- **slope effect**: the preset tables (`slope_effect.blk`) that set the
  penetration at an angle. The table key is the angle from the surface. See
  [06 §2.8](06-ballistics-and-armor.md#28-angle-of-impact-and-slope-effect).
- **`caliberToArmor`**: the ratio of the shell caliber to the armor. It
  selects the rows of the slope and ricochet tables. See
  [06 §2.8](06-ballistics-and-armor.md#28-angle-of-impact-and-slope-effect).
- **normalization**: a turn of a shell toward the plate normal at impact. The
  game has no separate normalization term. The slope table holds the angle
  effect. See [06 §2.9](06-ballistics-and-armor.md#29-normalization).
- **ricochet**: a hit where the shell bounces off the plate. Preset tables give
  the chance. The roll comes before the penetration test, on every plate. See
  [06 §2.10](06-ballistics-and-armor.md#210-ricochet-probability).
- **overmatch**: a hit by a shell whose caliber is much larger than the plate.
  The game has no "3 × caliber" rule. When `armorBreachK × B ≤ damageCaliber`,
  it uses plain `1 / cos θ`. See
  [06 §2.11](06-ballistics-and-armor.md#211-overmatch-rule).
- **RHA**: rolled homogeneous armor, the reference steel. The penetration
  formulas use its density, 7850 kg/m³. Classes include `RHA_tank` and
  `RHAHH_tank` (high hardness). See
  [06 §4.3](06-ballistics-and-armor.md#43-armor-class-and-material-modifiers).
- **CHA**: cast homogeneous armor, class `CHA_tank`. See
  [06 §4.3](06-ballistics-and-armor.md#43-armor-class-and-material-modifiers).
- **armor class**: the simulation category of a plate, in
  `armor_classes.blk`. It sets the quality, the caps and some ricochet rules.
  See [06 §4.3](06-ballistics-and-armor.md#43-armor-class-and-material-modifiers).
- **armor quality**: the multiplier of a plate's thickness, `q = mechQuality ×
  armorQuality`. Each mechanism (`generic`, `genericLongRod`, `cumulative`,
  EFP, tandem) can have its own value. See
  [06 §4.3](06-ballistics-and-armor.md#43-armor-class-and-material-modifiers).
- **effective thickness cap**: `armorEffectiveThicknessMax`, a part limit on
  the thickness that a shell must defeat. See
  [06 §4.2](06-ballistics-and-armor.md#42-effective-thickness).
- **charge**: the armor cost that a part takes from the penetration of a
  shell. For a plain part it is `q × T × S(θ)`. See
  [06 §4.6](06-ballistics-and-armor.md#46-per-part-charge-and-penetration-carry-confirmed-live).
- **mesh-charged part**: a part that the game charges from the chord through
  its collision mesh. The `SOLID` flag of the collision node selects it. See
  [06 §4.6](06-ballistics-and-armor.md#46-per-part-charge-and-penetration-carry-confirmed-live).
- **`armorThrough`**: the least penetration cost of a part. Thin modules with
  `armorThrough = 10` cost 10 mm each. See
  [06 §4.6](06-ballistics-and-armor.md#46-per-part-charge-and-penetration-carry-confirmed-live).
- **hit record**: the record that the game builds for each part that a shell
  crosses. It holds the arrival penetration, the charge and the state. A ray
  pattern around the shell path makes it. See
  [06 §4.6](06-ballistics-and-armor.md#46-per-part-charge-and-penetration-carry-confirmed-live).
- **pierce dispersion**: the random spread of about ±2.5 % on the penetration
  at each part. See
  [06 §4.6](06-ballistics-and-armor.md#46-per-part-charge-and-penetration-carry-confirmed-live).
- **stability (yaw)**: a shell with a `stability` block loses penetration when
  it yaws after a pierce or a ricochet. See
  [06 §4.6](06-ballistics-and-armor.md#46-per-part-charge-and-penetration-carry-confirmed-live).
- **composite armor**: armor of layers of different materials. Its effect
  depends on the direction of the hit. See
  [06 §4.4](06-ballistics-and-armor.md#44-composite-and-nera-directionality).
- **NERA**: non-explosive reactive armor, a composite sandwich of plates. See
  [06 §4.4](06-ballistics-and-armor.md#44-composite-and-nera-directionality).
- **ERA**: explosive reactive armor, blocks that explode outward when hit.
  Their `tandemPrechargeArmorQuality` is low (most at 0.33). See
  [06 §3.4b](06-ballistics-and-armor.md#34b-tandem-atgm-precharge-live-checked).
- **screen / skirt**: a thin add-on plate in front of the main armor, for
  example class `hull_side_special_armor`. See
  [06 §4.6](06-ballistics-and-armor.md#46-per-part-charge-and-penetration-carry-confirmed-live).
- **spall liner**: a fabric layer behind the armor that stops fragments, for
  example `armour_aramide_fabric`. See
  [06 §3.2](06-ballistics-and-armor.md#32-spall-cone).
- **module**: an internal part with hp, for example the engine, the breech,
  the ammo, the fuel tanks, the optics and the crew. See
  [06 §3.5](06-ballistics-and-armor.md#35-module-crew-and-ammo-damage-data).
- **`DamageParts` / `DamageEffects` / `MetaParts`**: unit BLK blocks. They
  list the parts, the hit rules of each part, and the part groups such as the
  crew compartment. See
  [06 §3.5](06-ballistics-and-armor.md#35-module-crew-and-ammo-damage-data).
- **`_dm` part**: the name form of a damage-model part, for example
  `engine_dm`. Collision nodes have the same names. See
  [08 §3.3](08-vehicles-and-models.md#33-collision-hulls).
- **hp state**: the 16-bit health of a part, 65535 at full. A hit lowers it by
  `ceil(damage / hp × 65535)`. See
  [06 §3.5](06-ballistics-and-armor.md#35-module-crew-and-ammo-damage-data).
- **`onHit` / `onKill`**: the two kinds of damage-effect rules of a part. An
  `onHit` rule rolls each effect. An `onKill` rule picks one outcome. See
  [06 §3.5](06-ballistics-and-armor.md#35-module-crew-and-ammo-damage-data).
- **disabled part**: a part that the armor test skips, for example a node that
  a modification hides or an empty ammo rack. See
  [06 §4.6](06-ballistics-and-armor.md#46-per-part-charge-and-penetration-carry-confirmed-live).

## Post-penetration damage

- **fuse (fuze)**: the part of an explosive shell that sets off the burst. Only
  a perforated part with a charge above `explodeTreshold` arms it. The burst
  comes `fuseDelayDist` metres later. See
  [06 §3.1](06-ballistics-and-armor.md#31-fuse-fuze-delay-and-sensitivity).
- **spall / secondary shatters**: the fragment cone behind a perforated plate.
  Presets in `secondary_shatter_presets.blk` set it. The cone axis is the
  shell direction. See [06 §3.2](06-ballistics-and-armor.md#32-spall-cone).
- **real shatters**: the body fragments of an HE or HEAT warhead burst. See
  [06 §3.2](06-ballistics-and-armor.md#warhead-body-fragments-real-shatters).
- **synthetic shatters**: the statistical burst model of APHE. It gives a
  range, a count, a penetration and a damage, not fragment rays. See
  [06 §3.2](06-ballistics-and-armor.md#aphe-burst-synthetic-shatters).
- **explosive filler**: the explosive in a shell, given by `explosiveType` and
  `explosiveMass` (kg). See
  [06 §3.3](06-ballistics-and-armor.md#33-he-filler-and-tnt-equivalent).
- **TNT equivalent**: the filler mass times a factor of `explosive.blk`.
  `strengthEquivalent` scales the blast, `brisanceEquivalent` scales the
  fragments. See [06 §3.3](06-ballistics-and-armor.md#33-he-filler-and-tnt-equivalent).
- **splash**: the blast damage around an HE burst, with an inner and an outer
  radius. See [06 §3.3](06-ballistics-and-armor.md#33-he-filler-and-tnt-equivalent).
- **overpressure**: the pressure damage of HE, HEAT and ATGM bursts in a
  compartment. It kills every crew member inside the inner radius. See
  [06 §3.3b](06-ballistics-and-armor.md#33b-overpressure-live-checked).
- **HEAT jet / cumulative**: the metal jet of a shaped charge. The game calls
  this mechanism `cumulative`. The jet loses about 100 mm of penetration per
  metre of air. See [06 §3.4](06-ballistics-and-armor.md#34-heat-standoff).
- **standoff**: the distance between the burst of a HEAT warhead and the
  armor. No standoff formula is known. See
  [06 §3.4](06-ballistics-and-armor.md#34-heat-standoff).
- **tandem precharge**: a small first charge of a tandem warhead. It defeats
  ERA before the main charge fires. See
  [06 §3.4b](06-ballistics-and-armor.md#34b-tandem-atgm-precharge-live-checked).
- **sabot petals**: the parts of an APFSDS sabot. They fly as bullets of their
  own, with about 51 mm of penetration, and can make their own spall. See
  [06 §3.2](06-ballistics-and-armor.md#32-spall-cone).
- **core breakup**: the break of an APDS or APCR core in a plate within a
  thickness band and above a critical speed. See
  [06 §3.2](06-ballistics-and-armor.md#32-spall-cone).
- **ammo stowage / rack**: the ammo positions of a vehicle (`ammoStowages`).
  Each `ammo_*_dm` slot is a part. See
  [06 §3.5](06-ballistics-and-armor.md#ammo-stowage-explosions-fatal-and-blowout).
- **first stage / ready rack**: the rounds that the gun takes first
  (`firstStage`, or `autoLoad` for a carousel autoloader). 8111 shows the
  count as `first_stage_ammo`. See
  [06 §3.5](06-ballistics-and-armor.md#how-a-spawn-fills-the-racks),
  [04](04-localhost-8111-api.md#get-indicators).
- **two-piece ammo**: ammo with a separate shell and charge. The charge
  clusters are `charges` blocks. See
  [06 §3.5](06-ballistics-and-armor.md#ammo-stowage-explosions-fatal-and-blowout).
- **blowout panels**: panels that vent an ammo explosion out of the vehicle.
  Such a rack has `fatalExplosion: false`. See
  [06 §3.5](06-ballistics-and-armor.md#ammo-stowage-explosions-fatal-and-blowout).
- **cook-off**: the explosion of ammo that burns in a dead vehicle. The chance per
  frame is `detonateProb × dt`. See
  [06 §3.5](06-ballistics-and-armor.md#ammo-stowage-explosions-fatal-and-blowout).
- **hit file (`ReplayHits`)**: a saved hit as a text BLK. The hit camera and
  Protection Analysis write it. See
  [06 §3.6](06-ballistics-and-armor.md#36-saved-hit-files-replayhits).

## Shell types

- **AP**: armor-piercing, a solid full-caliber shot. It uses the De Marre path.
  See [06 §2](06-ballistics-and-armor.md#2-penetration-model).
- **APC / APBC / APCBC**: AP with a penetrating cap, a ballistic cap, or both.
  They use the De Marre path and their own slope presets. See
  [06 §2](06-ballistics-and-armor.md#2-penetration-model).
- **APHE**: AP with an explosive filler. The fuse sets off the filler after it
  passes the armor. See [06 §3.2](06-ballistics-and-armor.md#aphe-burst-synthetic-shatters).
- **APCR**: AP composite rigid, a full-bore shot with a dense core. See
  [06 §3.2](06-ballistics-and-armor.md#32-spall-cone).
- **APDS**: AP discarding sabot. A sabot carries a sub-caliber core and falls
  off after the muzzle. See [06 §3.2](06-ballistics-and-armor.md#32-spall-cone).
- **APFSDS**: AP fin-stabilized discarding sabot, a long rod (dart). It uses
  the Lanz-Odermatt path and the `apds_fs_long` slope preset. See
  [06 §2.2](06-ballistics-and-armor.md#22-lanz-odermatt-how-the-game-builds-a-and-b).
- **HE / HE-FS**: high explosive, and its fin-stabilized form. The damage comes
  from splash, body fragments and overpressure. See
  [06 §3.3](06-ballistics-and-armor.md#33-he-filler-and-tnt-equivalent).
- **HEAT / HEAT-FS**: high-explosive anti-tank, a shaped charge, and its
  fin-stabilized form. See [06 §3.4](06-ballistics-and-armor.md#34-heat-standoff).
- **HESH**: high-explosive squash head. Its filler flattens on the plate and
  knocks spall off the inner face. The game has a `hesh` spall preset. See
  [06 §3.2](06-ballistics-and-armor.md#32-spall-cone).
- **ATGM**: anti-tank guided missile. Some have a tandem warhead. See
  [06 §3.4b](06-ballistics-and-armor.md#34b-tandem-atgm-precharge-live-checked).
- **EFP**: explosively formed penetrator. Its mechanism is
  `explosiveFormedProjectile`. See [06 §3.4](06-ballistics-and-armor.md#34-heat-standoff).

## Missiles and countermeasures

- **AAM**: air-to-air missile (`bulletType` `aam`). Its data is in the `rocket`
  block of `gamedata/weapons/rocketguns/<missile>.blk`. See
  [06 §6.1](06-ballistics-and-armor.md#61-where-the-data-is).
- **SAM**: surface-to-air missile. See
  [06 §6.4a](06-ballistics-and-armor.md#64a-ground-launched-saclos-missiles-data-location).
- **IR seeker**: a heat seeker (`opticalSeeker`). `rangeBand0` and `rangeBand1`
  give the rear and head-on lock range. `angleMax` is the gimbal limit. See
  [06 §6.5](06-ballistics-and-armor.md#65-seekers-and-countermeasure-data).
- **radar seeker**: a seeker that homes on radar returns (`radarSeeker`). An active seeker
  (ARH) has its own transmitter. A semi-active seeker (SARH) homes on the
  launcher radar. See [06 §6.5](06-ballistics-and-armor.md#65-seekers-and-countermeasure-data).
- **anti-radiation missile (HARM)**: a missile that homes on ground radar
  emitters, for example LD-10 and AGM-122. See
  [06 §6.1](06-ballistics-and-armor.md#61-where-the-data-is).
- **SACLOS**: semi-automatic command to line of sight. The operator keeps the
  sight on the target. See
  [06 §6.4a](06-ballistics-and-armor.md#64a-ground-launched-saclos-missiles-data-location).
- **beam riding**: guidance along a beam from the launcher
  (`lineOfSightAutopilot`), for example Fireflash. See
  [06 §6.1](06-ballistics-and-armor.md#61-where-the-data-is).
- **proportional navigation**: a guidance law that turns the missile in
  proportion to the turn rate of the line of sight. Its gain is `propNavMult`.
  See [06 §6.1](06-ballistics-and-armor.md#61-where-the-data-is).
- **loft**: a climb after launch that extends the range of a radar missile
  (`loftElevation`). See [06 §6.1](06-ballistics-and-armor.md#61-where-the-data-is).
- **proximity fuse**: a fuse that fires near a target (`proximityFuse`
  `radius`, `timeOut`). See [06 §6.1](06-ballistics-and-armor.md#61-where-the-data-is).
- **launch-zone table**: the `table0` to `table3` blocks of a missile. They
  give `rangeMax` and `timeMax`, and the game computes them with its own model.
  See [06 §6.2](06-ballistics-and-armor.md#62-launch-zone-tables-game-ground-truth).
- **`CxK` / `f(M)`**: the missile drag factor and the fitted Mach curve that
  scales it. See [06 §6.3](06-ballistics-and-armor.md#63-drag-law).
- **lock**: the state of a seeker that tracks a target. The seeker drops the
  track after `prolongationTimeMax` with no target. See
  [06 §6.5](06-ballistics-and-armor.md#65-seekers-and-countermeasure-data),
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **caged / uncaged, boresight, gimbal**: a caged seeker looks along the
  missile axis (the boresight). An uncaged seeker turns on its gimbal up to
  `angleMax`. See [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **IRCCM**: infrared counter-countermeasures, the seeker rules that reject
  flares. A gate seeker is one kind. See
  [06 §6.5](06-ballistics-and-armor.md#65-seekers-and-countermeasure-data).
- **flare**: an IR decoy. It lives about 4.4 to 4.5 s. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **chaff**: a radar decoy cloud. It lives 15 s or 20 s. One press releases
  5 charges 0.1 s apart by default. See
  [06 §6.5](06-ballistics-and-armor.md#65-seekers-and-countermeasure-data).
- **RCS**: radar cross section, the radar size of a target in m². See
  [06 §6.5](06-ballistics-and-armor.md#65-seekers-and-countermeasure-data).
- **ground clutter**: the radar return of the ground inside the seeker gates.
  See [06 §6.5](06-ballistics-and-armor.md#65-seekers-and-countermeasure-data).
- **Doppler gate / range gate**: the windows around the speed and the range of
  the target that a radar seeker accepts. See
  [06 §6.5](06-ballistics-and-armor.md#65-seekers-and-countermeasure-data).
- **notch**: a flight across the line of sight of a radar. The target then has
  the Doppler of the ground, and the clutter can hide it. See
  [06 §6.5](06-ballistics-and-armor.md#65-seekers-and-countermeasure-data).

## Sensors

- **sensor BLK**: the definition of a radar or IRST in `gamedata/sensors/*.blk`.
  It has `transivers`, `scanPatterns` and `signals`. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **transceiver**: the emitter and receiver part of a sensor. Its
  `visibilityType` gives the kind: `infraRed` (IRST), `optic` (TV), or
  `radarIntercept` (ESM receiver). No value means a radar. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **scan pattern**: the search or track shape of a sensor. `pyramide`, `cone`
  and `cylinder` are scans. `type: no` is a single-target track. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **IRST**: infrared search and track. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **RWR**: radar warning receiver. It sends no replay sensor record. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **TWS**: track while scan, a radar mode that tracks targets and also keeps
  the scan. See [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **ACM / HMD**: ACM is a close-range radar mode that locks a target in a small
  zone. HMD is the helmet-mounted display and sight. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **pulse / pulse-Doppler / HPRF / MPRF**: radar transceiver types: plain
  pulse, pulse-Doppler, high and medium pulse repetition frequency. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **targeting pod**: an external sensor pod, for example Litening. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **LWS / IRCM**: laser warning system and infrared countermeasure. 8111
  `/indicators` has fields for both. See
  [04](04-localhost-8111-api.md#get-indicators).

## Flight model

- **FM (flight model)**: the aircraft physics data,
  `gamedata/flightmodels/fm/<name>.blk`. The unit BLK names it in `fmFile`.
  See [08 §6.1](08-vehicles-and-models.md#61-where-it-is).
- **polar**: the lift and drag curve of one wing, fuselage or tail surface (`Cl0`,
  `lineClCoeff`, `alphaCritHigh`, `ClCritHigh`, `CdMin`). See
  [08 §6.2a](08-vehicles-and-models.md#62a-how-the-client-uses-a-polar).
- **Cl / Cd**: the lift and drag coefficients. `CdMin` is the least drag. See
  [08 §6.2a](08-vehicles-and-models.md#62a-how-the-client-uses-a-polar).
- **critical angle / stall**: the angle of attack of the highest lift
  (`alphaCritHigh`). Above it the surface stalls and the lift falls. See
  [08 §6.2a](08-vehicles-and-models.md#62a-how-the-client-uses-a-polar).
- **Oswald efficiency**: the factor `e` of the induced drag
  (`OswaldsEfficiencyNumber`). See
  [08 §6.2a](08-vehicles-and-models.md#62a-how-the-client-uses-a-polar).
- **Mach / `MachFactor`**: Mach is the speed divided by the speed of sound.
  `MachFactor` selects how the polar changes with Mach. See
  [08 §6.2a](08-vehicles-and-models.md#62a-how-the-client-uses-a-polar).
- **AoA / AoS**: angle of attack (the nose to the flight path, in the lift
  plane) and angle of sideslip. 8111 `/state` gives both. See
  [08 §6.3](08-vehicles-and-models.md#63-what-replay-tracks-show),
  [04](04-localhost-8111-api.md#get-state).
- **IAS / TAS**: indicated airspeed and true airspeed. See
  [04](04-localhost-8111-api.md#get-state).
- **load factor (G, `Ny`)**: the lift divided by the weight. See
  [08 §6.3](08-vehicles-and-models.md#63-what-replay-tracks-show).
- **excess power**: in this bank, the thrust minus the drag, given in g. It
  shows if an aircraft can climb or gain speed. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **wing strength (`CritOverload`)**: the wing break load `[neg, pos]` in N. A
  swing wing has one per sweep position. See
  [08 §6.2a](08-vehicles-and-models.md#62a-how-the-client-uses-a-polar).
- **VNE / MNE**: the never-exceed speed and the never-exceed Mach of a wing.
  See [08 §6.1](08-vehicles-and-models.md#61-where-it-is).
- **Instructor**: the flight assistant of mouse aim. The FM `Instructor` block
  holds its limits. See
  [08 §6.2a](08-vehicles-and-models.md#62a-how-the-client-uses-a-polar).
- **WEP**: war emergency power, a throttle above 100 % (1.1). See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **afterburner**: the thrust boost of a jet (`AfterburnerBoost`,
  `ThrAftMaxCoeff`). `Mode5` is throttle 1.1. See
  [08 §6.2](08-vehicles-and-models.md#62-template-values-for-modern-jets).
- **`ThrustMax0`**: the real dry thrust of a jet engine in kgf, static, at sea
  level. See [08 §6.2](08-vehicles-and-models.md#62-template-values-for-modern-jets).
- **kgf**: kilogram-force, 9.81 N. Jet FMs give thrust in kgf. Missile BLKs
  give thrust in N. See
  [08 §6.2](08-vehicles-and-models.md#62-template-values-for-modern-jets),
  [06 §6.1](06-ballistics-and-armor.md#61-where-the-data-is).
- **`Passport`**: the hangar performance block of an FM. Many jets carry
  template values there. See
  [08 §6.2](08-vehicles-and-models.md#62-template-values-for-modern-jets).
- **RPM / manifold pressure**: the engine speed, and the intake pressure of a
  piston engine. See [03 §2.4](03-replays.md#24-per-tick-unit-state),
  [04](04-localhost-8111-api.md#get-state).
- **supercharger / turbocharger**: compressors of a piston engine
  (`Compressor.Type` 1 and 2, and 3). See
  [08 §6.2b](08-vehicles-and-models.md#62b-piston-engines-and-propellers).
- **governor / propeller pitch**: the governor sets the blade pitch so that the
  engine holds its RPM. See
  [08 §6.2b](08-vehicles-and-models.md#62b-piston-engines-and-propellers).
- **blade element**: the propeller model. It cuts each blade into four
  elements. See [08 §6.2b](08-vehicles-and-models.md#62b-piston-engines-and-propellers).
- **radiator**: the water and oil coolers of a piston engine. The FM sync
  carries their positions. See [03 §2.4](03-replays.md#24-per-tick-unit-state).

## Vehicles and models

- **unit / unit id**: the game name for a vehicle and its id, for example
  `us_m47_patton_II`. `wpcost.blk`, TSS and replays use the same ids. See
  [08 §5](08-vehicles-and-models.md#5-battle-rating).
- **unit BLK**: the data file of one unit: `units/tankmodels/`,
  `flightmodels/` or `units/ships/` under `gamedata`. See
  [08 §1.2](08-vehicles-and-models.md#12-how-a-vehicle-id-becomes-a-mesh).
- **model resource**: the model that the `model` param of a unit BLK names.
  Many units share one. See
  [08 §1.2](08-vehicles-and-models.md#12-how-a-vehicle-id-becomes-a-mesh).
- **DynModel / RendInst**: a DynModel is a dynamic model, for example a
  vehicle. A RendInst is a static placed model, for example a prop. See
  [08 §1.1](08-vehicles-and-models.md#11-how-the-game-stores-models).
- **GeomNodeTree / skeleton**: the node tree of a model,
  `<resource>_skeleton`. It gives the node pivots. See
  [08 §1.6](08-vehicles-and-models.md#16-lod-and-skeleton).
- **LOD**: level of detail. LOD0 is the full mesh. See
  [08 §1.6](08-vehicles-and-models.md#16-lod-and-skeleton).
- **`_dmg` / `_xray` / `_collision`**: resource variants of a model: the damaged
  model, the X-ray model, and the collision model. See
  [08 §1.1](08-vehicles-and-models.md#11-how-the-game-stores-models).
- **collision hull / `CollisionNode` flags**: the collision model holds one
  hull per DM part. Each node has flags such as `TRACEABLE`, `PHYS_COLLIDABLE`
  and `SOLID`. See [08 §3.3](08-vehicles-and-models.md#33-collision-hulls).
- **`dm_skeleton`**: the node set of the DM parts of a model,
  `<model>_dm_skeleton`. See
  [03 §2.4b](03-replays.md#24b-spawns-ecs-messages-and-damage-state).
- **cupola**: the commander cupola. Its armor is the part
  `turret_commander_dm`. See [08 §3.1](08-vehicles-and-models.md#31-tank-armor-data).
- **camo overlay**: the tiled camouflage texture that the shader blends over
  the unpainted `_c` diffuse. See
  [08 §2.1](08-vehicles-and-models.md#21-the-base-layer-and-the-overlay).
- **full-repaint skin**: a skin that replaces the diffuse of each part. It is
  not an overlay. See [08 §2.5](08-vehicles-and-models.md#25-skin-kinds).
- **`unittags.blk`**: the role and class tags of each unit. See
  [08 §5a](08-vehicles-and-models.md#5a-unit-type-tags-unittagsblk).
- **`WeaponSlots`**: the unit BLK block of the aircraft weapon presets. See
  [08 §3.5](08-vehicles-and-models.md#35-weapon-loadouts).
- **`commonWeapons` / `gunner0`**: the block of the primary weapon of a tank,
  and the trigger name of the main gun. See
  [08 §4.1](08-vehicles-and-models.md#41-the-two-data-sources).
- **`limitsTable`**: gun elevation limits by turret yaw, for example over the
  engine deck. See [08 §4.1](08-vehicles-and-models.md#41-the-two-data-sources).

## World and units

- **HM2**: a heightmap block. It decodes with the ooz/Kraken (Oodle) codec.
  See [07](07-terrain-maps-and-missions.md).
- **LandRayTracer / lmap / gridHt**: the full-level heightfield. See
  [07](07-terrain-maps-and-missions.md).
- **RIGz / rendinst**: the prop block: buildings and trees placed by matrix.
  See [07](07-terrain-maps-and-missions.md).
- **landclass / albedo**: the biome-to-texture chain that bakes the ground
  color. See [07](07-terrain-maps-and-missions.md).
- **dynaf composit**: the dynamic airfield placed on air maps. See
  [07](07-terrain-maps-and-missions.md).
- **TMatrix**: a Dagor 4x3 transform matrix. It is BLK param type `0x0b`
  (`FLOAT12` / `m4x3f`), 48 bytes. See [02](02-file-formats.md).
- **ECS**: the entity component system the game uses. Replays carry net ECS
  messages. See [03](03-replays.md).
- **level**: the world of a map, the file `levels/<stem>.bin`. The level key is
  the stem, and it often differs from the display name. See
  [07 §5.1](07-terrain-maps-and-missions.md#51-level-naming).
- **mission**: the battle setup on a level, as a BLK under
  `gamedata/missions/`. It sets the mode, the units, the zones and the
  triggers. See [02 §3.10](02-file-formats.md#310-mission-files-blk-missions-user-missions).
- **trigger**: the mission logic unit. It has events, conditions and actions.
  See [02 §3.10](02-file-formats.md#310-mission-files-blk-missions-user-missions).
- **world axes**: a right-hand frame in metres. `x` points east, `z` points
  north, and `y` is the height. See
  [07 §4.1](07-terrain-maps-and-missions.md#41-world-coordinates).
- **map extent (`mapCoord`, `tankMapCoord`)**: the world corners of the air map
  and of the tank map of a level. See
  [07 §4.2](07-terrain-maps-and-missions.md#42-per-level-map-extents).
- **normalized map coordinates**: map positions from 0 to 1, with `y` down.
  8111 and the replay use them. See
  [07 §4.3](07-terrain-maps-and-missions.md#43-world-to-map-transform).
- **battle area**: the mission zone where a battle takes place. The HM2 block
  covers the 4 km battle area of a tank map. See
  [07 §1.2](07-terrain-maps-and-missions.md#12-the-hm2-block-battle-crop).
- **`lndm` / `LTdump`**: the dump header inside the `lmap` block, and the
  decompressed LandRayTracer dump. See
  [07 §1.3](07-terrain-maps-and-missions.md#13-the-landraytracer-full-map-heightfield).
- **RendInstGenData / pool**: the prop dump of the `RIGz` block. Each pool is
  one asset. `posInst` marks a tree with a position only. See
  [07 §2.2](07-terrain-maps-and-missions.md#22-grid-header-and-pool-descriptors).
- **composit / `objectGroups`**: a placed group of objects. A mission places
  one through an `objectGroups` node. See
  [07 §2.4](07-terrain-maps-and-missions.md#24-dynamic-composits-airfield-dynaf).
- **biome index / mega detail**: a texture of landclass index values that tiles
  over the map. See [07 §3.2](07-terrain-maps-and-missions.md#32-world-mapping-and-tiling).
- **LC_MEGA splatting**: the blend of detail textures by a splatting map, for
  city and field ground. See
  [07 §3.3](07-terrain-maps-and-missions.md#33-lc_mega-splatting).
- **bombing area**: the mission object of an air battle base. Its health and
  burn rules are mission keys such as `hp`, `hpFireMult` and `fireSpeed`. See
  [07 §6.1](07-terrain-maps-and-missions.md#61-the-bombing-area).
- **`weaponDamage`**: the base damage of a weapon preset in `wpcost.blk`. A
  bomb removes `weaponDamage / baseHP` of a base. See
  [07 §6.3](07-terrain-maps-and-missions.md#63-bomb-damage-against-a-base).
- **`coordencode` / `SpaceTime`**: a delta and varint codec for timed positions,
  and the sample that it packs. See
  [07 §4.5](07-terrain-maps-and-missions.md#45-trajectory-codec-coordencode).

## Linux client

- **native Linux client**: `linux64/aces`, with a Vulkan renderer. It uses X11
  (through XWayland on a Wayland desktop) unless it gets the `-wayland`
  argument. See [11](11-misc-game-info.md).
- **BattlEye**: the anti-cheat that the client loads, also on Linux
  (`BEClient_x64.so`). See [11](11-misc-game-info.md).
- **gamescope**: a nested compositor. The game keeps its focus inside it, so it
  continues to draw. See [11](11-misc-game-info.md).
- **FMOD**: the audio engine of the client. Its audio stream is `FMOD Audio`.
  See [11](11-misc-game-info.md).
- **launcher**: the program that updates and starts the game. On Linux it runs
  `linux64/aces -forcestart`. See [11](11-misc-game-info.md).
- **`config.blk` / `settings.blk`**: the user settings file and the built-in
  settings. `config.blk` can change only the keys that `settings.blk` allows.
  See [11](11-misc-game-info.md).
- **`SteamAppId`**: the environment variable that Steam sets. With it the game
  logs in with the Steam account. War Thunder's Steam app id is `236390`. See
  [11](11-misc-game-info.md).

## Tools

- **wt-tools**: the Python format decoders. See [02](02-file-formats.md).
- **WOSF**: the War Thunder Open Source Foundation, a group of public tools in
  Rust. See [02 §3.9](02-file-formats.md#39-the-wosf-rust-toolchain).
- **wt_ext_cli / wt_blk**: the WOSF command-line unpacker and its format
  library, for VROMFS, BLK, DXP and GRP. See
  [02 §3.9](02-file-formats.md#39-the-wosf-rust-toolchain).
- **WtFileUtils**: a second reference reader of VROMFS and BLK, in Python. See
  [02 §3.9](02-file-formats.md#39-the-wosf-rust-toolchain).
- **DAE (Dagor Asset Explorer)**: a Python tool that reads Dagor models,
  textures and levels, and exports models. See
  [02 §3.4](02-file-formats.md#34-game-resource-packs-grp2-grp-and-descriptors),
  [08](08-vehicles-and-models.md).
- **DagorEngine**: the public engine source of Gaijin. See
  [09](09-tooling-and-repos.md).
- **WrplReplayParser**: a C++ replay parser with Python bindings. See
  [03 §3.1](03-replays.md#31-wrplreplayparser-c-with-python-bindings).
- **wrpl-inspector / carve**: a Go replay library and GUI. Its carve step cuts
  one match out of the replay parts. See
  [03 §3.4](03-replays.md#34-the-carve-model-wrpl-inspector).
- **wt_sensor**: a WOSF parser of the radar and IRST BLKs. See
  [03 §2.4](03-replays.md#24-per-tick-unit-state).
- **wt_ballistics_calc**: a WOSF missile flight simulator. See
  [06 §1](06-ballistics-and-armor.md#1-shell-flight-external-ballistics).
- **wt-heatmaps**: a Go server that paints kill heatmaps over the level
  minimap. See [07 §4.5](07-terrain-maps-and-missions.md#45-trajectory-codec-coordencode).
