/* Parse the project JavaScript without executing it. */

const ByteArray = imports.byteArray;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;

let root = GLib.get_current_dir();
let files = [
    "gradeLogic.js",
    "gradeEngine.js",
    "extension.js",
    "panel/applet.js",
    "tests/grade_logic_test.js"
];

for (let i = 0; i < files.length; i++) {
    let path = root + "/" + files[i];
    let file = Gio.File.new_for_path(path);
    let [, contents] = file.load_contents(null);
    let text = ByteArray.toString(contents);
    try {
        new Function(text);
    } catch (e) {
        printerr("SYNTAX " + files[i] + ": " + e);
        imports.system.exit(1);
    }
}
print("syntax_check ok");
