# 11 — Misc game information

> Initial research: FURRO404, Linux client behavior and the in-game chat. https://github.com/FURRO404
> Contributors: War-Thunder-Datamine by gszabi99 (the chat scripts and text tables); WrplReplayParser by LivingTheDagor (the chat packets in replays).

This chapter holds notes about the game that fit no other chapter:

- how the game client and its launcher behave on the desktop: windows, focus,
  audio, start-up arguments and Steam detection
- the in-game chat: the menu chat (IRC), the battle chat, the chat commands,
  and the name privacy options

## Native Linux client window behavior

- The native Linux client (`linux64/aces`) has two window backends, X11 and
  Wayland. X11 is the default, so on a Wayland desktop the game runs through
  XWayland. In its X11 mode the window class (`WM_CLASS`) is
  `War Thunder (Vulkan, 64bit)`, and the renderer name is part of that string.
- At start the client checks for a Wayland session. In build 2.59.0.54 it
  reads `XDG_SESSION_TYPE` and logs
  `wayland: present because XDG_SESSION_TYPE value = wayland`. Some other
  builds check `XDG_RUNTIME_DIR` and log
  `wayland: present because XDG_RUNTIME_DIR found`.
- Next it reads `linux{ wayland:b }` from its settings and then looks for a
  `-wayland` command-line argument. If neither is set, it logs
  `wayland: use x11 due to configuration`.
- `linux{ wayland:b=yes }` in `config.blk` has no effect. The client loads
  `config.blk` over its built-in `settings.blk`, and it accepts only the keys
  that file allows. It logs
  `Settings: '(null)/linux' is not allowed for overwrite! check settings.blk`
  and drops the block.
- The `-wayland` argument works. The argument parser is Dagor's standard one,
  so `--wayland` works too. With it, the log lists each `wayland: output` with
  its scale, and the client opens a native Wayland window.
- Wayland mode reads the integer `wl_output` scale. With KDE fractional scaling
  (for example 135%, which is reported as scale 2), the window comes out
  oversized and spills past the monitor.
- Wayland mode does not fix the focus problem. The client still stops
  rendering when it loses focus. [tested on KDE Plasma 6, Wayland session]
- The native Linux client loads BattlEye. In build 2.59.0.54 the log shows
  `init anticheat flags: 2` and `[BEAC] Loading DLL from .../linux64/BEClient_x64.so`.
  A debugger attach or a process memory read can trigger the anti-cheat. Use
  a copy of the binary for static analysis.
- The notes below on minimizing come from the X11 mode.
- The client minimizes its own window when it loses focus. It does this in both
  the Fullscreen and the Windowed display modes. The binary imports
  `XIconifyWindow`, and no in-game setting turns this off.
- The client also stops rendering while it is unfocused, in both X11 and
  Wayland mode. In X11 mode, a KWin rule that
  forces "Minimized" to No keeps the window on screen, but the window shows a
  frozen frame. To keep it drawing, run the game nested inside gamescope. The
  game then keeps focus inside gamescope all the time.
- The client has an option to play sound while its window is inactive
  (`USEROPT_PLAY_INACTIVE_WINDOW_SOUND`). It reacts to the game's own focus
  state, so it never triggers when the game is nested in gamescope. The client
  plays audio through FMOD. Its PulseAudio/PipeWire stream is named
  `FMOD Audio`, with process binary `aces`, so an outside tool can change the
  game's volume by matching that stream.
- The Linux launcher (`launcher`, a sciter/GTK program) starts the game with
  glib's `g_spawn_async`. Its update settings define the command line: on Linux
  it is `linux64/aces -forcestart -add_file_to_report "<launcher log path>"`,
  run from the game folder.
- The launcher hides the "Fullscreen (windowed)" display mode on Linux. It
  offers only Fullscreen and Windowed there, and the default is Fullscreen.
- Launcher command-line flags found in the binary include `-justupdate`,
  `-appid`, `-localversion`, `--silent`, `--lang` and `--log`.
- Steam detection on Linux: the launcher and `linux64/aces` both read the
  `SteamAppId` environment variable (Steam sets it on launch) and call
  `SteamAPI_Init` from the bundled `libsteam_api.so`. The Steam install has no
  `steam_appid.txt`, so without `SteamAppId` the init fails and the game shows
  the Gaijin login page. With it, the game logs in with the Steam account.
  The launcher log records the result as `"steam": {"isSteamVersion": true,
  "isLaunchedFromSteam": <bool>, "steamAppId": <236390 or 0>}`.
- War Thunder's Steam app id is `236390`. The `aces` binary also contains the
  string `--nosteam` (behavior not tested).
- Under Flatpak Steam, the native client runs in the Steam Linux Runtime
  (soldier) container, which is started through the Flatpak portal. A
  `gamescope ... -- %command%` launch option then does not nest the game:
  `aces` gets the desktop's `DISPLAY`, not the gamescope Xwayland display.

## In-game chat

The game has two chat systems. They use different transports.

| Chat | Where | Transport |
|---|---|---|
| Menu chat | Hangar: public rooms, private messages, squad, squadron, threads, World War | An IRC client in the game (`chatClient.cpp`, the `gchat_*` script functions) |
| Battle chat | In a match: All, Team, Squad | Game server packets (`chatReplay.cpp`, the `chat_*` script functions) |

Sources: the UI scripts in `gui.vromfs.bin/scripts/chat/`, the text tables in
`lang.vromfs.bin/lang/menu_chat.csv`, and a static read of the Linux client
(build of 2026-08). [datamine, static analysis]

### Menu chat (IRC)

- The client errors are the standard IRC numeric replies, for example
  `chat/error/401` "No such nick/channel", `403` "No such channel",
  `404` "Cannot send to channel", `461` "Not enough parameters",
  `482` "You're not channel operator".
- The script sends raw IRC lines with `gchat_raw_command`, for example
  `join #room`, `part #room`, `kick #room nick`, `invite nick #room`,
  `MODE #room +i`. The client also uses its own `x` commands: `xtjoin` and
  `xtmeta` (threads), `xinvite` (delayed squad invite), `xpost`, `mpost`.
- Room id prefixes:

| Prefix | Room |
|---|---|
| `#<name>_<lang>` | Public lobby room, one for each language (`#lobby_room_` type) |
| `#_clan_<clan id>` | Squadron room |
| `#_msquad_` | Squad room |
| `#_x_thread_` | Thread room |
| `#_ww_` | World War operation room |
| no `#` | Private messages: the room id is the other player's nick |

There is no IRC room for a battle. The battle chat does not use IRC.

#### Chat commands

A message that starts with `/` or `\` is a command when its first word is in
the command list. The help text (`menuchat/help`) lists these:

| Command | Action |
|---|---|
| `/help` | Show the help. |
| `/msg <nick> <text>` or `/<nick> <text>` | Private message. |
| `/join #room [password]` | Join or make a room. The `#` is optional. |
| `/part [#room]` | Leave a room. |
| `/mode +i` | Make the current room invitation-only (room creator). |
| `/invite <nick>` | Invite a player to the current room (room creator). In the squad room it is a squad invite. |
| `/sinvite <nick>`, `/squad_invite <nick>` | Invite a player to your squad. |
| `/sremove <nick>`, `/squad_remove <nick>` | Remove a player from your squad. |
| `/kick <nick>` | Kick from the current room (in the squad room: remove from the squad). |
| `/sready`, `/squad_ready` | Set your squad ready flag. |
| `/shelp` | Show the squad help. |
| `/edit` | Edit the current thread. |

The list also has `reauth`, `xpost`, `mpost` and `p_check` (a presence check
that only moderators can use). A listed command that the script does not
handle goes to the IRC server as a raw line. [datamine]

#### Localized messages (`LMSG`)

The client runs each received menu-chat message through
`g_chat.localizeReceivedMessage`. A message that starts with `LMSG ` holds a
JSON value, and each reader sees it as text in their own language:

- a string: a localization key
- `{"l": "<loc key>", <param>: ...}`: a key with parameters
- `{"t": "<text>"}`: plain text
- `"c"`: a color tag: `av` (active), `ul` (user log), `tb` (blue team),
  `tr` (red team)
- an array: the parts, joined

The game uses this for its own system messages. When the game sends one, it
changes `<` and `>` in the values to `[` and `]`. On receipt, the client does
not do this check.

A player can type an `LMSG` message in the menu chat, and the chat server
passes it. For example, `LMSG {"t":"hello","c":"tr"}` shows "hello" in the red
team color. Type one space after `LMSG` and use straight double quotes.
Battle chat does not decode `LMSG` and shows the raw text. Battle chat does
show color tags (the game puts them in its own map-ping messages), but the
server changes `<` and `>` to `[` and `]` in player text. `{`, `}` and `"`
stay. [datamine; menu chat and battle chat tested live, October 2026]

#### Text color markup

The UI text boxes (`textarea`) read inline color tags:
`<color=@teamRedColor>...</color>` (a named UI color) or
`<color=#RRGGBB>...</color>` (any hex color). An `activeText` box does not
read them. The menu chat changes a typed `<` and `>` to `[` and `]` before it
sends (`validateChatMessage`), so a typed tag does not get through. The `LMSG`
`c` key takes only the four tags above. A JSON escape (`\u003c` for `<`,
`\u003e` for `>`) in an `LMSG` `t` value can possibly carry a hex color tag,
because the sender check sees only a literal `<`. [datamine, not tested live]

### Custom battle rooms (matching server)

A custom battle is a room on the matching server. The client talks to it with
`mrooms.*` calls (`matching/serviceNotifications/mroomsApi.nut`):
`create_room`, `get_room`, `join_room`, `leave_room`, `destroy_room`,
`set_attributes`, `set_member_attributes`, `set_password`, `set_ready_state`,
`kick_from_room`, `invite_player`, `start_session`, `fetch_rooms_digest2`.
Each call carries a `roomId` and a `public` (or `private`) table.

- `mrooms.set_attributes` changes the room's `public` table. The room owner
  sends it. The stock client sends its full settings table again, which
  includes `creator`.
- `mrooms.set_member_attributes` changes the sender's own member entry. The
  stock client sends its own `clanTag`, `country`, `team`, `spectator`,
  `state` and `ready`. The values come from the client, so a client can send
  any `clanTag`.

The server stores these values as the client sends them. A program that acts
as a client can set a `creator`, a `roomName` or a `clanTag` that the stock UI
cannot make. [datamine; community report, agrees with the live list]

#### Connection to the matching server

A community client for the matching server (C#, published on a cheat forum)
shows the protocol below. The items marked "binary" are also in the
2026-10-28 Linux client. The other items come only from that code and are not
tested.

- Transport: one TCP connection. Each message is JSON.
- Envelope: `{"data": {"name": "<api>", "data": {...}}, "id": N, "error": E,
  "type": T}`. `id` pairs a reply with its request. `type` 52 is an API call,
  64 is the login, and 24 closes the connection. A reply with an `error` value
  other than 0 failed.
- Compression: the JSON text gets a `0x1A` byte in front and is compressed
  with LZ4 (block format). The frame is a `0x01` byte, the frame length
  (int32), the length before compression (int32), then the LZ4 data.
- Encryption: AES-128-CBC with PKCS7 padding. The client makes a random
  session key. The IV is four int32 values: 0, then the length before
  compression three times. Each encrypted frame has a 16-byte header: the
  encrypted length, then that same IV value three times.
- Login (`type` 64, `id` 0): the client encrypts
  `{"chard_token", "session_key_evp"}` with the server's RSA-2048 public key
  (PKCS#1 v1.5) and sends it as `login`, with `auth_jwt`, `platform`,
  `protocol`, `version` (the game version as four 16-bit parts in one
  64-bit value), `user_id` and `name`. The field names and the public key are
  in the client binary. [binary]
- Error names: the client binary holds the full `SERVER_ERROR_*`,
  `CLIENT_ERROR_*` and `HOST_ERROR_*` list, from `OPERATION_COMPLETE` to
  `SERVER_ERROR_LOBBY_MATCH_STARTED`. The scripts import some of them from the
  native `matching.errors` module. [binary, datamine]
- API names: the scripts call `mrooms.*`, `match.*`, `mlogin.*`,
  `mpresence.*`, `hmanager.*` and `mrpc.*`. Server pushes have names like
  `mrooms.on_room_member_joined` and `mlogin.update_online_info` (which holds
  `rooms_total` and `players_total`). [datamine]
- Room data from `mrooms.get_room`: `public` (`creator`, `creatorId`,
  `players`, `hidden`, `mission`, `missionURL`, `chatPassword`, `room_key`,
  `sessionId`, `hasSession`), `private` (`blacklist`, `room_secret`), `size`,
  and `members` (`memberId`, `userId`, `name`, `public`, `private`). A member's
  `public.playerInfo` holds the server's record: `name`, `clanTag`, `clanId`,
  `country`, `rank`, `mrank`, `squad`, `team` and `crafts_info`.
- Room bans: `private.blacklist` is a list of user ids. The owner changes it
  with `mrooms.set_attributes`.
- Room id: the low 32 bits are a counter. The high 32 bits are seconds after
  2022-11-09 12:30:38 UTC (Unix time 1667997038), the room's creation time.
  One room id from October 2026 decodes to 2026-07-29, which is possible for a
  long-lived room. [not tested]

#### Host names in the room list

The room list ("Game Creator" column) shows `public.creator`, after
`getPlayerName`. The stock client sets it to the player's own name. The list
puts it in a `textareaNoTab` and escapes only quotes (`stripTags`), so markup
in it works:

- `<color=#RRGGBB>...</color>` gives a color. One tag on each character gives
  a gradient.
- `<b>...</b>` gives larger, bold text. The game's own texts do not use this
  tag. [community report; seen in the live list]
- A platform suffix changes to an icon: `@live` (Xbox) shows `⋇` (a gamepad
  glyph) on PC, `@psn` shows the PSN icon, `@steam` and `@epic` are removed
  (`user/nickTools.nut`, `user/remapNick.nut`).

The mission column shows `public.roomName` when it is set, and the stock
client never sets it. That column is an `activeText`, so it shows
symbol-font glyphs but no color markup.

#### Limits

The changes apply only to the room data. The host must own the room to change
`public`. In a normal battle, the player does not own the room, and the name
and the clan tag come from the server's player record. Battle chat also takes
the sender name from that record. So this procedure cannot change a player's
name in normal battles. [community report; agrees with the battle chat
routing above]

### Battle chat

- Modes: `CHAT_MODE_ALL`, `CHAT_MODE_TEAM`, `CHAT_MODE_SQUAD`,
  `CHAT_MODE_PRIVATE`. The scripts drop private messages in battle.
- A replay stores each chat message as packet type 3 (see
  [03-replays.md](03-replays.md)): sender name, text, channel
  (0 Team, 1 All, 2 Squad, 3 Direct), a local flag, a quick-message flag, and a
  complaints string. The packet has no user id and no team.
- The routing code sends a message as follows. [static analysis]
  - All: to all players.
  - Team: to each player with the same team id as the sender, and to each
    player with one flag bit set (probably spectators).
  - Squad: to the players in the sender's squad, and to the same flagged
    players.
  - Private: to one player id.
- The sender name in the packet comes from the server's player record (the
  player is found by id). A client does not supply its own sender name.
- Before the packet is built, each `<` in the text becomes `[` and each `>`
  becomes `]`. So a player cannot put UI markup (color, link) into the battle
  chat.
- A "fake" message is a local message that only the own client shows (for
  example the chat flood warning). The client does not send it to the server
  ("Can't send FAKE chat message to SERVER! Skipping message").
- The client looks up the sender only by name: `get_mplayer_by_name(sender)`.
  The sender's team color and the squad color come from that lookup.
- The routing code writes a log line in the form
  `[<UTC time>] <name>(<player id>) -> <ALL|TEAM|SQUAD|name>: <text>`.
- The local API at `127.0.0.1:8111/gamechat` gives the battle chat as
  `id`, `msg`, `sender`, `enemy`, `mode`, `time`
  (see [04-localhost-8111-api.md](04-localhost-8111-api.md)).

### Name privacy options

All three are in Options, "Privacy and Confidentiality" (feature
`PrivacySettings`).

| Option (UI text) | Id | Values | Gate |
|---|---|---|---|
| "Display real nick in battle and menu" | `display_my_real_nick` | on / off. Off: the server shows a generated name for you to the other players. Replays and server logs keep the real name. | Premium (the scripts reset it when premium ends) |
| "Display clan in battle and menu" | `display_my_real_clan` | on / off. Off: hides your squadron tag. | Premium (same reset) |
| "Hide player nicknames" (streamer mode) | `display_real_nicks_participants` | "Without changes" (0), "Display User ID" (1), "Change player nicknames" (2) | PC only. The scripts show no premium check; the native client reads the value. |

The client keeps a name map for each battle (`user/nameMapping.nut`). For
each player, `get_mplayers_list` gives `name` (the name to show) and
`realName`. The map keeps `fake -> real` and `real -> fake`, and both tables
use the name text as the key. `getPlayerName(n)` shows `getFakeName(n)` when
there is one, else the name. Replays show the real name in brackets after the
generated name.

### Known problems

- **Streamer-mode name clash in battle chat** [verified in a player's client
  replays, 2026-10]. Cause: "Hide player nicknames" set to "Change player
  nicknames".
  - With that value, the native client gives each other player a random bot
    name (format `coop/Bot%d`, 545 keys in `lang/missions_pilots.csv`). The
    client applies the names before it records, so its replays hold them too:
    in the footer (31 of 32 players, all but the recording player) and as the
    chat sender name. Replays from before the option was on had 0 bot names.
  - The names are random for each player, so two players often get the same
    name. With 16 players on each side and 545 names, chance gives a pair
    across the teams in about 37% of matches. The replays showed 9 of 29.
  - The server routes Team chat by team id. The client got 353 Team messages
    from names only on its own team, 5 from shared names, and 0 from names
    only on the enemy team.
  - But the client finds the sender only by name
    (`get_mplayer_by_name(sender)`). With a shared name it can pick the enemy.
    The teammate's message then shows in `[Team]` with the enemy sender color
    (red), as if the enemy wrote in team chat.
  - Fix for a player: set "Hide player nicknames" to "Without changes".
    "Display User ID" gives unique names, so it probably also avoids the
    clash (not tested).
  - A server-side generated name ("Display real nick" off) uses the same
    `coop/Bot<n>` keys (MPI `nickLocKey`). It can clash in the same way, but
    it is rare: 1 player in the replays checked.
- **Remote battle chat** [reported, not verified]. For a long time players
  could make an account post in a battle chat from outside the game client
  while that account was in a match. The method and the fix date are not
  known.
