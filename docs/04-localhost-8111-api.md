# Localhost 8111 API

> Initial research: this bank, from live capture of the running game.
> Contributors: DagorEngine by Gaijin Entertainment (the map web server source, open-sourced 2023-09-16). https://github.com/GaijinEntertainment/DagorEngine

War Thunder runs a small HTTP server inside the game client. The server gives
live telemetry to a local web page. This page documents the endpoints, the
response shapes, and the limits.

The captures on this page come from a live tank test drive on this machine.
Each block that says "captured live" is real output from that session. Each
block that says "from repo" or "from server UI" comes from source, not from a
live probe. The page labels every field by source.

## Access

The server listens on `127.0.0.1:8111`. Send a GET request to read an endpoint.

```
curl -s -m 3 http://127.0.0.1:8111/<endpoint>
```

The server accepts GET only. The server needs no authentication. The server
sets `Access-Control-Allow-Origin: *` on responses (see Security below).

An unknown path returns HTTP 404. A known endpoint returns HTTP 200.

## Index page: `GET /`

The root path returns the built-in web HUD as HTML. The page draws the minimap,
the indicators, the state list, the chat, and the HUD messages. The page loads
JavaScript from the same server, for example `utils.js` and `cookies.js`.

The page names every data endpoint in its `updateSlow` function. That function
is the authoritative endpoint list:

```
/mission.json
/map_obj.json
/map_info.json
/gamechat?lastId=<n>
/hudmsg?lastEvt=<n>&lastDmg=<n>
/indicators
/state
```

The page also loads:

```
/map.img
/loc/map/primary_objectives?fmt=js
/loc/map/secondary_objectives?fmt=js
```

## `GET /state`

`/state` reports aircraft flight state. The state is invalid for a tank.

Captured live in a tank test drive:

```json
{ "valid": false }
```

When `valid` is `false`, no other field is present.

The server UI lists the state field names for a valid aircraft. These names come
from the `state_columns` table in the page source, not from a live capture:

```
H, m         TAS, km/h    IAS, km/h    M          AoA, deg    AoS, deg
Ny           Vy, m/s      Wx, deg/s    Mfuel, kg  Mfuel0, kg
aileron, %   elevator, %  rudder, %    flaps, %   gear, %     airbrake, %
throttle 1, %   RPM 1   manifold pressure 1, atm   water temp 1, C
oil temp 1, C   pitch 1, deg   thrust 1, kgs   efficiency 1, %
```

The per-engine fields repeat for engines 1 to 4.

## `GET /indicators`

`/indicators` reports the active vehicle instruments. The response is valid for
a tank and for an aircraft.

Captured live in a tank test drive (vehicle `uk_fv721_fox`):

```json
{"valid": true, "army": "tank",
"type": "tankModels/uk_fv721_fox",
"stabilizer": -1.000000,
"gear": 5.000000,
"gear_neutral": 5.000000,
"speed": 0.000000,
"has_speed_warning": 0.000000,
"rpm": 500.000000,
"driving_direction_mode": 0.000000,
"cruise_control": 0.000000,
"lws": -1.000000,
"ircm": -1.000000,
"roll_indicators_is_available": 0.000000,
"first_stage_ammo": -1.000000,
"crew_total": 3.000000,
"crew_current": 3.000000,
"crew_distance": 1.000000,
"gunner_state": 0.000000,
"driver_state": 0.000000}
```

`army` names the vehicle class. `type` gives the vehicle model path. `army`
reads `tank` for a ground vehicle and `air` for an aircraft.

`first_stage_ammo` reports the ready-rack count. On the Fox the value is `-1`,
because the Fox has no modelled ready rack. This field reports the turret-bustle
ready rack and says nothing about the loaded round.

The server UI lists the aircraft indicator names in the `indicator_columns`
table. These names come from the page source, not from a live capture. The set
includes:

```
speed  vario  altitude_10k  aviahorizon_roll  aviahorizon_pitch  compass
rpm  manifold_pressure  oil_temperature  water_temperature  fuel  throttle
prop_pitch  flaps  gears  weapon1  weapon2  weapon3  ammo_counter0..16
```

## `GET /map_info.json`

`/map_info.json` reports the map bounds and a generation counter.

Captured live in a tank test drive:

```json
{
   "grid_size" : [ 1600.0, 1600.0 ],
   "grid_steps" : [ 225.0, 225.0 ],
   "grid_zero" : [ 1519.449951171875, 2497.250 ],
   "hud_type" : 1,
   "map_generation" : 1,
   "map_max" : [ 4096.0, 4096.0 ],
   "map_min" : [ 0.0, 0.0 ],
   "valid" : true
}
```

Fields:

- `map_min` and `map_max` give the world extent of the current picture, in
  metres. See Coordinate system below.
- `grid_size` gives the grid cell size in metres.
- `grid_steps` gives the grid line spacing in metres.
- `grid_zero` gives the world origin of the grid.
- `hud_type` reads `1` for a ground map and `0` for an air map. This mapping is
  cross-checked against air and ground battles.
- `map_generation` counts battles. The value increments on each new battle.
  A client polls this field to detect a map change.
- `valid` reports `true` when a map is loaded.

## `GET /map_obj.json`

`/map_obj.json` reports the live map objects. The objects include the player,
enemy and friendly vehicles, airfields, capture zones, and respawn points.

Captured live in a tank test drive (a populated firing-range session):

```json
[
{"type":"ground_model","color":"#faC81E","color[]":[250,200,30],"blink":0,"icon":"Player","icon_bg":"none","x":0.418987,"y":0.564182,"dx":0.940018,"dy":-0.341124},
{"type":"ground_model","color":"#fa0C00","color[]":[250,12,0],"blink":0,"icon":"TankDestroyer","icon_bg":"none","x":0.476035,"y":0.564365},
{"type":"ground_model","color":"#fa0C00","color[]":[250,12,0],"blink":0,"icon":"MediumTank","icon_bg":"none","x":0.518198,"y":0.559460},
{"type":"ground_model","color":"#fa0C00","color[]":[250,12,0],"blink":0,"icon":"SPAA","icon_bg":"none","x":0.513955,"y":0.677802},
{"type":"ground_model","color":"#fa0C00","color[]":[250,12,0],"blink":0,"icon":"HeavyTank","icon_bg":"none","x":0.613794,"y":0.543762}]
```

The array is trimmed above. The live session held one Player and seven enemy
ground models.

Common fields on each object:

- `type` names the object class. Observed values: `ground_model`, `airfield`.
  Respawn and zone objects use `respawn_base_tank`, `respawn_base_fighter`,
  `respawn_base_bomber`, and `capture_zone`.
- `icon` names the marker shape. Observed values: `Player`, `MediumTank`,
  `HeavyTank`, `TankDestroyer`, `SPAA`. The server UI also handles `Airdefence`,
  `Structure`, `waypoint`, `capture_zone`, `bombing_point`, `defending_point`,
  and the respawn icons.
- `icon_bg` names the background icon, or `none`.
- `color` gives the marker color as a hex string.
- `color[]` gives the same color as an RGB array.
- `blink` reports the blink state. `0` is off. `1` is normal blink. `2` is heavy
  blink. The blink map comes from the server UI.
- `x` and `y` give the normalized position. See Coordinate system below.
- `dx` and `dy` give the heading vector. Only the Player object carried a
  heading in the live capture.

An `airfield` object carries `sx`, `sy`, `ex`, and `ey` instead of `x` and `y`.
These fields give the start and end of the runway line, each normalized 0 to 1.
This field set comes from the `draw_airfield` function in the server UI.

In a full battle this endpoint holds every spotted unit. The `icon:"Player"`
object calibrates the world-to-map transform, because that object marks the
local player at a known world position.

## Coordinate system

`map_obj.json` gives `x` and `y` as normalized fractions of the map picture.
The range is 0.0 to 1.0. `x` increases to the right. `y` increases downward.
The value `(0,0)` is the top-left corner of the picture. The value `(1,1)` is
the bottom-right corner.

`map_info.json` gives the world extent of that same picture. `map_min` is the
world position of one corner. `map_max` is the world position of the opposite
corner. Both values are in metres.

To convert a normalized object to world metres, interpolate between `map_min`
and `map_max`:

```
world_x = map_min[0] + x * (map_max[0] - map_min[0])
world_y = map_min[1] + y * (map_max[1] - map_min[1])
```

The extent is not a fixed frame. Each level has its own extent. An air map is
wider than the tank map of the same level. The extent cross-checks against the
level definition files. On Berlin the server returned `[1024,0]..[3072,2048]`.
The level BLK field `tankMapCoord0/1` in `levels/avg_berlin.blk` read the same
pair. An air battle returned `[-65536,-65536]..[65536,65536]`. So `map_info`
replaces the level BLK for the picture kind that the HUD shows.

See [09-heatmaps-and-coordinates.md](09-heatmaps-and-coordinates.md) for the
coordinate model that the heatmap tools use, and
[07-terrain-and-maps.md](07-terrain-and-maps.md) for the map picture and terrain
extents.

## `GET /map.img`

`/map.img` returns the current map picture. The picture is the same image that
the HUD minimap draws.

Captured live in a tank test drive:

```
HTTP/1.1 200 OK
Content-Type: image/jpeg
Content-Length: 506117
```

The file was a JPEG, 2048x2048 pixels, 3 colour components, about 506 KB.

The server UI requests the picture with a cache-buster query. The value is the
current `map_generation`:

```
/map.img?gen=<map_generation>
```

The client re-requests the picture when `map_generation` changes.

## `GET /mission.json`

`/mission.json` reports the mission objectives and the run status.

Captured live in a tank test drive:

```json
{
   "objectives" : null,
   "status" : "running"
}
```

`status` reports the run state. The captured value was `running`.

`objectives` is `null` in a test drive. In a real mission `objectives` is an
array. Each objective carries `text`, `status`, and `primary`. The server UI
reads these fields. The server UI uses `status` as a CSS class, with the values
`in_progress`, `completed`, and `failed`. These field names come from the
`format_mission_data` and `updateObjectives` functions in the server UI, not
from a live capture.

## `GET /mission`

`/mission` (no `.json`) returned an empty body in the live test drive. The data
consumers use `/mission.json`.

## `GET /hudmsg`

`/hudmsg` reports the HUD message stream. The response holds two arrays:
`events` and `damage`.

Query parameters:

- `lastEvt` gives the last event id that the client already has. The server
  returns only events with a larger id.
- `lastDmg` gives the last damage id that the client already has. The server
  returns only damage lines with a larger id.

Send `lastEvt=0&lastDmg=0` to read from the start.

Captured live in a tank test drive:

```json
{"events":[

],
"damage":[
{ "id": 1, "msg": "PlayerOne (Fox) destroyed ZSU-23-4V", "sender": "", "enemy": false, "mode": "", "time": 6 }
]}
```

Each `damage` entry carries:

- `id` gives the message sequence number. Pass this value back as `lastDmg`.
- `msg` gives the message text. A kill line reads `<killer> destroyed <victim>`.
- `sender` gives the sender name, or an empty string for a system line.
- `enemy` reports whether the sender is an enemy.
- `mode` gives the chat mode, or an empty string.
- `time` gives the battle time in seconds.

The `events` array uses the same entry shape. The array was empty in the test
drive.

In a full battle `damage` carries the kill and damage lines. Read this endpoint
as a kill-and-disconnect timeline. Pair the kill lines with player-left and
crew-lost events to detect wrecks.

## `GET /gamechat`

`/gamechat` reports the in-battle chat.

Query parameter:

- `lastId` gives the last chat id that the client already has. The server
  returns only messages with a larger id. Send `lastId=-1` or `lastId=0` to read
  from the start.

Captured live in a tank test drive:

```json
[

]
```

The chat was empty. Each chat entry uses the same shape as a `hudmsg` entry:
`id`, `msg`, `sender`, `enemy`, `mode`, `time`. The server UI reads these fields.

## `GET /loc/...`

The `/loc/` paths return localized UI strings. The server UI loads two of them.

Captured live in a tank test drive:

```
GET /loc/map/primary_objectives?fmt=js
loc_tbl['map/primary_objectives'] = "PRIMARY GOALS"
```

The `fmt=js` parameter returns a JavaScript assignment. The client evaluates the
line to fill its `loc_tbl` table.

## Valid state versus invalid state

Some endpoints report a `valid` flag. The flag depends on the game mode and the
active vehicle.

| endpoint | valid when | invalid response |
|---|---|---|
| `/state` | in an aircraft | `{ "valid": false }` |
| `/indicators` | in any controlled vehicle | `{ "valid": false }` |
| `/map_info.json` | a map is loaded | `valid` is `false` |

In a tank test drive `/state` is invalid, and `/indicators` and
`/map_info.json` are valid. When `valid` is `false`, the endpoint omits every
data field. A client must check `valid` before it reads any other field.

## Polling model

The server UI polls the data endpoints on a fixed timer. The `init` function
sets two timers:

- `updateSlow` runs every 500 ms (2 Hz). This timer fetches `/mission.json`,
  `/map_obj.json`, `/map_info.json`, `/gamechat`, `/hudmsg`, `/indicators`, and
  `/state`.
- `updateFast` runs every 25 ms (40 Hz). This timer only redraws the canvas.
  It sends no network request.

So the game's own UI reads every data endpoint at 2 Hz. A client interpolates
positions between fetches, the same way the UI does.

A client does not need to poll every endpoint. A client can poll
`map_generation` from `/map_info.json` as a battle-change trigger, and read the
rest another way. So 8111 is not a hard dependency for a live map. A client
works without the socket.

## Limits

- The server is read-only telemetry. No endpoint accepts a write.
- The server accepts GET only.
- The retail client binds the `127.0.0.1:8111` family.
- The feature is opt-in. The `allowWebUi` option gates the server. The option
  is off by default.
- The data rate is low. The UI polls at 2 Hz. A client that polls faster gains
  little, because the server updates the values at the game tick.

## Security

The map HTTP listener has no authentication, no Origin check, and no Host check.
The listener sets `Access-Control-Allow-Origin: *`. The engine source binds
`0.0.0.0` on the base implementation
(`prog/gameLibs/webui/httpserver.cpp` in DagorEngine). The retail client uses
the `localhost:8111` family. When the feature is on, any LAN peer, or any web
origin that the user visits, can read the live telemetry. The listener holds no
account token. So the exposure is telemetry and phishing, not account access.

Do not expose the port beyond localhost. Keep `allowWebUi` off unless a local
tool needs it.

## Repository status

- Field meanings that a test drive cannot show come from full battles. A live
  map client polls `map_generation` as a battle-change trigger, reads `/hudmsg`
  for a kill-and-disconnect timeline, and uses `map_obj.json` with
  `map_info.json` to calibrate and check the world-to-map transform.
- The Dagor engine's own web server source
  (`prog/gameLibs/webui/httpserver.cpp`) is the upstream implementation of this
  API, not a consumer of it.

## Cross-references

- [03-replays.md](03-replays.md) — replay capture, an offline alternative data
  source to 8111.
- [07-terrain-and-maps.md](07-terrain-and-maps.md) — the map picture, the level
  extents, and the terrain that back `map.img` and `map_info`.
- [09-heatmaps-and-coordinates.md](09-heatmaps-and-coordinates.md) — the
  coordinate model that consumes the normalized positions from `map_obj.json`.
