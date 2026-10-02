#!/usr/bin/env python3
"""Panel list edits for install.sh and uninstall.sh.

The grade does not need Python. This file is stdlib only so the installer
can call the system python3. Tests import the pure functions and do not
touch gsettings.
"""

import ast
import json
import os
import subprocess
import sys

MUFFIN_SCHEMA = "org.cinnamon.muffin"
UNREDIRECT_KEY = "unredirect-fullscreen-windows"


def parse_list(raw):
    raw = raw.strip()
    if raw.startswith("@as "):
        raw = raw[4:].strip()
    if raw in ("[]", "@as []"):
        return []
    value = ast.literal_eval(raw)
    if not isinstance(value, (list, tuple)):
        raise ValueError("gsettings value is not a list")
    return [str(item) for item in value]


def parse_int(raw):
    return int(str(raw).strip().split()[-1])


def render(items):
    if not items:
        return "@as []"
    parts = ["'" + str(item).replace("'", "") + "'" for item in items]
    return "[" + ", ".join(parts) + "]"


def choose_panel(panels):
    ids = []
    for item in panels:
        head = str(item).split(":")[0]
        if head.isdigit():
            ids.append(head)
    if not ids or "1" in ids:
        return "panel1"
    return "panel" + ids[0]


def extension_without(exts, uuid):
    return [item for item in exts if item != uuid]


def applet_present(applets, uuid):
    return any(uuid in item.split(":") for item in applets)


def applet_without(applets, uuid):
    return [item for item in applets if uuid not in item.split(":")]


def next_instance(applets, next_id):
    used = []
    for item in applets:
        parts = item.split(":")
        if len(parts) > 4 and parts[4].isdigit():
            used.append(int(parts[4]))
    instance = int(next_id)
    if used:
        instance = max(instance, max(used) + 1)
    return instance


def applet_entry(panel, uuid, instance):
    return "%s:right:2:%s:%d" % (panel, uuid, instance)


def plan_install(exts, applets, next_id, panels, applet_uuid, ext_uuid):
    messages = []
    if ext_uuid in exts:
        new_exts = extension_without(exts, ext_uuid)
        messages.append("Disabled shell extension " + ext_uuid)
        extensions_changed = True
    else:
        new_exts = list(exts)
        messages.append("Shell extension already disabled")
        extensions_changed = False

    if applet_present(applets, applet_uuid):
        messages.append("Applet already on the panel")
        return {
            "extensions": new_exts,
            "applets": list(applets),
            "next_id": int(next_id),
            "extensions_changed": extensions_changed,
            "applets_changed": False,
            "next_changed": False,
            "messages": messages,
        }

    instance = next_instance(applets, next_id)
    entry = applet_entry(choose_panel(panels), applet_uuid, instance)
    messages.append("Enabled " + entry)
    return {
        "extensions": new_exts,
        "applets": list(applets) + [entry],
        "next_id": instance + 1,
        "extensions_changed": extensions_changed,
        "applets_changed": True,
        "next_changed": True,
        "messages": messages,
    }


def plan_uninstall(exts, applets, applet_uuid, ext_uuid):
    messages = []
    if ext_uuid in exts:
        new_exts = extension_without(exts, ext_uuid)
        messages.append("Disabled extension " + ext_uuid)
        extensions_changed = True
    else:
        new_exts = list(exts)
        messages.append("Extension was not enabled")
        extensions_changed = False
    new_applets = applet_without(applets, applet_uuid)
    if len(new_applets) != len(applets):
        messages.append("Removed applet from the panel")
        applets_changed = True
    else:
        messages.append("Applet was not on the panel")
        applets_changed = False
    return {
        "extensions": new_exts,
        "applets": new_applets,
        "extensions_changed": extensions_changed,
        "applets_changed": applets_changed,
        "messages": messages,
    }


def unredirect_path():
    return os.path.join(os.path.expanduser("~/.config"), "iron-within", "unredirect.json")


def read_unredirect_payload(text):
    data = json.loads(text)
    if not isinstance(data, dict) or not isinstance(data.get("value"), bool):
        raise ValueError("unredirect.json value is not a boolean")
    return data["value"]


def gget_raw(key):
    return subprocess.check_output(
        ["gsettings", "get", "org.cinnamon", key], text=True
    ).strip()


def gset(key, value):
    subprocess.check_call(["gsettings", "set", "org.cinnamon", key, value])


def apply_plan(plan):
    if plan["extensions_changed"]:
        gset("enabled-extensions", render(plan["extensions"]))
    if plan["applets_changed"]:
        gset("enabled-applets", render(plan["applets"]))
    if plan.get("next_changed"):
        gset("next-applet-id", str(plan["next_id"]))
    for message in plan["messages"]:
        print(message)


def restore_unredirect_file(path=None):
    """Put the muffin key back if the shell died while the grade was on."""
    path = path or unredirect_path()
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        value = read_unredirect_payload(handle.read())
    subprocess.check_call([
        "gsettings", "set", MUFFIN_SCHEMA, UNREDIRECT_KEY,
        "true" if value else "false",
    ])
    os.remove(path)
    print("Restored unredirect-fullscreen-windows to", "true" if value else "false")
    return value


def install(applet_uuid, ext_uuid):
    plan = plan_install(
        parse_list(gget_raw("enabled-extensions")),
        parse_list(gget_raw("enabled-applets")),
        parse_int(gget_raw("next-applet-id")),
        parse_list(gget_raw("panels-enabled")),
        applet_uuid,
        ext_uuid,
    )
    apply_plan(plan)


def uninstall(applet_uuid, ext_uuid):
    plan = plan_uninstall(
        parse_list(gget_raw("enabled-extensions")),
        parse_list(gget_raw("enabled-applets")),
        applet_uuid,
        ext_uuid,
    )
    apply_plan(plan)
    restore_unredirect_file()


def main(argv):
    if len(argv) != 4 or argv[1] not in ("install", "uninstall"):
        print("Usage: cinnamon_settings.py install|uninstall APPLET_UUID EXT_UUID", file=sys.stderr)
        return 2
    if argv[1] == "install":
        install(argv[2], argv[3])
    else:
        uninstall(argv[2], argv[3])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
