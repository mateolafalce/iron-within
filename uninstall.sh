#!/bin/bash
# Turn the grade off, restore the muffin unredirect key if a crash left it
# overridden, drop the panel applet and the shell extension, remove the links.
# Does not touch ICC profiles, gamma, or the project files.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APPLET_UUID="iron-within-panel@mateo"
EXT_UUID="iron-within@mateo"
APPLET_DEST="${HOME}/.local/share/cinnamon/applets/${APPLET_UUID}"
EXT_DEST="${HOME}/.local/share/cinnamon/extensions/${EXT_UUID}"

if command -v gdbus >/dev/null 2>&1; then
    gdbus call --session --dest org.Cinnamon --object-path /org/Cinnamon \
        --method org.Cinnamon.Eval \
        "var a = imports.ui.appletManager.get_object_for_uuid('${APPLET_UUID}', '${APPLET_UUID}'); if (a && a.setActive) a.setActive(false); var o = imports.ui.extensionSystem.get_object_for_uuid('${EXT_UUID}'); if (o && o.setActive) o.setActive(false);" \
        >/dev/null 2>&1 || true
fi

python3 "$ROOT/scripts/cinnamon_settings.py" uninstall "$APPLET_UUID" "$EXT_UUID"

remove_link() {
    local dest="$1"
    if [[ -L "$dest" ]]; then
        rm "$dest"
        echo "Removed link $dest"
    elif [[ -e "$dest" ]]; then
        echo "Left in place (not a symlink): $dest" >&2
        exit 1
    fi
}

remove_link "$APPLET_DEST"
remove_link "$EXT_DEST"

echo "Uninstalled. Monitor ICC profiles were not modified."
