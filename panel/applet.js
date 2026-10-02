/* Panel icon. Click toggles the grade, same gesture as Desaturate All.
 * The shaders and the muffin key live in gradeEngine.js.
 */

const Applet = imports.ui.applet;
const Main = imports.ui.main;
const Settings = imports.ui.settings;

const Logic = require("./gradeLogic").GradeLogic;
const Engine = require("./gradeEngine");

const UUID = "iron-within-panel@mateo";
const HOTKEY_NAME = "cinematic-grade-panel-toggle";

function MyApplet(metadata, orientation, panelHeight, instanceId) {
    this._init(metadata, orientation, panelHeight, instanceId);
}

MyApplet.prototype = {
    __proto__: Applet.IconApplet.prototype,

    _init: function(metadata, orientation, panelHeight, instanceId) {
        Applet.IconApplet.prototype._init.call(this, orientation, panelHeight, instanceId);

        this.metadata = metadata;
        this.set_applet_icon_symbolic_name("applications-graphics-symbolic");
        this.set_applet_tooltip("Cinematic grade: off. Click to turn the grade on.");

        this._engine = Engine.getEngine(Logic.resolveProjectRoot(metadata.path));
        this.settings = new Settings.AppletSettings(this, UUID, this.instance_id);
        this.settings.bind("preset", "preset", this._onSettingsChanged);
        this.settings.bind("intensity", "intensity", this._onSettingsChanged);
        this.settings.bind("keybinding", "keybinding", this._onKeybindingChanged);
        this.settings.bind("composite-fullscreen", "composite_fullscreen", this._onSettingsChanged);

        this._engine.register("applet", "applet", (state) => this._onEngineState(state));
        this._engine.configure("applet", this._config());
        this._onKeybindingChanged();
    },

    on_applet_clicked: function() {
        this._engine.toggle("applet");
    },

    toggle: function() {
        this._engine.toggle("applet");
    },

    setActive: function(active) {
        this._engine.setActive("applet", !!active);
    },

    status: function() {
        let state = this._engine.status();
        state.kind = "applet";
        state.shortcut = this.settings.getValue("keybinding") || "";
        return state;
    },

    on_applet_removed_from_panel: function() {
        Main.keybindingManager.removeHotKey(HOTKEY_NAME);
        if (this._engine)
            this._engine.unregister("applet");
        if (this.settings)
            this.settings.finalize();
    },

    _config: function() {
        return {
            preset: this.settings.getValue("preset"),
            intensity: this.settings.getValue("intensity"),
            compositeFullscreen: this.settings.getValue("composite-fullscreen")
        };
    },

    _onSettingsChanged: function() {
        if (!this._engine.isOwner("applet"))
            return;
        this._engine.configure("applet", this._config());
    },

    _onKeybindingChanged: function() {
        Main.keybindingManager.removeHotKey(HOTKEY_NAME);
        if (!this._engine.isOwner("applet"))
            return;
        let key = this.settings.getValue("keybinding") || "";
        if (!key)
            return;
        let ok = Main.keybindingManager.addHotKey(HOTKEY_NAME, key, () => this._engine.toggle("applet"));
        if (!ok)
            global.logError("[" + UUID + "] could not bind " + key);
    },

    _onEngineState: function(state) {
        if (state.active) {
            let text = "Cinematic grade: on (" + state.preset + "). Click to turn the grade off.";
            if (state.error)
                text += " " + state.error;
            this.set_applet_tooltip(text);
            this._setIconColor("#3da9a0");
        } else if (state.error) {
            this.set_applet_tooltip("Cinematic grade: off. " + state.error);
            this._setIconColor(null);
        } else {
            this.set_applet_tooltip("Cinematic grade: off. Click to turn the grade on.");
            this._setIconColor(null);
        }
    },

    _setIconColor: function(color) {
        if (!this._applet_icon)
            return;
        this._applet_icon.style = color ? ("color: " + color + ";") : "";
    }
};

function main(metadata, orientation, panelHeight, instanceId) {
    return new MyApplet(metadata, orientation, panelHeight, instanceId);
}
