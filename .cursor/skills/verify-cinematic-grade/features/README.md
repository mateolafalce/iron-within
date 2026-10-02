# Cinematic Grade verification map

This directory is the maintained source for verifying the user-facing behavior of Cinematic Grade. Read the index before driving the desktop, then use the matching feature file as the recipe.

## Baseline preconditions

- The panel applet `iron-within-panel@mateo` is on the one Cinnamon session, linked at this checkout.
- The shell extension `iron-within@mateo` is not enabled.
- `DISPLAY` is the session the person is using. There is no second Cinnamon, no Xephyr, and no private grade.
- Run `.cursor/skills/verify-cinematic-grade/scripts/control-grade doctor` and require `"ok": true`.
- Run `control-grade begin` once. A second begin is a refusal, not a parallel run.
- Recipes start with the grade off and with the preset, intensity, and fullscreen switch that `begin` saved, unless a step says otherwise.
- `control-grade cleanup` restores that snapshot. It does not delete `artifacts/`.

## Driving conventions

- Treat every command as literal. Keep flags and preset names unchanged.
- Read state with `control-grade observe`. Do not parse a private eval as the proof.
- The click path is `control-grade click`. The shortcut path is `control-grade shortcut`. The terminal path is `control-grade cli`.
- Settings paths are `control-grade preset`, `intensity`, `composite`, and `configure`.
- Pictures are an icon crop or the swatch window, never the whole desktop.
- Record the feature id and the entry point next to every artifact.
- Report an unreachable entry point with the command and the unmet precondition. Do not mark it verified through a different entry point.

## Proof and skip reporting

- Capture the command and the following `observe` JSON.
- UI proof is the tooltip, the icon style, `effects`, and `passes`. Icon and swatch PNGs are kept. On this session an X screenshot does not show the shader, so chroma is not the proof.
- CLI proof is the `bin/cinematic-grade` stdout and exit code, then `observe`.
- Fullscreen proof is `muffinUnredirect` and `restoreFile` before and after the grade changes.
- Leave proof under `.cursor/skills/verify-cinematic-grade/artifacts/<feature>/`.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with control-grade` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

## Features

- [Turn the grade on and off](./toggle.md) covers the panel click, the shortcut, the `cinematic-grade` command, the icon, and the fullscreen-compositing hold.
- [Choose a preset](./preset.md) covers Configure and the four preset names.
- [Set intensity](./intensity.md) covers the intensity scale, including 0 and 1.
- [Keep fullscreen windows composited](./fullscreen.md) covers the muffin unredirect hold and its restore.
