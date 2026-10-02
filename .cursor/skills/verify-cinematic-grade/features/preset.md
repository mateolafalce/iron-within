# Choose a preset

The preset picks which grade the desktop uses. The four names are Subtle, Cinematic, Iron Within, and Extreme. Changing it while the grade is on updates the picture and the tooltip. Changing it while the grade is off waits until the next on.

## Sub-features

- `preset-configure` opens the applet settings from the panel menu.
- `preset-choose` stores one of `subtle`, `cinematic`, `iron_within`, or `extreme`.
- `preset-live` shows the new name in the tooltip while the grade is on.

## How to get to it (user POV)

- Right-click the panel icon and choose `Configure...`.
- In that window, change the combobox labeled `Preset`. The visible options are `Subtle`, `Cinematic`, `Iron Within`, and `Extreme`.

## Driving it with control-grade

Preconditions:

- `control-grade doctor` printed `"ok": true`.
- `control-grade begin` has opened this run.
- The grade is off. `status.preset` is the value `begin` saved (this checkout's panel default is `iron_within`).

- **Open settings.** Right-click the icon and choose `Configure...`. Run `control-grade configure`. A process named `xlet-settings` is running for `iron-within-panel@mateo` and this applet's instance id. The window has a combobox labeled `Preset`.
- **Choose Subtle.** Choose `Subtle` in that combobox. Run `control-grade preset subtle`. `observe` shows `status.preset` `subtle` and `presetSetting` `subtle`. `status.active` is still false. The tooltip is still the off sentence.
- **See it live.** Turn the grade on with `control-grade cli on`. The tooltip is `Cinematic grade: on (subtle). Click to turn the grade off.` `effects` is 6 and `passes` is 6, because the `subtle` preset's sharpen is above 0.
- **Choose Iron Within.** Run `control-grade preset iron_within`. The tooltip is `Cinematic grade: on (iron_within). Click to turn the grade off.` `effects` is 3 and `passes` is 3.
- **Close settings.** `control-grade cleanup` closes the `xlet-settings` process this run started and restores the saved preset. Do not leave `subtle` selected.

## Gotchas

- `control-grade preset` writes the settings file and calls `org.Cinnamon.updateSetting`, which is what Configure does after it saves. `settings.setValue` from inside the applet does not move the running grade. The menu path still has to open with `control-grade configure` when the proof claims the settings window.
- The instance id is not stable across a reinstall. `configure` reads it from the loaded applet. Do not hardcode `26`.
- A preset name outside the four values is rejected by the harness. The running grade keeps the previous preset if `presets.json` itself is invalid. That file is not this feature.
- `cleanup` restores the begin preset. A proof that stops before cleanup leaves the desktop on the last chosen preset.
