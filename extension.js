/* Shell-extension entry. The grade itself lives in gradeEngine.js.
 * If the panel applet is loaded, the applet owns the grade and this
 * extension does not mount a second copy.
 */

const Main = imports.ui.main;
const Settings = imports.ui.settings;

const Logic = require("./gradeLogic").GradeLogic;
const Engine = require("./gradeEngine");

const UUID = "iron-within@mateo";
const HOTKEY_NAME = "cinematic-grade-toggle";

let controller = null;

function init(metadata) {
    controller = new Controller(metadata);
}

function enable() {
    return controller.enable();
}

function disable() {
    controller.disable();
}

function Controller(metadata) {
    this._init(metadata);
}

Controller.prototype = {
    _init: function(metadata) {
        this.metadata = metadata;
        this.settings = null;
        this._engine = null;
        this._owns = false;
        this._seenActive = false;
        this._silent = false;
    },

    enable: function() {
        this.settings = new Settings.ExtensionSettings(this, this.metadata.uuid);
        this.settings.bind("active", "active", this._onSettingsChanged);
        this.settings.bind("preset", "preset", this._onSettingsChanged);
        this.settings.bind("intensity", "intensity", this._onSettingsChanged);
        this.settings.bind("toggle-key", "toggle_key", this._onKeybindingChanged);
        this.settings.bind("composite-fullscreen", "composite_fullscreen", this._onSettingsChanged);

        this._owns = false;
        this._seenActive = false;
        this._engine = Engine.getEngine(Logic.resolveProjectRoot(this.metadata.path));
        let owns = this._engine.register("extension", "extension", (state) => this._onEngineState(state));
        if (owns)
            global.log("[" + UUID + "] enabled, preset " + this.settings.getValue("preset"));
        else
            global.log("[" + UUID + "] panel applet owns the grade");
        return this;
    },

    disable: function() {
        Main.keybindingManager.removeHotKey(HOTKEY_NAME);
        if (this._engine)
            this._engine.unregister("extension");
        if (this.settings)
            this.settings.finalize();
        this.settings = null;
        this._owns = false;
        global.log("[" + UUID + "] disabled");
    },

    toggle: function() {
        if (!this._engine || !this._engine.isOwner("extension"))
            return;
        this.setActive(!this.settings.getValue("active"));
    },

    setActive: function(value) {
        if (!this._engine || !this._engine.isOwner("extension"))
            return;
        this.settings.setValue("active", !!value);
    },

    reloadPresets: function() {
        if (this._engine)
            this._engine.reloadPresets();
    },

    status: function() {
        let state = this._engine.status();
        state.kind = "extension";
        state.shortcut = this.settings ? (this.settings.getValue("toggle-key") || "") : "";
        return state;
    },

    _config: function() {
        return {
            preset: this.settings.getValue("preset"),
            intensity: this.settings.getValue("intensity"),
            compositeFullscreen: this.settings.getValue("composite-fullscreen")
        };
    },

    _onSettingsChanged: function() {
        if (this._silent || !this._engine || !this._engine.isOwner("extension"))
            return;
        this._engine.configure("extension", this._config());
        this._engine.setActive("extension", !!this.settings.getValue("active"));
    },

    _onKeybindingChanged: function() {
        this._bindHotkey();
    },

    _onEngineState: function(state) {
        let owns = state.owner === "extension";
        let becameOwner = owns && !this._owns;
        if (!owns)
            this._owns = false;
        if (becameOwner) {
            this._owns = true;
            this._engine.configure("extension", this._config());
            this._engine.setActive("extension", !!this.settings.getValue("active"));
            this._bindHotkey();
            return;
        }
        if (owns && this.settings && this.settings.getValue("active") !== state.active) {
            this._silent = true;
            this.settings.setValue("active", state.active);
            this._silent = false;
        }
        if (owns && state.active !== this._seenActive)
            this._notify(state.active);
        this._seenActive = state.active;
        this._bindHotkey();
    },

    _bindHotkey: function() {
        Main.keybindingManager.removeHotKey(HOTKEY_NAME);
        if (!this._engine || !this._engine.isOwner("extension") || !this.settings)
            return;
        let key = this.settings.getValue("toggle-key") || "";
        if (!key)
            return;
        let ok = Main.keybindingManager.addHotKey(HOTKEY_NAME, key, () => this.toggle());
        if (!ok)
            global.logError("[" + UUID + "] could not bind " + key);
    },

    _notify: function(active) {
        if (!this.settings.getValue("show-osd"))
            return;
        if (active) {
            let intensity = Number(this.settings.getValue("intensity"));
            if (!isFinite(intensity))
                intensity = 1;
            Main.notify(
                "Cinematic grade on",
                this.settings.getValue("preset") + " at " + intensity.toFixed(2)
            );
        } else {
            Main.notify("Cinematic grade off", "Original color restored.");
        }
    }
};
