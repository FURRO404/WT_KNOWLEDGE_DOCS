# 10 — Game modes: TSS tournaments and Squadron Realistic

> Initial research: FURRO404, TSS API capture and squadron rating decode. https://github.com/FURRO404
> Contributors: War-Thunder-Datamine by gszabi99 (the `clanDuel` settings).

This document has two parts:

- Sections 1–8: the public data API of the War Thunder Tournament Service
  System (TSS), `https://tss.warthunder.com`, and the tournament replay page
  and CDN.
- Section 9: the rating of Squadron Realistic Battles (SRE, also called SQB),
  the squadron roster and ratings from the `char` server, and the datamined
  rating settings and the season timing.

New information about the game modes (their APIs and their rules) goes in
this chapter.

The TSS source is empirical research against the live site on 2026-09-24
(about 70 requests, no login) and a read of the site JavaScript
(`static-tss.warthunder.com/js/script.js?v=113`).

Each fact carries a marker:
- **[verified]**: seen in a live reply.
- **[js]**: read from the site JavaScript, not seen in a live reply.
- **[datamine]**: a value in the unpacked game files.
- **[inferred]**: a conclusion that was not tested.

For the replay and session ids that TSS links to, see
[03-replays.md](03-replays.md). For vehicle ids and the economic rank, see
[08-vehicles-and-models.md](08-vehicles-and-models.md). For the `char` server
transport and the BLK reply format, see
[05-char-server-api.md](05-char-server-api.md).

---

## 1. Transport

- There is one endpoint: `https://tss.warthunder.com/functions.php`. The field
  `action` selects the call. [verified]
- A call is a form-encoded POST or a GET with query parameters. Most calls
  accept both. `DetailTournament` works only as a GET, and a POST returns an
  empty body. [verified]
- The replies are JSON, but the server labels them `Content-Type: text/html`.
  [verified]
- The public calls below need no login, no cookie and no token. The server sets
  `PHPSESSID` and `lang=en`, but a client does not need to send them back.
  [verified]
- The server sends `Cache-Control: no-store, no-cache` and no ETag or
  Last-Modified. A client must compare payloads itself to find changes.
  [verified]
- No rate-limit header and no HTTP 429 came back at about one request per
  2 s. The limits are not known.
- All times are Unix epoch seconds in UTC. Most numbers arrive as strings.
  [verified]
- The parameter name for the tournament id changes between calls: `id`,
  `tournamentID` or `tournamentId`. Use the exact name in the tables below.
  [verified]
- Some field names are Gaijin spellings: `single-elumination`,
  `double-elumination`, `coutnryFlag`, `tornamentStatusStyle`,
  `confarmationTeam`. [verified]

## 2. Tournament list: `GetActiveTournaments`

`POST action=GetActiveTournaments`. The reply is about 250 KB. The site sends
`countCard=N`, but the server ignores it and returns the full list. A region or
cluster parameter changes nothing. [verified]

```json
{"status":"OK","my_rating":{"userID":0,"rating":"no_rating"},"countViewTournament":14,
 "data":[{"tournamentID":"25923","nameEN":"Firestorm 4v4 AA Division","typeTournament":"swiss",
  "cluster":"EU","teamSize":"4","minTeamSize":"1","maxTeamSize":"5","amountTeam":"32",
  "countAllTeamsConfirm":"0","dateStartReg":"1790056800","dateConfirmation":"1790545799",
  "dateStartTournament":"1790545800","dateEndTournament":"1790632200",
  "prize_pool":"11250 Golden eagles","icon_tournament":null,"status":"1","active":"0",
  "gameMode":"RB","statisticGroup":"mixed","blitz":"1","rating_a":"0","rating_b":"100000",
  "timeWinnerStr":"1790546400, 1790547420, ...","timeFinal":"1790638920"}]}
```

- The list holds all upcoming tournaments (`status` "1") and the finished
  tournaments of about the last 29 days (`status` "0"). On 2026-09-24 it held
  29 upcoming and 275 finished rows. [verified]
- `active` was "0" on all 304 rows, upcoming and finished. No tournament was
  live in any sample, so the value while a tournament runs is not known. The
  site JavaScript does not read `active` from a list row. Do not use it until a
  live sample shows what it means. [verified values, js]
- `typeTournament`: `single-elumination`, `double-elumination`, `swiss`.
  [verified]
- `gameMode`: `RB`, `AB`, `HB`. HB means Historical Battles, the TSS name for
  Simulator Battles (SB). In the game files `historical` means RB, not SB.
  [verified]
- `statisticGroup`: `tank`, `aircraft`, `ship`, `mixed` (tanks and aircraft).
  [verified]
- `teamSize`: 1, 2, 3, 4, 5 and 8 were seen. `minTeamSize`–`maxTeamSize` is the
  roster size. [verified]
- `rating_a`–`rating_b` is a gate on the player PvP rating, the same scale as
  the `pvp_ratio` that `infoTeam` returns. This TSS rating is not the SRE
  rating (section 9.1). `0`–`100000` means no gate. The
  "Division" events use caps such as `0`–`1215` or `0`–`1300`. The site filters
  the list against the viewer rating in the browser. [verified values, js filter]
- `cluster` was "EU" on every row, also for events that start at times for
  other regions. [verified]
- `amountTeam` is the maximum number of teams. `countAllTeamsConfirm` is the
  number of confirmed teams (section 5). [verified]
- The site caches this list for 20 minutes in the browser. [js]

### 2.1 Banner image

`https://tss.warthunder.com/icon_tournament/{name}.png`. `{name}` is
`icon_tournament` when it is not null, else `md5(str(tournamentID))`. The
detail reply gives the full file name in `icon_name`. [verified]

### 2.2 Tournament page

`https://tss.warthunder.com/index.php?action=tournament&id={id}`. The page is a
JavaScript shell. The HTML holds no tournament data. [verified]

## 3. Lifecycle and times

| Phase | List `status` | Detail `tournamentStatus` / style | `status_registration` |
|---|---|---|---|
| Registration open | "1" | `open` / `success` | "" |
| Live | "1" [inferred] | `live` / `danger` [js] | not seen |
| Finished | "0" | `past` / `default` | "off" |

- The site computes the status as follows, and the server value matched it on
  every sample: `past` when `dateEndTournament <= now`, else `open` when
  `dateStartReg <= now <= dateStartTournament`, else `live` when
  `dateStartTournament <= now <= dateEndTournament`. [js, verified match]
- No tournament showed before its registration opened. Registration opens at
  06:00 UTC on almost all rows (303 of 304). For the usual events it opens
  3.3 to 7.5 days before the start. Special events (qualifiers and finals of a
  series) opened up to 18 days before the start. [verified]
- Before the start, `dateEndTournament` is a placeholder: exactly
  `dateStartTournament + 86400`. After the end, the server writes the real end
  time. A multi-day final had a real end 251 hours after its start. Do not use
  it as an end time before the tournament is finished. [verified]
- `dateConfirmation` is `dateStartTournament - 1`. Registration closes at the
  start. [verified]
- A timed check-in exists only when `get_about_info` gives `check_in` "1". The
  site then shows a check-in deadline at `dateStartTournament - 3600`. `check_in`
  was "0" on every sample. [verified values, js rule]
- `status_live` and `status_confirmation` were "off" on every sample, before and
  after. `status_bracket` was `false`. [verified]
- `timeWinnerStr` and `timeFinal` (list) and `dateBattle.playOffTime[]` and
  `dateBattle.final` (detail) are the planned round times. [verified]

## 4. Tournament detail: `DetailTournament`

`GET functions.php?action=DetailTournament&id={id}`. The reply is a flat
object of about 60 KB, with no `data` wrapper. It also works for tournaments
older than the list window. [verified]

```json
{"tournamentID":"25920","nameEN":"2x2 RBm Tanks","typeTournament":"single-elumination",
 "typeTournamentShort":"SE","difficulty":"realistic","gameMode":"RB","teamSize":"2",
 "maxTeamSize":"2","amountTeam":"64","cluster":"EU","timeLimit":"15","maxRespawns":"3",
 "isLimitedAmmo":"1","amountBattles":"1",
 "countryTeamA":"usa, germany, china, ussr, britain, japan, italy, france, sweden, israel",
 "prize_pool":"3600 Golden eagles","countAllTeamsConfirm":"3","tournamentStatus":"open",
 "rewards":{"1":{"place":"1","reward":"Premium Account 3 days (Premium), ... 500 (GE)"}},
 "allLocations":[{"key":"normandy_Conq2","name":"[Conquest 2]\nNormandy","image":"normandy"}],
 "allTechnics":{"usa":[{"image":"us_m47_patton_II","rank":"5","name":"M47"}]},
 "dateBattle":{"playOffTime":["1790514000","1790515020"],"final":"1790519100"},
 "blockRegTournament":{"start":"22.09 06:00 UTC","finish":"27.09  12:49 UTC"},
 "descriptionTournamentEN":"[b]Blitz Tournament 2х2 RBm[/b]\n...",
 "discussion_EN":"[url=https://discord.gg/wt-esport]Discord[/url]",
 "icon_name":"709732b52c5bf782d327f289404e5491.png","listTeams":[],"listTeams_not_confirm":[]}
```

- **Vehicles.** `allTechnics` maps a nation to a fixed list of allowed
  vehicles. `image` is the unit id of the datamine. `rank` is the vehicle rank
  (era I–VIII), the same value as `rank` in `char.vromfs.bin/config/wpcost.blk`.
  The battle rating is not in the reply. Compute it from `wpcost.blk`:
  `BR = economicRank / 3 + 1`, with `economicRankHistorical` for RB,
  `economicRankArcade` for AB and `economicRankSimulation` for SB. Example:
  `us_m47_patton_II` has economic rank 19 → BR 7.3. [verified]
- Every sampled tournament (tank, aircraft SB, naval, mixed) used a fixed
  `allTechnics` list. No sample used the player's own vehicles or a BR range.
  The match data model has `ranksmin`/`ranksmax` fields (section 6), but they
  were empty. [verified]
- `countryTeamA` and `countryTeamB` were the same on every sample. [verified]
- **Maps.** `allLocations[]` gives `key`, a display `name` (with a mode prefix
  and a newline) and an `image` key. [verified]
- **Rules.** `timeLimit` (minutes), `maxRespawns`, `isLimitedAmmo`,
  `isLimitedFuel`, `amountBattles` (games per match), `killLimit`,
  `scoreLimit`, `weather`, `daytime`. [verified]
- **Text.** `descriptionTournamentEN`/`RU` and `regulationsEN`/`RU` are BBCode
  (`[b]`, `[br]`, `[url=...]`). `descriptionTournament` and `regulations` are the
  HTML forms. Entry rules such as "anticheat required" are only in this free
  text. [verified]
- **Status.** The detail also has `status` ("1" or "0", the same value as
  the list row) and `active` ("0"). [verified]
- **Teams.** `listTeams` (confirmed) and `listTeams_not_confirm`. The same lists
  as `GetListAllTeam` (section 5). [verified]

### 4.1 `get_about_info`

`POST action=get_about_info&tournamentId={id}` gives the tournament fields under
`data.tournaments`. The detail does not have `statisticGroup`, `rating_a` or
`rating_b`, and this call has all three. [verified] It also gives `check_in`, `check_captain_online`, `second_chance`, `autoBattle`,
`bronzeMatch`, `rating`, `time_start {timeWinnerStr, timeFinal, startDelayTime,
timeInviteGroup}`, `allRewards` and `missions`. [verified]
`data.tournaments.tournamentName` is an internal id such as
`40405763_1788802280`, not a display name. Use `nameEN`. [verified]

## 5. Teams and registration

`POST action=GetListAllTeam&tournamentID={id}` gives:

- `listTeamsReady`: confirmed teams. The count equals `countAllTeamsConfirm`.
- `listTeamsNotReady`: registered teams that are not confirmed.
- `listTeamsId`: all teams, as an object with `idTeam` keys, not a list.

[verified]

```json
{"idTeam":"<team id>","teamName":"<team name>","teamCaptainID":"<captain uid>",
 "nickCaptain":"<captain nick>","coutnryFlag":"ru","iconTeam":false,"numberMember":3}
```

- **Confirmed** means that the captain confirmed the roster. The confirm
  button shows only when `teamSize <= members <= maxTeamSize`, and the captain
  can undo it (`confarmationTeamRevert`). A team with a full roster can still be
  unconfirmed. [js, verified example]
- `numberMember` is a display row index, not a member count. [verified]
- No registration time exists. `idTeam` is a global auto-increment number, so it
  shows the order of registration. A diff of the `idTeam` sets between two reads
  finds new teams. [verified]
- Teams can leave, disband or lose confirmation, so the sets can shrink. The
  confirmed count of one tournament fell from 3 to 2 in 16 minutes. [verified]
- `POST action=searchAllTeam&tournamentID={id}` gives `usersCount` (the real
  member count), `confirmed`, `typeRegister` and `needPassword`, for
  unconfirmed teams only. [verified]
- `POST action=infoTeam&tournamentID={id}&teamID={idTeam}` gives
  `users_team[] {userID, nick, role ("captain"|"member"), realName, pvp_ratio}`
  and `param_team.confirmed`. [verified]

## 6. Schedule, results and replays

- **Single and double elimination.**
  `POST action=get_shedule_matches&tournamentId={id}` gives
  `data.all_teams[] {teamName (uuid), realName, id_team}` and
  `data.all_matches[] {id, typeBracket, round, teamA, teamB, winner, scoreA,
  scoreB, finished, timeInvite, timeStart}`. `teamA`, `teamB` and `winner` are
  uuids that map through `all_teams`. `typeBracket` values include `Winner`,
  `Looser`, `LooserFinal`, `Semifinal` and `Final`. It returns an empty list for
  Swiss. [verified]
- The schedule times are the plan, not what happened. `timeStart = timeInvite
  + 60`, and the Final `timeInvite` equals `timeFinal`, which can be later than
  the real end. [verified]
- **Swiss.** `POST action=GetArraySwissData&tournamentID={id}&id_group=1` gives
  `data.GroupMatch[] {id, round, teamA, teamB, realNameA, realNameB, winner,
  scoreA, scoreB, statsStatus (1 = played), timeInvite, timeStart}` and
  `data.GroupStage[][] {realName, points, won, draw, defeats, buchholz_points,
  KD, frag}`. The Swiss times match the real play. [verified]
- In a 2026-10 reply, `data.GroupMatch` was not a flat list. It was an
  object of the form `{"0": {"<timeInvite>": [match, ...]}}`, with the matches
  grouped by their invite time. Read all nested lists. [verified, 2026-10]
- **Groups.** `GetArrayGroupData` / `GetArrayGroupDataShort` (`tournamentID`,
  `id_group`). Empty for Swiss. [verified]
- **Bracket tree.** `GetArrayBracketData` / `GetArrayBracketDataShort`
  (`tournamentID`) give the nested tree that the site draws. [verified]
- **Battles of a match.**
  `GET action=getListAllBattles&tournamentID={id}&idMatch={m}&typeBracket={t}`
  gives `[{name, url, winner, statusReplay, host, teamA, teamB}]`. `url` is the
  decimal session id of the replay. `statusReplay` is `view replay`,
  `technical victory` (a forfeit, with an empty `url`) or `wait` [js]. [verified]
- For a Swiss tournament, send `typeBracket=Swiss` with a capital S. The
  lowercase `swiss` gives an empty reply. `getInfoMatch` takes the same value
  in `typeMatch`. [verified, 2026-10]
- **One match.** `GET action=getInfoMatch&tournamentID=&idMatch=&typeMatch=`
  gives the team names, `userListA`/`userListB`, the scores, `timeInviteMatch`,
  `timeStartMatch`, `allBattleTime` and `lisUnits {ranksmin, ranksmax, class,
  maxCount, type}`. [verified]
- More `getInfoMatch` fields, seen in 2026-10: `matchParametrs` holds the
  map that was played (`mission[]`), `killLimit`, `scoreLimit`,
  `isLimitedFuel` and `spectators`. `listDictTeamA` and `listDictTeamB` map
  each `userID` to a nick. Each `lisUnits[]` entry also has the display `name`
  of the vehicle and a `team`. In those replies `ranksmin`, `ranksmax`,
  `class` and `maxCount` were empty. A roster can be larger than `teamSize`:
  the 8v8 events had 9 to 10 players for each team. [verified, 2026-10]
- The map keys in the tournament's `allLocations` do not have the same case as
  the mission files. For example `sinai_Dom` and `tss_rheinland_Dom` are the
  missions `cta/tanks/sinai/sinai_dom.blk` and
  `cta/tournament/tss_rheinland_dom.blk`. Naval maps are
  `cta/ships/<map>/<map>_ndom.blk`. [verified, 2026-10]
- **Player stats of a match.** `POST action=tournamentInfoAll` (`tournamentID`,
  `idMatch`, `typeMatch`). [verified]
- **Final placings.** `POST action=GetStatsTournamentShort&tournamentID={id}`
  gives `readyTopTeamsTournament[] {realName, place, userID, role, FRAG, DEATH,
  ...}`. [verified]
- No call gives a per-match result time. `dateEndTournament` (after the end) is
  the only real completion time. [verified]

### 6.1 Air duel missions

- TSS air duels use the missions `gladiators_air_1x1_norespawn`,
  `gladiators_air_2x2_norespawn`, `gladiators_europe_air_1x1_norespawn` and
  `gladiators_europe_air_2x2_norespawn` (`gamedata/missions/cta/planes/duel/`),
  in realistic and simulator difficulty. A "2x2" battle is often played by one
  player on each side. One replay can hold several rounds: the same player uid
  then has one track entity for each round. [verified, 2026-10 data]
- The replay JSON gives these duels an empty `mission_mode`. Some 1x1 duels
  are also played in arcade difficulty. Simulator shows as the `difficulty`
  value `hardcore`. [verified, 2026-10 data]
- TSS team air battles use Air Domination missions, not the duel missions.
  Their `mission_path` is under `gamedata/missions/cta/tournament/`, not
  `cta/planes/`, and their `mission_mode` is `Air Domination`. Examples:
  `korea_#_cap_jets_ad`, `norway_#_cap_jets_ad`, `arcade_canyon_snow_#_cap_jets_ad`,
  `korea_lake_#_cap_jet_ad`, `air_kamchatka_noautocap_jet_ad`,
  `avg_red_desert_noautocap_jet_ad`, `avn_japan_noautocap_jet_ad` (`#` is a
  number). Most are 2v2 and some are 4v4 (45 and 10 in a sample of 60).
  The same folder also holds ground `Domination` missions with tanks, such as
  `tss_normandy_dom` and `tss_rheinland_dom`. Thus a filter on `/planes/` in
  the path finds only the duels. [verified, 2026-10 data, about 3,000 Air
  Domination battles against 900 duels]
- Guns are locked for the first 30 s of each round. In the replay tracks this
  shows as no gun hit earlier than 23.0 s after the shooter's first track
  sample of that round (9,227 gun hits checked), because a track starts about
  7 s into the round. The lock applies to every round, not only the first.
  Missiles are not part of this check. [verified, 2026-10 data]

## 7a. warthunder.com replay page

The replay page `https://warthunder.com/{lang}/tournament/replay/` is a Vue app
that shows only after login. Its API paths (from the page code):

| Purpose | Call |
|---|---|
| Replay list | `GET /{lang}/api/replay`, or `POST` with filter fields |
| One replay | `GET /{lang}/api/replay/{id}` |
| Start the replay in the game client | `GET /{lang}/tournament/watch?sessionId={decimal session id}` |
| Download all parts as a zip | `/{lang}/tournament/replayDownload` |
| Report a player | `POST /{lang}/tournament/claim`, categories from `GET /{lang}/api/replay/claim_categories` |

- **Start replay** sends the session ID in decimal. The page shows it in hex,
  for example `72e390f0000bdcdc` = `8278619900504431836`. Use a 64-bit integer
  (JavaScript `BigInt`) for the conversion. The call needs only the site login
  cookie, and the reply is JSON with a `status` field. `{"status":"ok"}` starts
  the replay in the client that is logged in with the same account.
  `{"error":"SERVER_ERROR_PEER_LOGOUT","status":"failed"}` means that no such
  client is running. [verified, 2026-10]
- Each replay part is a file:
  `https://wt-game-replays.warthunder.com/{hex session id}/0000.wrpl`, then
  `0001.wrpl`, and so on. [verified, 2026-10]
- The CDN path needs all 16 hex digits of the session ID. Some tools write the
  hex ID with no leading zero (15 digits, for example `74b12d40024ef1e`). The
  CDN gives 404 for that form and 302 to the file for the padded form
  `074b12d40024ef1e`. Pad the ID to 16 digits with zeros before you build the
  URL. [verified, 2026-10]
- The CDN sends a 302 to the file on a second host,
  `https://wt-replays-cdnnow.cdn.gaijin.net/{hex session id}/NNNN.wrpl`.
  [verified, 2026-10]
- The CDN is not only for tournaments. It also keeps the server replays of
  normal random battles (ground and air). A client replay holds the session
  ID at header offset 732, so the server replay of the same battle can be
  downloaded with it. 48 of 76 random battles from the previous 3 weeks were
  still there. [verified, 2026-10]
- The CDN host `wt-replays-cdnnow.cdn.gaijin.net` sends
  `Access-Control-Allow-Origin` with the origin of the request (also for
  `github.io` and `localhost`, and also on a 404). A web page can thus fetch
  the parts directly. The `wt-game-replays.warthunder.com` address sends only
  a 302 with no CORS header, so a browser cannot follow it.
  [verified, 2026-10]
- To find out if a part exists, send a GET, not a HEAD. A HEAD gives 404 also
  for a part that exists. A GET gives 302, and a GET with a `Range` header
  gives 206. The last part of a replay is the one before the first 404.
  [verified, 2026-10]
- The CDN does not keep replays for a long time. On 2026-10-12, all parts of
  sessions from tournaments of 2026-09-24 to 2026-09-28 gave 404, also with the
  padded ID. The example above, which downloaded earlier in 2026-10, also gave
  404. Sessions from 2026-10-01 and later still downloaded. The retention seems
  to be about two weeks. The exact time is not known. Download a replay soon
  after the match. [verified, 2026-10]

## 7. Other calls

| Action | Method | Params | Notes |
|---|---|---|---|
| `rating_user` | POST | `type` (tank/aircraft/ship/mixed), `page` | Public PvP rating board. `data.rating` has `ab`, `rb` and `hb` lists of 50 rows. `page` counts from 0. |
| `get_bracket_youtube` | POST | `tournamentId` | Group and bracket data together |
| `get_dynamic_score` | GET link | `id`, `name_image` | A score image |
| `GetActiveMyTournaments`, `info_my_team` | POST | | Needs login |
| `get_activeList_room`, `join_room`, `replay_start` | GET | `userID`, `token`, ... | Needs login. The lobby and invite state of a live match. |
| `GetRegion`, `GetAllCountry`, `saveRegionUser` | POST | | Needs login. The profile country, not the server cluster. |
| `addNewTeam`, `joinToTeam`, `liveTeam`, `disbandTeam`, `delUserTeam`, `confarmationTeam`, `confarmationTeamRevert` | POST | | Team write actions. Not probed. |

- There is no news, folder or series call. `folderID` was "" everywhere.
  League pages are separate `index.php?action=league_*` routes. [verified]

## 8. Open questions

- The values of `status`, `active`, `tournamentStatus`, `status_live` and
  `status_confirmation` while a tournament runs. No tournament was live during
  the research.
- Whether the server moves the placeholder `dateEndTournament` while a
  tournament runs. If it does not, the rule in section 3 gives `past` at
  start + 24 h, also for a tournament that runs longer. Until this is known,
  use list `status` "0" as the sign of the end.
- Whether a `check_in` "1" tournament exists, and how its window behaves.
- The rate limits of the site.

---

## 9. Squadron Realistic Battles rating

This section covers the rating of Squadron Realistic Battles (SRE, also called
SQB): the `char` server calls that give the squadron data, the squadron rating
formula, and the datamined settings.

### 9.1 `cln_clan_get`: roster and ratings

- `cln_clan_get` is a `GET /json` read (see
  [05-char-server-api.md](05-char-server-api.md)). Send the header
  `clanId: <id>` or `clanName: <name>`. [verified]
- The answer can be wrapped in a block with a single key. Unwrap it until
  `member_ratings` is present. [verified]
- `members` holds the roster. `member_ratings` holds the ratings of each
  member. `astat` holds the ratings of the squadron. [verified]
- The personal SRE rating is `member_ratings[uid].dr_era5_hist`. The squadron
  rating is `astat.dr_era5_hist`. They are different ratings. [verified]
- `astat` also holds `dr_era0..7_{arc,hist,sim}`, `ftime_hist`,
  `akills_hist`, `gkills_hist`, `battles_hist`, `wins_hist`, `deaths_hist`,
  `activity` and `clan_activity_by_periods`. [verified]
- The TSS rating of a player (`pvp_ratio`, section 5) is also a different
  value. Do not use it as the SRE personal rating. [verified]

### 9.2 Squadron rating formula

The squadron rating is the sum of the 20 best member ratings, plus the sum of
all other member ratings divided by 20, rounded down:

```
astat.dr_era5_hist = floor( sum(top 20 member dr_era5_hist)
                          + sum(all other member dr_era5_hist) / 20 )
```

- The values 20 and 20 are `topPlayersCountForClanRating` and
  `otherPlayersDivisorForClanRating` in the `clanDuel` block (section 9.4).
- The formula was checked on 6 live squadrons with 78 to 128 members. Each
  result matched `astat.dr_era5_hist` to within the rounding. Example: top-20
  sum 40043.6, sum of the others 163603.3, result 48223.7, `astat` 48223.
  [verified 2026-10-18]

### 9.3 Squadron leaderboard

- The leaderboard action is `cln_clan_get_leaderboard` with
  `sortField=dr_era5_hist`. A page holds 200 rows at most. [verified]
- `sortField=dr_era5_sim` gives `BAD_REQUEST`. `sortField=dr_era5_arc` is
  accepted, but it gives 0 for every squadron. [verified]

### 9.4 Datamined `clanDuel` settings

The unpacked file `char.vromfs.bin_u/config/game_settings.blkx` has a
`clanDuel` block with these keys: [datamine]

| Key | Value |
|---|---:|
| `useSingleEra` | `true` |
| `fastGrowthLimit` | 1500 |
| `tier1Limit` | 2100 |
| `tier2Limit` | 2400 |
| `tier1EloK` | 32 |
| `tier2EloK` | 24 |
| `tier3EloK` | 16 |
| `topPlayersCountForClanRating` | 20 |
| `otherPlayersDivisorForClanRating` | 20.0 |
| `periodicDiminish1Multiplier` | 0.9 |
| `periodicDiminish1PeriodDays` | 7 |
| `periodicDiminish2Multiplier` | 0.8 |
| `periodicDiminish2PeriodDays` | 7 |
| `periodicDiminish3Multiplier` | 0.5 |
| `periodicDiminish3PeriodDays` | 7 |
| `reward/firstRewardDayUnixTime` | 1402927200 |
| `reward/rewardPeriodDays` | 14 |
| `reward/topPlayersRewarded` | 20 |
| `reward/{arcade,historical,simulation}/era5/place1Gold` | 10000 |
| `reward/{arcade,historical,simulation}/era5/place2Gold` | 5000 |
| `reward/{arcade,historical,simulation}/era5/place3Gold` | 2500 |
| `battle_royale_small/superiorityBattlesThreshold` | 20 |
| `battle_royale_small_rb/superiorityBattlesThreshold` | 20 |

- `fastGrowthLimit` 1500 suggests that a different rule applies below 1500
  points. [inferred]

### 9.5 Personal awards

Players reported these approximate awards per match. They are not verified.
[reported, unverified]

| Player points | Win | Loss |
|---:|---:|---:|
| 0–800 | about +32 | about −1 |
| 1500 | about +16 | about −16 |
| 1850 | about +4 | about −28 |
| 2000 and above | about +1 | about −31 to −32 |

The calculation of a personal award is not known. The effect of the
`periodicDiminish*` keys is not known.

### 9.6 Season and BR-cap timing [verified, 2026 match and rating history]

A season lasts two months and starts on the 1st of an odd month (January, March,
May, July, September, November). The max BR steps down once a week. Gaijin
posts the schedule in one forum post that it edits for each season
(`forum.warthunder.com/t/4446`). The post often comes out late, and its edit
history is not public.

Two events happen at the season start, and they are independent:

- **The point reset.** Squadron points go to 0 at about 00:00 UTC on the 1st.
  The rating history puts it between 22:30 UTC on the last day of the old season
  and 00:50 UTC on the 1st. The reset was on time at each start from March to
  September 2026.
- **The BR-cap change.** The cap changes later on the 1st. Usually this is in
  the gap between the US slot and the EU slot (about 07:00 to 14:00 UTC).

So the US slot on the 1st usually counts for the new season but plays at the
last cap of the old season (4.7 or 5.0). The exceptions:

| Season start | Points | BR cap |
|---|---|---|
| 2026-01-01 | reset (forum report; the rating history starts after it) | stayed at 4.7. The mode closed and came back at the top cap on Jan 3 at about 21:25 UTC |
| 2026-03-01 | reset 22:30–02:04 UTC | top cap from about 06:53 UTC, at the end of the US slot |
| 2026-05-01 | reset 22:30–04:09 UTC | top cap between 06:25 and 14:08 UTC |
| 2026-07-01 | reset 22:30–02:47 UTC | stayed at 5.0 until about 14:30 UTC, inside the EU slot |
| 2026-09-01 | reset 22:30–00:50 UTC | top cap between 06:47 and 14:05 UTC |

The weekly steps change at the same time of day as the cap change, between the
two slots on the date of the schedule. They fall on the weekday of the season
start (Jan: Thursday, Mar: Monday, May: Friday, Jul: Wednesday, Sep: Tuesday).
In March, week 1 ran 8 days, from Sunday the 1st to Monday the 9th. The posted
schedule can differ from the game. The 2026-01 post put the last step on
Tue 24.02, but the game kept the Thursday rhythm and changed on Thu 26.02.

The match data cannot show the exact minute of a change that falls between the
two slots, because no matches are played then.
