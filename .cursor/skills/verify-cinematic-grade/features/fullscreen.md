# Keep fullscreen windows composited

While the grade is on and this switch is on, fullscreen windows stay inside the compositor so the shader can see them. The applet remembers the previous Muffin unredirect value and writes it back when the grade turns off, or when the switch turns off.

## Sub-features

- `fullscreen-hold` forces `org.cinnamon.muffin unredirect-fullscreen-windows` false while the grade is on and the switch is on, and records the previous boolean in `~/.config/iron-within/unredirect.json`.
- `fullscreen-restore` writes that boolean back and deletes the file when the grade turns off.
- `fullscreen-switch-off` releases the hold even if the grade stays on.

## How to get to it (user POV)

- Right-click the panel icon and choose `Configure...`.
- Use the switch labeled `Keep fullscreen windows composited while the grade is on`.

The person does not edit `unredirect.json` and does not open the Muffin settings for the normal path. Those two are the observable side effects.

## Driving it with control-grade

Preconditions:

- `control-grade doctor` printed `"ok": true`.
- `control-grade begin` has opened this run.
- The grade is off, `compositeFullscreen` is true, and `restoreFile` is null. Record `muffinUnredirect` from this off state and call that boolean `saved`.

- **Hold.** Run `control-grade cli on`. `observe` shows `status.active` true, `muffinUnredirect` false, and `restoreFile` equal to `{"value":true}` or `{"value":false}` matching `saved`.
- **Restore.** Run `control-grade cli off`. `status.active` is false, `restoreFile` is null, and `muffinUnredirect` equals `saved`.
- **Switch off while on.** Run `control-grade cli on`, then `control-grade composite off`. The grade stays on (`status.active` true, teal icon). `restoreFile` is null and `muffinUnredirect` equals `saved`.
- **Switch back on.** Run `control-grade composite on`. The hold returns: `muffinUnredirect` is false and `restoreFile.value` equals `saved`.
- **Leave the switch on.** Run `control-grade cli off`. `cleanup` also restores `compositeFullscreen` to the begin value.

## Gotchas

- Do not delete `unredirect.json` by hand while the grade is on. The next off would have nothing to restore.
- If `restoreFile` is already non-null while the grade is off, stop. A previous run or a shell crash left a hold. Do not overwrite it inside this recipe.
- The applet does not change the ICC profile, gamma, or colord. Do not look at those for this feature.
- A fullscreen window that was already unredirected may need a moment to come back under the compositor. The proof of this feature is the muffin key and the file, not a screenshot of a game.
