# Set intensity

Intensity scales the selected preset. 0 keeps the original image. 1 applies the full preset. The icon still turns teal whenever the grade is on, including at 0.

## Sub-features

- `intensity-full` stores 1 and applies the full preset while the grade is on.
- `intensity-zero` stores 0. The grade stays on, the icon stays teal, and the picture is the original image.
- `intensity-configure` is the same scale in the Configure window.

## How to get to it (user POV)

- Right-click the panel icon and choose `Configure...`.
- Move the scale labeled `Intensity`. The tooltip on that scale says 0 is the original image and 1 is the full preset.

## Driving it with control-grade

Preconditions:

- `control-grade doctor` printed `"ok": true`.
- `control-grade begin` has opened this run.
- The grade is off and `status.preset` is `iron_within`.
- `begin` saved intensity 1.

- **Open settings.** Run `control-grade configure`. The window shows the `Intensity` scale.
- **Set zero while off.** Run `control-grade intensity 0`. `status.intensity` is 0 and `status.active` is false.
- **Turn on at zero.** Run `control-grade cli on`. `status.active` is true, `status.intensity` is 0, `iconStyle` is `color: #3da9a0;`, and the tooltip is `Cinematic grade: on (iron_within). Click to turn the grade off.`
- **Set full.** Run `control-grade intensity 1`. `status.intensity` is 1, `active` stays true, and `iconStyle` stays `color: #3da9a0;`.
- **Restore.** Run `control-grade cli off`. `cleanup` restores intensity 1 if a later step does not.

## Gotchas

- X screenshots do not show the shader, so chroma cannot prove intensity 0 against intensity 1. Assert `status.intensity` and that the icon style stays teal while the grade is on.
- With `iron_within`, sharpen is already 0, so `effects` and `passes` stay 3 at intensity 0 and at 1. A preset whose sharpen is above 0, such as `subtle`, drops from 6 passes to 3 at intensity 0. The icon stays teal either way.
- The scale step in the schema is 0.05. The harness accepts any number from 0 to 1 and stores a whole number when the value is whole. Assert `status.intensity`, not the text in the scale widget.
