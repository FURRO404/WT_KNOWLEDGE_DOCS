# TSS tournament site API

This document describes the public data API of the War Thunder Tournament
Service System (TSS), `https://tss.warthunder.com`. The source is empirical
research against the live site on 2026-09-24 (about 70 requests, no login)
and a read of the site JavaScript (`static-tss.warthunder.com/js/script.js?v=113`).

Each fact carries a marker:
- **[verified]**: seen in a live reply.
- **[js]**: read from the site JavaScript, not seen in a live reply.
- **[inferred]**: a conclusion that was not tested.

For the replay and session ids that TSS links to, see
[03-replays.md](03-replays.md). For vehicle ids and the economic rank, see
[08-vehicles-and-models.md](08-vehicles-and-models.md).

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
- `gameMode`: `RB`, `AB`, `HB` (HB is simulator battles). [verified]
- `statisticGroup`: `tank`, `aircraft`, `ship`, `mixed` (tanks and aircraft).
  [verified]
- `teamSize`: 1, 2, 3, 4, 5 and 8 were seen. `minTeamSize`–`maxTeamSize` is the
  roster size. [verified]
- `rating_a`–`rating_b` is a gate on the player PvP rating, the same scale as
  the `pvp_ratio` that `infoTeam` returns. `0`–`100000` means no gate. The
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
{"idTeam":"1258945","teamName":"NSTLK","teamCaptainID":"143545842",
 "nickCaptain":"CrossGlitch_","coutnryFlag":"ru","iconTeam":false,"numberMember":3}
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
- **Groups.** `GetArrayGroupData` / `GetArrayGroupDataShort` (`tournamentID`,
  `id_group`). Empty for Swiss. [verified]
- **Bracket tree.** `GetArrayBracketData` / `GetArrayBracketDataShort`
  (`tournamentID`) give the nested tree that the site draws. [verified]
- **Battles of a match.**
  `GET action=getListAllBattles&tournamentID={id}&idMatch={m}&typeBracket={t}`
  gives `[{name, url, winner, statusReplay, host, teamA, teamB}]`. `url` is the
  decimal session id of the replay. `statusReplay` is `view replay`,
  `technical victory` (a forfeit, with an empty `url`) or `wait` [js]. [verified]
- **One match.** `GET action=getInfoMatch&tournamentID=&idMatch=&typeMatch=`
  gives the team names, `userListA`/`userListB`, the scores, `timeInviteMatch`,
  `timeStartMatch`, `allBattleTime` and `lisUnits {ranksmin, ranksmax, class,
  maxCount, type}`. [verified]
- **Player stats of a match.** `POST action=tournamentInfoAll` (`tournamentID`,
  `idMatch`, `typeMatch`). [verified]
- **Final placings.** `POST action=GetStatsTournamentShort&tournamentID={id}`
  gives `readyTopTeamsTournament[] {realName, place, userID, role, FRAG, DEATH,
  ...}`. [verified]
- No call gives a per-match result time. `dateEndTournament` (after the end) is
  the only real completion time. [verified]

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
