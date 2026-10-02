import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cinnamon_settings import (  # noqa: E402
    applet_entry,
    choose_panel,
    parse_int,
    parse_list,
    plan_install,
    plan_uninstall,
    read_unredirect_payload,
    render,
)


class ListCodec(unittest.TestCase):
    def test_roundtrip_empty_and_typed(self):
        self.assertEqual(parse_list("@as []"), [])
        self.assertEqual(parse_list("[]"), [])
        raw = "['panel1:right:2:iron-within-panel@mateo:4', 'menu@cinnamon.org']"
        self.assertEqual(render(parse_list(raw)), raw)
        self.assertEqual(parse_list("@as " + raw)[0], "panel1:right:2:iron-within-panel@mateo:4")

    def test_render_strips_quotes(self):
        self.assertEqual(render(["a'b"]), "['ab']")

    def test_parse_int_accepts_a_bare_number_or_a_typed_value(self):
        self.assertEqual(parse_int("27"), 27)
        self.assertEqual(parse_int("uint32 27"), 27)


class InstallPlan(unittest.TestCase):
    def test_install_is_idempotent_and_picks_panel1(self):
        exts = ["some@other"]
        applets = ["panel1:left:0:menu@cinnamon.org:0"]
        first = plan_install(exts, applets, 3, ["1:0:bottom"], "iron-within-panel@mateo", "iron-within@mateo")
        self.assertTrue(first["applets_changed"])
        self.assertEqual(first["applets"][-1], applet_entry("panel1", "iron-within-panel@mateo", 3))
        self.assertEqual(first["next_id"], 4)
        again = plan_install(
            first["extensions"], first["applets"], first["next_id"],
            ["1:0:bottom"], "iron-within-panel@mateo", "iron-within@mateo",
        )
        self.assertFalse(again["applets_changed"])
        self.assertIn("already on the panel", again["messages"][-1])

    def test_install_uses_another_panel_when_panel1_is_absent(self):
        plan = plan_install([], [], 1, ["2:0:left"], "iron-within-panel@mateo", "iron-within@mateo")
        self.assertTrue(plan["applets"][0].startswith("panel2:"))

    def test_install_drops_the_extension_and_bumps_past_used_ids(self):
        applets = ["panel1:right:0:other@cinnamon.org:9"]
        plan = plan_install(
            ["iron-within@mateo"], applets, 1, ["1:0:bottom"],
            "iron-within-panel@mateo", "iron-within@mateo",
        )
        self.assertNotIn("iron-within@mateo", plan["extensions"])
        self.assertTrue(plan["extensions_changed"])
        self.assertEqual(plan["applets"][-1], "panel1:right:2:iron-within-panel@mateo:10")

    def test_uninstall_removes_only_our_applet(self):
        applets = [
            "panel1:left:0:menu@cinnamon.org:0",
            "panel1:right:2:iron-within-panel@mateo:4",
        ]
        plan = plan_uninstall(applets, applets, "iron-within-panel@mateo", "iron-within@mateo")
        self.assertEqual(plan["applets"], ["panel1:left:0:menu@cinnamon.org:0"])
        self.assertTrue(plan["applets_changed"])
        missing = plan_uninstall([], plan["applets"], "iron-within-panel@mateo", "iron-within@mateo")
        self.assertFalse(missing["applets_changed"])

    def test_choose_panel_defaults_to_panel1(self):
        self.assertEqual(choose_panel([]), "panel1")
        self.assertEqual(choose_panel(["1:0:bottom", "2:0:top"]), "panel1")


class UnredirectFile(unittest.TestCase):
    def test_payload_matches_the_js_contract(self):
        self.assertTrue(read_unredirect_payload('{"value":true}'))
        self.assertFalse(read_unredirect_payload('{"value":false}'))
        with self.assertRaises(ValueError):
            read_unredirect_payload('{"value":1}')
        with self.assertRaises(json.JSONDecodeError):
            read_unredirect_payload("{")


if __name__ == "__main__":
    unittest.main()
