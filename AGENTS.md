# AGENTS.md

Instructions for agents working in this repository.

## What this is

Cinematic Grade is a real-time color grade and sharpen for the whole Cinnamon desktop. The compositor is Muffin. The filter is a pair of GLSL 1.20 shaders on Clutter actors. It does not change the monitor ICC profile, gamma ramps, or colord.

Normal use is the panel applet `iron-within-panel@mateo`. One click, Super+G, or `bin/cinematic-grade` toggles the grade. The grade starts off.

The shell extension `iron-within@mateo` is a second entry point. `install.sh` links it and leaves it disabled. When the applet is on the panel, the applet owns the single grade session in `gradeEngine.js`. Do not mount a second copy.

`panel/gradeEngine.js` and `panel/gradeLogic.js` are symlinks to the copies at the repo root. Edit the root files.

## Commands

From the repo root:

```bash
./tests/run.sh
```

That script creates `.venv` when it is missing. It runs the JavaScript logic tests with `cjs`, then the shader pixel tests with `.venv/bin/python`. Use `.venv/bin/python` and `.venv/bin/pip` for Python in this repo. `control-grade` is the exception: it runs on `/usr/bin/python3` because it needs GTK and Xlib, which the venv does not have.

```bash
./install.sh
./uninstall.sh
bin/cinematic-grade on
bin/cinematic-grade off
bin/cinematic-grade toggle
bin/cinematic-grade status
```

There is no npm package and no pip manifest. Dependabot only covers GitHub Actions pins, and only when workflow files exist.

## Desktop checks

Changes to the applet, the grade session, the shaders, the presets, or the installer need the live check in `.cursor/skills/verify-cinematic-grade/SKILL.md`. Drive the one running Cinnamon session. Do not start a second desktop, do not run `killall cinnamon`, and do not call `RestartCinnamon` from a verification recipe.

Proof files under `.cursor/skills/verify-cinematic-grade/artifacts/` are session output. `demo/` is local capture output. Do not commit either.

## Invariants

The contract in `README.md` is the source of truth. A change is most likely to break these rules:

- One session, on `global`. The applet wins when both entry points are loaded.
- Mount is all or nothing on `Main.uiGroup`, `global.bottom_window_group`, and `global.top_window_group`. A shader failure removes every effect.
- The math runs on the encoded framebuffer. Identity settings leave an opaque pixel unchanged. Do not convert that math to linear light.
- `presets.json` must contain `subtle`, `cinematic`, `iron_within`, and `extreme`. Every key in `GradeLogic.PRESET_KEYS` must be a finite number. A bad save keeps the previous presets.
- A `shaders/*.glsl` edit is compiled on a throwaway effect. Replace the running shader only when that compile succeeds.
- While the grade is on and fullscreen compositing is requested, save `org.cinnamon.muffin unredirect-fullscreen-windows` to `~/.config/iron-within/unredirect.json` before setting the key to false. Restore that value when the grade turns off, on the next start after a crash, and in `uninstall.sh`.
- The applet does not store the on state. Each session starts with the grade off.

## Commits

Every commit uses [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

```
<type>(<optional-scope>): <summary>

<optional body>

Co-authored-by: Michael <265398295+lafalce-assistant@users.noreply.github.com>
```

- `type` is one of `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Add a scope only when it names a real area, for example `feat(shader):` or `fix(applet):`. Write the scope in lowercase.
- Write the summary in English, in the imperative, starting with a lowercase letter. No trailing period. Keep it within 72 characters.
- Add a body when the summary does not say why the change exists. Separate the body from the summary with one blank line.
- The last line is the `Co-authored-by` trailer above, and a blank line comes before it. Do not add `Co-authored-by: Claude`, `Generated with Claude Code`, or any variant.
- Put one logical change in each commit.
- Do not commit secrets, `.venv/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, verification artifacts, or `demo/`.

| Type | Use |
| --- | --- |
| feat | User-facing grade, control, or preset behavior |
| fix | A repair to that behavior |
| docs | README, license text, or this guide |
| test | `tests/` or the shader reference |
| ci | GitHub Actions or Dependabot |
| chore | Tooling, ignore rules, and the desktop verification skill |
| refactor | A structure change that keeps the grade the same |
| perf | Fewer passes, or less work per frame |
| style | Formatting only, with no behavior change |
| build | Install scripts or packaging |
| revert | A revert of an earlier commit |

```
feat: add the cinematic grade for the cinnamon desktop

fix(unredirect): restore the muffin key after a shell crash

docs: add the MIT license

ci: add dependabot updates for github actions

chore: ignore cinematic grade verification artifacts
```
