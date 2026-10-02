# Turn the grade on and off

The panel icon, the shortcut, and `bin/cinematic-grade` each turn the desktop grade on or off. On, the icon is `panel/icon-active.png`, the icon style is `color: #3da9a0;`, and the tooltip names the preset. Off, the icon is `panel/icon.png`, the style is empty, and the tooltip says the grade is off.

## Sub-features

- `toggle-click` turns the grade on and off from a left click on the panel icon.
- `toggle-shortcut` does the same with the first configured binding.
- `toggle-cli` does the same with `on`, `off`, and `toggle`.
- `toggle-icon` shows a teal icon and an "on" tooltip only while the grade is on.
- `toggle-hold` writes the fullscreen-compositing hold while the grade is on and removes it when the grade turns off.

## How to get to it (user POV)

- Left-click the hooded panel icon. The tooltip reads `Cinematic grade: off. Click to turn the grade on.` or `Cinematic grade: on (<preset>). Click to turn the grade off.`
- Press the shortcut. The default binding is Super+G (`<Super>g`).
- Run `bin/cinematic-grade on`, `off`, `toggle`, or `status`.

## Driving it with control-grade

Preconditions:

- `control-grade doctor` printed `"ok": true`.
- `control-grade begin` has opened this run.
- `control-grade observe` shows `status.active` false, `status.error` null, `status.preset` `iron_within`, `status.intensity` 1, `compositeFullscreen` true, and `restoreFile` null. If the grade is on, run `control-grade cli off` before the first proof step.
- `status.shortcut` is `<Super>g`. If it is empty, skip `toggle-shortcut` and report it. Do not send a different key.

- **Icon off.** Read the idle state. Run `control-grade observe`. `status.active` is false, `status.effects` is 0, `status.passes` is 0, `tooltip` is `Cinematic grade: off. Click to turn the grade on.`, and `iconStyle` is empty.
- **Capture the off icon.** Run `control-grade shot .cursor/skills/verify-cinematic-grade/artifacts/toggle/icon-off.png`. The PNG is only the applet actor.
- **Open the swatch.** Run `control-grade swatch open`, then `control-grade swatch shot .cursor/skills/verify-cinematic-grade/artifacts/toggle/swatch-off.png`, then `control-grade chroma .cursor/skills/verify-cinematic-grade/artifacts/toggle/swatch-off.png`. Record the chroma. This capture does not prove the grade. See Gotchas.
- **Click on.** Left-click the icon. Run `control-grade click`. `status.active` is true, `tooltip` is `Cinematic grade: on (iron_within). Click to turn the grade off.`, `iconStyle` is `color: #3da9a0;`, `status.effects` is 3, and `status.passes` is 3. `muffinUnredirect` is false. `restoreFile` is `{"value":false}` when the off-state muffin value was false, or `{"value":true}` when that value was true. Save this object as `artifacts/toggle/after-click.json`.
- **Capture the on icon and swatch.** Run `control-grade shot .cursor/skills/verify-cinematic-grade/artifacts/toggle/icon-on.png`, `control-grade swatch shot .cursor/skills/verify-cinematic-grade/artifacts/toggle/swatch-on.png`, and `control-grade chroma .cursor/skills/verify-cinematic-grade/artifacts/toggle/swatch-on.png`. The assertion that the grade is on is the tooltip, `iconStyle`, `effects`, and `passes`. The swatch chroma is not the assertion. It may stay high, or it may fall when the capture includes the shader.
- **Click off.** Run `control-grade click`. `status.active` is false, the off tooltip is back, `iconStyle` is empty, `effects` and `passes` are 0, `restoreFile` is null, and `muffinUnredirect` is the boolean recorded while off.
- **Shortcut on.** Press the binding. Run `control-grade shortcut`. The on tooltip, teal style, `effects` 3, and `passes` 3 return. Stdout includes `"sent": "<Super>g"`.
- **Shortcut off.** Run `control-grade shortcut` again. The grade is off and `restoreFile` is null.
- **CLI on.** Run `control-grade cli on`. Exit code 0. Stdout contains `"active":true`. `control-grade observe` matches the on state above.
- **CLI status.** Run `control-grade cli status`. Exit code 0. Stdout contains `"active":true` and `"preset":"iron_within"`.
- **CLI off.** Run `control-grade cli off`. Exit code 0. Stdout contains `"active":false`. `observe` is the off state and `restoreFile` is null.
- **CLI toggle.** Run `control-grade cli toggle`. The grade turns on. Run it again. The grade turns off and `restoreFile` is null.
- **Proof.** Keep `artifacts/toggle/icon-off.png`, `icon-on.png`, `swatch-off.png`, `swatch-on.png`, `after-click.json`, and `proof.txt` (the commands, exit codes, chroma numbers, and the on/off fields).

## Gotchas

- `iron_within` uses no sharpen, so a mounted grade is 3 effects and 3 passes (one grade pass on each of the three actors). A preset with sharpen above 0 is 6 and 6. Do not assert 3 after changing preset.
- The X capture sometimes includes the Muffin shader and sometimes does not. One run saved two red swatches, both chroma 149, and a gray icon crop. The run after the hooded icon landed saw the shader: swatch off was flat red (chroma 149) and swatch on was desaturated grain (chroma 0). The icon actor crop stayed gray even though `icon-active.png` is teal, because `iron_within` saturation is 0 and the capture of that actor was gray. Assert the tooltip, `iconStyle`, `effects`, and `passes`. Do not fail the toggle because the swatch chroma stayed high or fell. Fail it when those four stay put.
- Grain is on for `iron_within`. A capture that someday includes the shader will not match pixel for pixel between two "on" shots.
- The hardware cursor is not graded. Do not use the cursor as the swatch.
- `control-grade click` refuses an actor that is not on a screen edge. Do not fall back to a coordinate in the middle of the screen.
- A shortcut that another grab already owns can eat Super+G. If `shortcut` exits 0 but `active` does not flip, report `toggle-shortcut` as failed. Do not count the click as the shortcut.
- `bin/cinematic-grade` also talks to the shell extension when that extension is loaded. Doctor fails while `iron-within@mateo` is enabled, because the applet would no longer be the only client.
- The swatch is verification scaffolding. `cleanup` closes it. A missing swatch means the chroma proof did not run.
