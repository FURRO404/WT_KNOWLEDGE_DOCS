# 10 — Tooling and repository index

This section lists the public repositories that hold War Thunder (WT) work. Each
row says what the repository does, its language, and where to read more.

## Format and datamine tools

| Repository | Language | Purpose | Section |
|---|---|---|---|
| [wt-tools](https://github.com/klensy/wt-tools) | Python | Unpack vromfs, decode BLK/DataBlock, dxp, clog | [02](02-file-formats.md) |
| [War-Thunder-Datamine](https://github.com/gszabi99/War-Thunder-Datamine) | data | The unpacked game files, one folder per vromfs | [02](02-file-formats.md) |
| [Dagor-Asset-Explorer](https://github.com/quentin-dh/Dagor-Asset-Explorer) | Python | Export Dagor models, skeletons, map props | [02](02-file-formats.md) |
| [DagorEngine](https://github.com/GaijinEntertainment/DagorEngine) | C++ | The open engine source, for reference | [02](02-file-formats.md) |

## Replay, map, and stats tools

| Repository | Language | Purpose | Section |
|---|---|---|---|
| [WrplReplayParser](https://github.com/LivingTheDagor/WrplReplayParser) | C++ | `.wrpl` parser with Python bindings | [03](03-replays.md) |
| [wrpl-inspector](https://github.com/maxsupermanhd/wrpl-inspector) | Go | `.wrpl` library and GUI | [03](03-replays.md) |
| [wt-heatmaps](https://github.com/maxsupermanhd/wt-heatmaps) | Go | Kill heatmaps and the `coordencode` codec | [09](09-heatmaps-and-coordinates.md) |
| [WtMiniMapPictures](https://github.com/LivingTheDagor/WtMiniMapPictures) | images | Minimap image set | [07](07-terrain-and-maps.md) |

## External community tools (public)

These public repositories back facts in this bank. They are the recommended
external references.

| Repository | Language | Purpose | Section |
|---|---|---|---|
| [wt_ext_cli](https://github.com/Warthunder-Open-Source-Foundation/wt_ext_cli) | Rust | Fast VROMFS and BLK unpacker (CLI) | [02](02-file-formats.md) |
| [wt_blk](https://github.com/Warthunder-Open-Source-Foundation/wt_blk) | Rust | VROMFS, BLK, DXP/GRP format library | [02](02-file-formats.md) |
| [wt_datamine_extractor](https://github.com/Warthunder-Open-Source-Foundation/wt_datamine_extractor) | Rust | Structured game data from the datamine | [02](02-file-formats.md) |
| [wt_csv](https://github.com/Warthunder-Open-Source-Foundation/wt_csv) | Rust | Parser for WT `.csv` lang files | [02](02-file-formats.md) |
| [wt_version](https://github.com/Warthunder-Open-Source-Foundation/wt_version) | Rust | Parse the 4-part game version | [02](02-file-formats.md) |
| [wt_dm_api](https://github.com/Warthunder-Open-Source-Foundation/wt_dm_api) | Rust | HTTP server that serves datamine BLK files | [02](02-file-formats.md) |
| [WtFileUtils](https://github.com/LivingTheDagor/WtFileUtils) | Python | Reference VROMFS and BLK reader | [02](02-file-formats.md) |
| [wt_ballistics_calc](https://github.com/Warthunder-Open-Source-Foundation/wt_ballistics_calc) | Rust | Missile flight simulator | [06](06-ballistics-and-armor.md) |
| [wt_sensor](https://github.com/Warthunder-Open-Source-Foundation/wt_sensor) | Rust | Radar and IRST BLK definitions | [03](03-replays.md) |

The `Warthunder-Open-Source-Foundation` (WOSF) organization is the upstream of
the format reverse-engineering. See https://github.com/Warthunder-Open-Source-Foundation.

## Websites and live tools

These public websites use the knowledge in this bank. They serve heatmaps and
match statistics.

| Site | Purpose |
|---|---|
| https://thunder.nanachi.party/ | Heatmaps and statistics |
| https://sre.pawjob.us/ | Squadron Battles (SRE) statistics |
| https://tss.pawjob.us/ | Tournament (TSS) statistics |
| https://lt4.pawjob.us/ | Random Battles statistics and heatmaps |
| https://statshark.net/ | Player and match statistics |
| https://www.thunderstack.net/ | A large collection of WT tools. Many are out of date. |

## Notes and status

- `wt-tools` last changed in 2021. Its format decoders still match the current
  files, because the BLK and vromfs formats did not change. See
  [02-file-formats.md](02-file-formats.md).
- `War-Thunder-Datamine` tracks the game version, at 2.58.0.24 at the time of
  this document.

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
- The notes below on minimizing come from the X11 mode.
- The client minimizes its own window when it loses focus. It does this in both
  the Fullscreen and the Windowed display modes. The binary imports
  `XIconifyWindow`, and no in-game setting turns this off.
- The client also stops rendering while it is unfocused, in both X11 and
  Wayland mode. In X11 mode, a KWin rule that
  forces "Minimized" to No keeps the window on screen, but the window shows a
  frozen frame. To keep it drawing, run the game nested inside gamescope. The
  game then keeps focus inside gamescope all the time.
- The Linux launcher (`launcher`, a sciter/GTK program) starts the game with
  glib's `g_spawn_async`. Its update settings define the command line: on Linux
  it is `linux64/aces -forcestart -add_file_to_report "<launcher log path>"`,
  run from the game folder.
- The launcher hides the "Fullscreen (windowed)" display mode on Linux. It
  offers only Fullscreen and Windowed there, and the default is Fullscreen.
- Launcher command-line flags found in the binary include `-justupdate`,
  `-appid`, `-localversion`, `--silent`, `--lang` and `--log`.
