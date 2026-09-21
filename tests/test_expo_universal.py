# Copyright 2026 Scion Frontiers & Antigravity
# Test suite for Expo Universal Mobile Plugin (#24) and ExpoManager

import json
import os
import shutil
import tempfile
import unittest

from core.expo import ExpoManager, ExpoProjectConfig, ExpoDevSession, ExpoDoctorReport
from plugins.plugin_manager import PluginManager, ExpoUniversalPlugin, ALL_PLUGINS


class TestExpoUniversal(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="harness_expo_test_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_detect_expo_project_negative(self):
        res = ExpoManager.detect_project(self.test_dir)
        self.assertFalse(res["is_expo"])
        self.assertFalse(res["is_react_native"])
        self.assertIsNone(res["sdk_version"])

    def test_scaffold_universal_app(self):
        app_dir = os.path.join(self.test_dir, "my-universal-app")
        res = ExpoManager.scaffold_universal_app(
            target_dir=app_dir,
            name="My Universal App",
            bundle_id="com.scion.myuniversalapp",
            package_name="com.scion.myuniversalapp"
        )
        self.assertEqual(res["status"], "created")
        self.assertEqual(res["slug"], "my-universal-app")

        # Verify key files
        for rel_file in [
            "package.json",
            "app.json",
            "tsconfig.json",
            "app/_layout.tsx",
            "app/(tabs)/_layout.tsx",
            "app/(tabs)/index.tsx",
            "app/(tabs)/explore.tsx",
            "app/+not-found.tsx"
        ]:
            file_path = os.path.join(app_dir, rel_file)
            self.assertTrue(os.path.exists(file_path), f"Missing scaffolded file: {rel_file}")

        # Check app.json content
        with open(os.path.join(app_dir, "app.json"), "r") as f:
            app_data = json.load(f)
        expo_cfg = app_data["expo"]
        self.assertEqual(expo_cfg["name"], "My Universal App")
        self.assertEqual(expo_cfg["ios"]["bundleIdentifier"], "com.scion.myuniversalapp")
        self.assertEqual(expo_cfg["android"]["package"], "com.scion.myuniversalapp")
        self.assertTrue(expo_cfg["newArchEnabled"])
        self.assertIn("expo-router", expo_cfg["plugins"])

    def test_detect_expo_project_positive(self):
        app_dir = os.path.join(self.test_dir, "detect-test")
        ExpoManager.scaffold_universal_app(target_dir=app_dir, name="Detect Test")

        detect = ExpoManager.detect_project(app_dir)
        self.assertTrue(detect["is_expo"])
        self.assertTrue(detect["is_react_native"])
        self.assertTrue(detect["has_expo_router"])
        self.assertEqual(detect["sdk_version"], "52.0.0")

    def test_apply_config_plugin(self):
        app_dir = os.path.join(self.test_dir, "plugin-test")
        ExpoManager.scaffold_universal_app(target_dir=app_dir, name="Plugin Test")

        # 1. Add camera plugin with options
        res = ExpoManager.apply_config_plugin(
            app_dir,
            "expo-camera",
            {"cameraPermission": "Allow app to scan codes."}
        )
        self.assertEqual(res["status"], "added")

        with open(os.path.join(app_dir, "app.json"), "r") as f:
            app_data = json.load(f)
        plugins = app_data["expo"]["plugins"]
        self.assertEqual(len(plugins), 2)  # expo-router + expo-camera

        # 2. Update camera plugin idempotently
        res2 = ExpoManager.apply_config_plugin(
            app_dir,
            "expo-camera",
            {"cameraPermission": "Updated permission string."}
        )
        self.assertEqual(res2["status"], "updated")
        self.assertEqual(res2["total_plugins"], 2)  # No duplicate added

    def test_generate_eas_config(self):
        app_dir = os.path.join(self.test_dir, "eas-test")
        ExpoManager.scaffold_universal_app(target_dir=app_dir, name="EAS Test")

        res = ExpoManager.generate_eas_config(app_dir, apple_team_id="FD7Q764N23")
        self.assertEqual(res["status"], "generated")
        self.assertTrue(os.path.exists(res["eas_file"]))

        with open(res["eas_file"], "r") as f:
            eas_data = json.load(f)

        self.assertIn("development", eas_data["build"])
        self.assertIn("preview", eas_data["build"])
        self.assertIn("production", eas_data["build"])
        self.assertEqual(eas_data["build"]["production"]["ios"]["appleTeamId"], "FD7Q764N23")
        self.assertEqual(eas_data["submit"]["production"]["ios"]["ascApiKeyId"], "9KRPNNB5X4")

    def test_get_dev_session(self):
        sess = ExpoManager.get_dev_session(port=8081, tunnel=False)
        self.assertTrue(sess.url.startswith("http://"))
        self.assertTrue(sess.exp_url.startswith("exp://"))
        self.assertIn(":8081", sess.url)
        self.assertIn("EXPO GO SCANNER", sess.qr_ascii)

    def test_doctor_audit_healthy(self):
        app_dir = os.path.join(self.test_dir, "doc-test")
        ExpoManager.scaffold_universal_app(target_dir=app_dir, name="Doctor Test")

        report = ExpoManager.run_doctor_audit(app_dir)
        self.assertTrue(report.is_healthy)
        self.assertEqual(report.sdk_version, "52.0.0")
        self.assertEqual(len(report.errors), 0)

    def test_plugin_manager_integration(self):
        mgr = PluginManager()
        plugin = mgr.get_plugin("expo-universal-mobile")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.category, "platform")
        self.assertEqual(len(ALL_PLUGINS), 24)

        # Test plugin method execution
        app_dir = os.path.join(self.test_dir, "plugin-mgr-app")
        scaffold_res = plugin.scaffold_app(app_dir, "Plugin Manager App")
        self.assertEqual(scaffold_res["status"], "created")

        doctor_res = plugin.doctor(app_dir)
        self.assertTrue(doctor_res["is_healthy"])


if __name__ == "__main__":
    unittest.main()
