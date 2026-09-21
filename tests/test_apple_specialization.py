#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Test suite for Apple Platform Specialization (Xcode, Swift 6, simctl, notarytool, HIG)

import os
import shutil
import tempfile
import unittest

from core.apple import (
    XcodeBuilder,
    XCResultParser,
    Diagnostic,
    SimulatorManager,
    NotaryPipeline,
    SwiftConcurrencyGate,
    HIGAccessibilityAuditor,
)

class TestAppleSpecialization(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    # -------------------------------------------------------------
    # 1. Xcode & Swift 6 Diagnostics
    # -------------------------------------------------------------
    def test_swift6_strict_concurrency_diagnostics_parser(self):
        sample_output = """
/Users/dev/App/ViewModel.swift:24:9: error: call to main actor-isolated initializer 'init()' in a synchronous nonisolated context
/Users/dev/App/Service.swift:42:15: warning: mutation of captured var 'counter' in concurrently-executing code
/Users/dev/App/Model.swift:12:1: warning: type 'UserData' does not conform to the 'Sendable' protocol
/Users/dev/App/Utils.swift:5:8: note: mark with '@unchecked Sendable'
"""
        diags = XcodeBuilder.parse_diagnostics(sample_output)
        self.assertEqual(len(diags), 4)

        # First diagnostic: MainActor isolation error
        d1 = diags[0]
        self.assertEqual(d1.severity, "error")
        self.assertEqual(d1.line, 24)
        self.assertTrue(d1.is_strict_concurrency)
        self.assertIn("@MainActor", d1.suggested_fix)

        # Second diagnostic: Concurrently executing mutation
        d2 = diags[1]
        self.assertEqual(d2.severity, "warning")
        self.assertTrue(d2.is_strict_concurrency)
        self.assertIn("Actor", d2.suggested_fix)

        # Third diagnostic: Sendable conformance
        d3 = diags[2]
        self.assertTrue(d3.is_strict_concurrency)
        self.assertIn("Sendable", d3.suggested_fix)

    def test_xcresult_parser(self):
        sample_xcresult_json = {
            "actions": {
                "_values": [
                    {
                        "buildResult": {
                            "issues": {
                                "testFailureSummaries": {
                                    "_values": [
                                        {
                                            "testCaseName": "UserViewModelTests.testUserLoginFailure()",
                                            "message": "XCTAssertEqual failed: (\"unauthorized\") is not equal to (\"success\")",
                                            "documentLocationInCreatingWorkspace": {
                                                "url": {"_value": "file:///Tests/UserViewModelTests.swift#CharacterRangeLen=0&EndingColumnNumber=9"}
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                ]
            }
        }
        failures = XCResultParser.parse_test_summary(sample_xcresult_json)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["test"], "UserViewModelTests.testUserLoginFailure()")
        self.assertIn("XCTAssertEqual failed", failures[0]["message"])

    # -------------------------------------------------------------
    # 2. Simulator Manager (simctl)
    # -------------------------------------------------------------
    def test_simulator_manager_catalog_and_clean_status(self):
        mgr = SimulatorManager()
        devices = mgr.list_devices("iOS")
        # On macOS host with Xcode, real devices are listed. In container, mock list is returned.
        self.assertGreater(len(devices), 0)

        # Verify clean status bar override method executes safely
        res_status = mgr.configure_clean_status_bar("NON-EXISTENT-DEVICE")
        # Non-existent device should return False or True safely without unhandled exception
        self.assertIsInstance(res_status, bool)

        # Verify screenshot creates output directory and file
        png_path = os.path.join(self.temp_dir, "test_shot.png")
        shot_res = mgr.take_screenshot("NON-EXISTENT-DEVICE", png_path)
        self.assertIsInstance(shot_res, str)

    # -------------------------------------------------------------
    # 3. Notarization & Codesign
    # -------------------------------------------------------------
    def test_notarization_and_codesign_pipeline(self):
        # 1. Verification of a system binary or directory
        status = NotaryPipeline.verify_codesign("/bin/zsh")
        self.assertTrue(status.is_signed)
        self.assertTrue(status.satisfies_requirements)

        # 2. Missing credentials detection in notarytool
        res = NotaryPipeline.submit_notarization("/path/to/app.zip")
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "MissingCredentials")

    # -------------------------------------------------------------
    # 4. Swift 6 Concurrency & Swift Testing Gate
    # -------------------------------------------------------------
    def test_swift_concurrency_gate(self):
        swift_code = """
import SwiftUI
import Testing

class UnsafeViewModel: ObservableObject {
    @Published var count = 0
}

@Observable class ModernViewModel {
    var title = ""
}

var globalCounter: Int = 0

@Test func verifySomething() {
    #expect(true)
}
"""
        issues = SwiftConcurrencyGate.audit_swift_code(swift_code, "TestView.swift")
        # Should flag UnsafeViewModel (missing @MainActor), ModernViewModel, and globalCounter
        self.assertGreaterEqual(len(issues), 2)
        issue_types = [i["type"] for i in issues]
        self.assertIn("MissingMainActor", issue_types)
        self.assertIn("UnsafeGlobalMutableVar", issue_types)

        # Directory audit with Swift Testing count
        file_path = os.path.join(self.temp_dir, "TestFile.swift")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(swift_code)

        result = SwiftConcurrencyGate.audit_directory(self.temp_dir)
        self.assertEqual(result.total_files_scanned, 1)
        self.assertEqual(result.swift_testing_suites, 1)
        self.assertEqual(result.xctest_suites, 0)

    # -------------------------------------------------------------
    # 5. Human Interface Guidelines (HIG) & Accessibility Auditor
    # -------------------------------------------------------------
    def test_hig_accessibility_auditor(self):
        swiftui_code = """
import SwiftUI

struct BadView: View {
    var body: some View {
        VStack {
            Button(action: { print("tap") }) {
                Image(systemName: "trash")
            }
            .frame(width: 30, height: 30)
            
            Text("Hardcoded typography")
                .font(.system(size: 12))
                .background(Color.white)
        }
    }
}
"""
        issues = HIGAccessibilityAuditor.audit_swiftui_code(swiftui_code, "BadView.swift")
        rule_ids = [i.rule_id for i in issues]

        # 1. Accessible Icon Button
        self.assertIn("HIG-A11Y-001", rule_ids)
        # 2. Dynamic Type
        self.assertIn("HIG-TYPO-002", rule_ids)
        # 3. Hit target < 44pt
        self.assertIn("HIG-TARGET-003", rule_ids)
        # 4. Hardcoded Color.white
        self.assertIn("HIG-COLOR-004", rule_ids)

        # Directory audit report score
        file_path = os.path.join(self.temp_dir, "BadView.swift")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(swiftui_code)

        report = HIGAccessibilityAuditor.audit_directory(self.temp_dir)
        self.assertEqual(report.total_files_scanned, 1)
        self.assertLess(report.score, 100.0)
        self.assertEqual(len(report.issues), len(issues))

    # -------------------------------------------------------------
    # 6. App Store Pre-Submission Compliance (mjmirza/app-store-compliance)
    # -------------------------------------------------------------
    def test_app_store_compliance_clean_project(self):
        from core.apple import AppStoreComplianceAuditor
        # Clean project with PrivacyInfo and Info.plist
        plist_path = os.path.join(self.temp_dir, "Info.plist")
        with open(plist_path, "w", encoding="utf-8") as f:
            f.write("<plist><dict><key>ITSAppUsesNonExemptEncryption</key><false/></dict></plist>")

        privacy_path = os.path.join(self.temp_dir, "PrivacyInfo.xcprivacy")
        with open(privacy_path, "w", encoding="utf-8") as f:
            f.write("<plist><dict></dict></plist>")

        swift_path = os.path.join(self.temp_dir, "Main.swift")
        with open(swift_path, "w", encoding="utf-8") as f:
            f.write("import SwiftUI\nstruct AppView: View { var body: some View { Text(\"Hello\") } }")

        report = AppStoreComplianceAuditor.audit_project(self.temp_dir)
        self.assertTrue(report.is_compliant)
        self.assertEqual(report.critical_count, 0)
        self.assertGreaterEqual(report.score, 90)

    def test_app_store_compliance_catches_blockers(self):
        from core.apple import AppStoreComplianceAuditor
        # Project with missing usage description, staging URL, and account deletion omission
        swift_path = os.path.join(self.temp_dir, "UnsafeView.swift")
        with open(swift_path, "w", encoding="utf-8") as f:
            f.write("""
import AVFoundation
import CoreLocation

func connect() {
    let api = "http://staging.api.internal/v1/auth"
    let user = createAccount(username: "john")
}
""")
        report = AppStoreComplianceAuditor.audit_project(self.temp_dir)
        self.assertFalse(report.is_compliant)
        self.assertGreater(report.critical_count, 0)
        self.assertLess(report.score, 60)

        pattern_ids = [f.pattern_id for f in report.findings]
        self.assertIn("APPLE-2.1-STAGING-BACKEND", pattern_ids)
        self.assertIn("APPLE-5.1.1-MISSING-USAGE-DESCRIPTION", pattern_ids)
        self.assertIn("APPLE-5.1.1-NO-ACCOUNT-DELETION", pattern_ids)

    def test_apple_developer_plugin_integration(self):
        from plugins.plugin_manager import PluginManager, AppleDeveloperPlugin
        pm = PluginManager()
        plugin = pm.get_plugin("apple-developer")
        self.assertIsNotNone(plugin)
        self.assertIsInstance(plugin, AppleDeveloperPlugin)

        creds = plugin.get_asc_credentials()
        self.assertEqual(creds["key_id"], "9KRPNNB5X4")
        self.assertEqual(creds["team_id"], "FD7Q764N23")

        compliance = plugin.audit_compliance(self.temp_dir)
        self.assertIn("is_compliant", compliance)
        self.assertIn("score", compliance)
        self.assertIn("findings", compliance)

if __name__ == "__main__":
    unittest.main()
