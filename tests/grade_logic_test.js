/* Contract tests for gradeLogic.js. Run from the repo root:
 *   cjs tests/grade_logic_test.js
 */

const ByteArray = imports.byteArray;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;

imports.searchPath.unshift(GLib.get_current_dir());
const Logic = imports.gradeLogic.GradeLogic;

let failures = 0;

function check(label, condition) {
    if (condition)
        return;
    failures += 1;
    printerr("FAIL " + label);
}

function readText(path) {
    let file = Gio.File.new_for_path(path);
    let [, contents] = file.load_contents(null);
    return ByteArray.toString(contents);
}

function presetOptions(schemaPath) {
    let schema = JSON.parse(readText(schemaPath));
    let options = schema.preset.options;
    let values = [];
    for (let label in options)
        values.push(options[label]);
    values.sort();
    return values;
}

let root = GLib.get_current_dir();
let presetsText = readText(root + "/presets.json");
let accepted = Logic.acceptPresetText(presetsText, null);
check("presets.json is accepted", accepted.ok);
check("rejected text keeps the previous map", (function() {
    let bad = Logic.acceptPresetText("{", accepted.presets);
    return !bad.ok && bad.presets === accepted.presets;
})());
check("a missing key rejects the whole file", (function() {
    let parsed = JSON.parse(presetsText);
    delete parsed.subtle.grain;
    let bad = Logic.acceptPresetText(JSON.stringify(parsed), accepted.presets);
    return !bad.ok && bad.presets === accepted.presets && bad.error.indexOf("subtle.grain") !== -1;
})());
check("non-object presets.json is rejected", !Logic.acceptPresetText("[1]", null).ok);

let names = Logic.SCHEMA_PRESETS.slice().sort();
check("applet schema lists the same presets", presetOptions(root + "/panel/settings-schema.json").join() === names.join());
check("extension schema lists the same presets", presetOptions(root + "/settings-schema.json").join() === names.join());

check("intensity clamps", Logic.clampIntensity(-1) === 0 && Logic.clampIntensity(2) === 1 && Logic.clampIntensity("nope") === 1);
check("sharpen gate", Logic.sharpenWanted({ sharpen: 0.2 }, 1) && !Logic.sharpenWanted({ sharpen: 0.2 }, 0));
check("normalize fills only finite numbers", Logic.normalizePreset({ exposure: "x" }).exposure === Logic.FALLBACK_PRESET.exposure);

let holdOn = Logic.unredirectTransition(null, true, true, true);
check("hold records the original true value and forces compositing",
    holdOn.writeFile && holdOn.writeFile.value === true && holdOn.setMuffin === false && !holdOn.deleteFile);
let holdAlreadyOff = Logic.unredirectTransition(null, false, true, true);
check("hold records an original false without rewriting the key",
    holdAlreadyOff.writeFile && holdAlreadyOff.writeFile.value === false && holdAlreadyOff.setMuffin === null);
let holdAgain = Logic.unredirectTransition({ value: true }, false, true, true);
check("a second hold keeps the original file and forces compositing",
    holdAgain.writeFile === null && holdAgain.setMuffin === false && !holdAgain.deleteFile);
let release = Logic.unredirectTransition({ value: true }, false, true, false);
check("grade off restores the original value and deletes the file",
    release.deleteFile && release.setMuffin === true && release.writeFile === null);
let releaseCompositeOff = Logic.unredirectTransition({ value: false }, false, false, true);
check("composite option off releases the hold",
    releaseCompositeOff.deleteFile && releaseCompositeOff.setMuffin === false);
let idle = Logic.unredirectTransition(null, true, true, false);
check("idle with no file does not touch muffin",
    idle.writeFile === null && idle.setMuffin === null && !idle.deleteFile);

check("restore payload roundtrip",
    Logic.readUnredirectPayload(Logic.unredirectPayload(true)).value === true &&
    Logic.readUnredirectPayload(Logic.unredirectPayload(false)).value === false &&
    Logic.unredirectPayload(true) === '{"value":true}');
let badPayload = false;
try {
    badPayload = Logic.readUnredirectPayload('{"value":1}') === null;
} catch (e) {
    badPayload = false;
}
check("non-boolean restore payload is refused", badPayload);

let stamp = String(GLib.get_monotonic_time());
let tmp = Gio.File.new_for_path(GLib.get_tmp_dir()).get_child("iron-within-root-" + stamp);
tmp.make_directory(null);
let shaders = tmp.get_child("shaders");
shaders.make_directory(null);
shaders.get_child("grade.glsl").replace_contents("ok", null, false, Gio.FileCreateFlags.NONE, null);
let panel = tmp.get_child("panel");
panel.make_directory(null);
let linkParent = Gio.File.new_for_path(GLib.get_tmp_dir());
let link = linkParent.get_child("iron-within-panel-link-" + stamp);
link.make_symbolic_link(panel.get_path(), null);
check("applet symlink resolves to the project root", Logic.resolveProjectRoot(link.get_path()) === tmp.get_path());
check("project root resolves to itself", Logic.resolveProjectRoot(tmp.get_path()) === tmp.get_path());
check("this repo resolves to itself", Logic.resolveProjectRoot(root) === root);
link.delete(null);
shaders.get_child("grade.glsl").delete(null);
shaders.delete(null);
panel.delete(null);
tmp.delete(null);

if (failures) {
    printerr(failures + " failed");
    imports.system.exit(1);
}
print("grade_logic_test ok");
