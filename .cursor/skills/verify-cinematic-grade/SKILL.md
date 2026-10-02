---
name: verify-cinematic-grade
description: Drive Cinematic Grade on the one Cinnamon desktop and prove the panel icon, the shortcut, and bin/cinematic-grade. Use when changing the applet, the grade session, the shaders, the presets, or the installer, and before calling desktop behavior done.
---

# Verify Cinematic Grade

Cinematic Grade is the Cinnamon panel applet `iron-within-panel@mateo`. One click, the configured shortcut, or `bin/cinematic-grade` turns a full-desktop color grade on or off. This skill drives that live session. It does not start a second desktop.

The shell extension `iron-within@mateo` stays disabled. The applet owns the grade.

## Launch

There is no per-run server. The applet lives inside the running Cinnamon session (`max-instances` is 1). Two drives of that session would toggle the same screen.

Install once, from the repo root:

```bash
./install.sh
```

That links `~/.local/share/cinnamon/applets/iron-within-panel@mateo` at this checkout and adds the applet to the panel. The grade stays off until a click, the shortcut, or `bin/cinematic-grade`.

If the icon is missing, or `control-grade doctor` says the shell has not loaded this checkout, press Alt+F2, type `r`, and press Enter. The applet then loads this checkout with the grade off. Turn it back on afterwards if it was on. Do not run `killall cinnamon` and do not call `RestartCinnamon` from a verification recipe.

Readiness is `control-grade doctor` exiting 0. Then `control-grade begin`. Recipes in `features/` assume that pair.

## Doctor

`control-grade doctor` is read-only. It exits 0 only when all of these are true:

- `DISPLAY` is set and the X screen size can be read.
- `org.Cinnamon.Eval` returns the panel applet, and no command holds the verify lock.
- `status.kind` is `applet`, `status.owner` is `applet`, `status.desktop` is `cinnamon`, and `status.session` is `x11`.
- `status.root` is this repo, `status.shaders` is true, `status.error` is null, and `status.workingSpace` is `encoded-framebuffer`.
- The tooltip starts with `Cinematic grade:`.
- The stage size times the scale factor matches the X screen.
- `org.cinnamon enabled-applets` contains `iron-within-panel@mateo`.
- `org.cinnamon enabled-extensions` does not contain `iron-within@mateo`.
- The XTest extension is available.

A missing `workingSpace` or a Spanish tooltip means the shell is still running an older applet. Stop. Reload with Alt+F2 `r`, then run doctor again.

Doctor prints one JSON object. `"ok": false` lists `failures`. `"runOpen": true` means `begin` was already called. That is not a doctor failure. A second `begin` is refused.

## Drive

The harness is `.cursor/skills/verify-cinematic-grade/scripts/control-grade`. Run it from any directory. Mutating commands refuse to start unless `begin` opened this run, and they refuse to run beside another `control-grade` process.

User entry points:

- Left click on the panel icon from `panel/icon.png` (the hooded mark). The tooltip is the state. On, the icon file is `panel/icon-active.png` and the icon style is `color: #3da9a0;`.
- The shortcut stored on the applet. The default is `<Super>g`. An empty value turns the shortcut off. The click and the CLI still work.
- Right click, then `Configure...`. That opens `xlet-settings` for this instance. Labels come from `panel/settings-schema.json`: `Preset`, `Intensity`, `Shortcut to toggle the grade`, `Keep fullscreen windows composited while the grade is on`.
- `bin/cinematic-grade on|off|toggle|status`.

`control-grade click` moves the pointer to the center of the applet actor and sends button 1, then puts the pointer back. It refuses when the actor is unmapped, tiny, huge, or not within 80 pixels of a screen edge.

`control-grade shortcut` sends the first binding in `status.shortcut` (`::` separates extras). It does not invent a key if the binding is empty.

`control-grade cli on|off|toggle|status` runs `bin/cinematic-grade` and prints that program's stdout.

`control-grade preset`, `intensity`, and `composite` write `~/.config/cinnamon/spices/iron-within-panel@mateo/iron-within-panel@mateo.json` and call `org.Cinnamon.updateSetting`. That is the path Configure uses. Names are `subtle`, `cinematic`, `iron_within`, and `extreme`. Intensity is a number from 0 to 1. `composite on` is the fullscreen switch. Calling `settings.setValue` from inside the applet stores the value without moving the running grade, because the reload then sees no change. Do not use that as the drive.

`control-grade observe` prints the status object plus `tooltip`, `iconStyle`, actor geometry, `compositeFullscreen`, `muffinUnredirect` (`org.cinnamon.muffin unredirect-fullscreen-windows`), and `restoreFile` (`~/.config/iron-within/unredirect.json`, or null).

Recipes and expected states are in `features/`. Start each recipe from the grade off, with the preset and intensity `begin` recorded, unless that recipe says otherwise. `cleanup` puts those settings back.

## Evidence

Write proof under `.cursor/skills/verify-cinematic-grade/artifacts/<feature>/`. Cleanup must leave that directory in place.

For a toggle proof, keep the `observe` JSON from the off state and the on state, a PNG of the icon actor in both states, and a PNG of the verification swatch in both states. Record the command, the exit code, and the asserted fields in `proof.txt`.

The swatch is scaffolding, not a product window. `control-grade swatch open` shows a 220x220 undecorated window titled `cinematic-grade-swatch`, filled with `#c0392b`, centered on the screen. `swatch shot` captures its interior. `swatch close` closes it. `chroma <png>` prints the mean chroma of the center half (max channel minus min channel).

Proof standards:

- Drive the icon, the shortcut, and `bin/cinematic-grade`. Do not call `setActive` from a private eval and count that as the click.
- Capture the action and the next `observe`, not only the last picture.
- A passing `status.active` is not enough. The tooltip, the icon style, and `effects` / `passes` have to move with it.
- An X screenshot may or may not include the Muffin shader. One session saved identical swatches (chroma 149 both times) and a gray icon crop. A later session, after the hooded icon, saved a flat red swatch off (chroma 149) and a desaturated grainy swatch on (chroma 0). Assert `iconStyle`, the tooltip, `effects`, and `passes`. Keep the shots. Do not fail the toggle because the swatch chroma stayed high or fell.
- Side effect of the fullscreen switch, when it is on: turning the grade on writes `unredirect.json` and forces the muffin key false. Turning the grade off deletes the file and writes the saved boolean back. Read the key with `observe`. Do not trust the switch name alone.
- Intensity 0 leaves the grade active and the icon teal. The settings copy says 0 is the original image. Do not treat a teal icon as proof that the pixels changed.
- Do not screenshot the whole desktop. The icon crop and the swatch are the pictures.

## Cleanup

`control-grade cleanup` restores the preset, intensity, fullscreen switch, and active flag recorded by `begin`, in that order. It closes the swatch and the `xlet-settings` process this run opened. It releases the run. It does not delete `artifacts/`. It does not kill Cinnamon, and it does not kill by process name.

If `begin` was not called, cleanup exits 0 and prints that there is no open run.

If the shell was reloaded before `begin`, the snapshot says the grade is off. Put back a grade that was on before the reload with:

```bash
bin/cinematic-grade on
```

## Helpers

```bash
.cursor/skills/verify-cinematic-grade/scripts/control-grade doctor
.cursor/skills/verify-cinematic-grade/scripts/control-grade begin
.cursor/skills/verify-cinematic-grade/scripts/control-grade observe
.cursor/skills/verify-cinematic-grade/scripts/control-grade click
.cursor/skills/verify-cinematic-grade/scripts/control-grade shortcut
.cursor/skills/verify-cinematic-grade/scripts/control-grade cli status
.cursor/skills/verify-cinematic-grade/scripts/control-grade shot artifacts/toggle/icon-off.png
.cursor/skills/verify-cinematic-grade/scripts/control-grade swatch open
.cursor/skills/verify-cinematic-grade/scripts/control-grade swatch shot artifacts/toggle/swatch-off.png
.cursor/skills/verify-cinematic-grade/scripts/control-grade chroma artifacts/toggle/swatch-off.png
.cursor/skills/verify-cinematic-grade/scripts/control-grade preset iron_within
.cursor/skills/verify-cinematic-grade/scripts/control-grade intensity 1
.cursor/skills/verify-cinematic-grade/scripts/control-grade composite on
.cursor/skills/verify-cinematic-grade/scripts/control-grade configure
.cursor/skills/verify-cinematic-grade/scripts/control-grade cleanup
```

The script uses `/usr/bin/python3` because it needs GTK, Gdk, and Xlib. The project `.venv` does not have `gi`.

`observe`, `click`, `shortcut`, `preset`, `intensity`, and `composite` print one JSON object on stdout. `cli` prints the `bin/cinematic-grade` stdout. `doctor` prints `{"ok": true|false, ...}`.

Keep the map honest with `/maintain-verification-skill` when the applet's user-facing behavior changes. A cadence is optional.
