#!/bin/bash
# Link the panel applet and enable it. The grade stays off until a click or Super+G.
# The shell extension is linked but left disabled, so the shader is not applied twice.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APPLET_UUID="iron-within-panel@mateo"
EXT_UUID="iron-within@mateo"
APPLET_DEST="${HOME}/.local/share/cinnamon/applets/${APPLET_UUID}"
EXT_DEST="${HOME}/.local/share/cinnamon/extensions/${EXT_UUID}"

mkdir -p "$(dirname "$APPLET_DEST")" "$(dirname "$EXT_DEST")"

if [[ -e "$APPLET_DEST" && ! -L "$APPLET_DEST" ]]; then
    echo "Refusing to replace a real directory: $APPLET_DEST" >&2
    exit 1
fi
if [[ -e "$EXT_DEST" && ! -L "$EXT_DEST" ]]; then
    echo "Refusing to replace a real directory: $EXT_DEST" >&2
    exit 1
fi

ln -sfn "$ROOT/panel" "$APPLET_DEST"
ln -sfn "$ROOT" "$EXT_DEST"
echo "Linked $APPLET_DEST -> $ROOT/panel"
echo "Linked $EXT_DEST -> $ROOT"

if command -v gdbus >/dev/null 2>&1; then
    gdbus call --session --dest org.Cinnamon --object-path /org/Cinnamon \
        --method org.Cinnamon.Eval \
        "var o = imports.ui.extensionSystem.get_object_for_uuid('${EXT_UUID}'); if (o && o.setActive) o.setActive(false);" \
        >/dev/null 2>&1 || true
fi

python3 "$ROOT/scripts/cinnamon_settings.py" install "$APPLET_UUID" "$EXT_UUID"

echo "Panel icon: the hooded mark. Click to toggle, same gesture as Desaturate All."
echo "Shortcut: Super+G. The grade starts off."
echo "Right-click the icon and choose Configure to pick a preset or intensity."
