# 11 — Misc information

This chapter holds notes that fit no other chapter. At this time it covers how
the game client and its launcher behave on the desktop: windows, focus, audio,
start-up arguments and Steam detection.

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
