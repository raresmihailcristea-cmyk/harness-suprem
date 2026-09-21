#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Apple App Store Pre-Submission Compliance Auditor & Review Blocker Gate
# Integrated from mjmirza/app-store-compliance taxonomy and Apple App Store Review Guidelines

from __future__ import annotations
from dataclasses import dataclass, field
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("core.apple.compliance")

@dataclass
class ComplianceFinding:
    pattern_id: str
    guideline: str
    title: str
    severity: str  # "critical", "high", "medium", "low"
    file_path: str
    line_number: int
    matched_signal: str
    fix_recommendation: str

@dataclass
class ComplianceReport:
    is_compliant: bool
    score: int
    total_files_scanned: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    findings: List[ComplianceFinding] = field(default_factory=list)
    appeal_recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_compliant": self.is_compliant,
            "score": self.score,
            "total_files_scanned": self.total_files_scanned,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "findings": [
                {
                    "pattern_id": f.pattern_id,
                    "guideline": f.guideline,
                    "title": f.title,
                    "severity": f.severity,
                    "file_path": f.file_path,
                    "line_number": f.line_number,
                    "matched_signal": f.matched_signal,
                    "fix": f.fix_recommendation,
                }
                for f in self.findings
            ],
            "appeal_recommendations": self.appeal_recommendations,
        }

class AppStoreComplianceAuditor:
    """Pre-submission gate evaluating Swift/Xcode projects against Apple Review Guidelines."""

    PATTERNS_PATH = "/Users/rarescristea/.gemini/config/skills/app-store-compliance/data/rejection-patterns.json"

    # Core Sensitive Permissions mapping (Guideline 5.1.1)
    SENSITIVE_FRAMEWORKS = {
        "AVFoundation": ("NSCameraUsageDescription", "Guideline 5.1.1(ii): Camera access requires clear purpose string in Info.plist"),
        "CoreLocation": ("NSLocationWhenInUseUsageDescription", "Guideline 5.1.1(ii): Location access requires specific user benefit description in Info.plist"),
        "Photos": ("NSPhotoLibraryUsageDescription", "Guideline 5.1.1(ii): Photo library access requires explanation in Info.plist"),
        "CoreBluetooth": ("NSBluetoothAlwaysUsageDescription", "Guideline 5.1.1(ii): Bluetooth access requires explicit purpose string"),
        "AppTrackingTransparency": ("NSUserTrackingUsageDescription", "Guideline 5.1.2(i): ATT tracking requires explicit purpose explanation"),
    }

    # Required Reason APIs (Apple Privacy Manifests 2024-2026)
    REQUIRED_REASON_SIGNALS = [
        ("UserDefaults", "NSPrivacyAccessedAPICategoryUserDefaults", "Apple Privacy Manifest: UserDefaults requires PrivacyInfo.xcprivacy declaration"),
        ("systemBootTime", "NSPrivacyAccessedAPICategorySystemBootTime", "Apple Privacy Manifest: systemBootTime requires PrivacyInfo.xcprivacy declaration"),
        ("statfs", "NSPrivacyAccessedAPICategoryDiskSpace", "Apple Privacy Manifest: Disk space inspection requires PrivacyInfo.xcprivacy declaration"),
    ]

    # Staging/localhost signals in production (Guideline 2.1)
    STAGING_URL_PATTERNS = [
        re.compile(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|staging\.[a-zA-Z0-9.-]+|test\.[a-zA-Z0-9.-]+|dev\.[a-zA-Z0-9.-]+)", re.IGNORECASE),
    ]

    # Account creation without deletion signals (Guideline 5.1.1(v))
    AUTH_SIGNALS = [
        re.compile(r"\b(createAccount|signUp|registerUser|registerAccount)\b", re.IGNORECASE)
    ]
    DELETION_SIGNALS = [
        re.compile(r"\b(deleteAccount|requestAccountDeletion|removeUserAccount)\b", re.IGNORECASE)
    ]

    @classmethod
    def audit_project(cls, project_dir: str) -> ComplianceReport:
        """Runs the enterprise pre-submission compliance audit on the target project directory."""
        findings: List[ComplianceFinding] = []
        files_scanned = 0
        has_privacy_manifest = False
        has_account_creation = False
        has_account_deletion = False

        # First pass: check for PrivacyInfo.xcprivacy and Info.plist presence
        info_plist_path = None
        info_plist_content = ""

        for root, _, files in os.walk(project_dir):
            if any(p in root for p in [".git", "build", "DerivedData", ".build", "Pods"]):
                continue
            for f in files:
                if f == "PrivacyInfo.xcprivacy":
                    has_privacy_manifest = True
                if f in ("Info.plist", "App-Info.plist"):
                    info_plist_path = os.path.join(root, f)
                    try:
                        with open(info_plist_path, "r", encoding="utf-8", errors="ignore") as pf:
                            info_plist_content = pf.read()
                    except Exception:
                        pass

        # Scan project files
        for root, _, files in os.walk(project_dir):
            if any(p in root for p in [".git", "build", "DerivedData", ".build", "Pods"]):
                continue

            for f in files:
                if not f.endswith((".swift", ".m", ".h", ".plist", ".json")):
                    continue

                full_path = os.path.join(root, f)
                files_scanned += 1
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f_in:
                        content = f_in.read()
                        lines = content.splitlines()
                except Exception:
                    continue

                rel_path = os.path.relpath(full_path, project_dir)

                # Check account creation vs deletion signals
                for auth_p in cls.AUTH_SIGNALS:
                    if auth_p.search(content):
                        has_account_creation = True
                        break
                for del_p in cls.DELETION_SIGNALS:
                    if del_p.search(content):
                        has_account_deletion = True
                        break

                # 1. Staging/Localhost Backend URLs (Guideline 2.1)
                for line_idx, line in enumerate(lines, 1):
                    for stg in cls.STAGING_URL_PATTERNS:
                        m = stg.search(line)
                        if m and not line.strip().startswith("//") and not "test" in rel_path.lower():
                            findings.append(ComplianceFinding(
                                pattern_id="APPLE-2.1-STAGING-BACKEND",
                                guideline="2.1",
                                title="Backend points at localhost or staging environment",
                                severity="critical",
                                file_path=rel_path,
                                line_number=line_idx,
                                matched_signal=m.group(0),
                                fix_recommendation="Ensure production builds point to live production APIs with active SSL certificates.",
                            ))

                # 2. Sensitive Framework Linking without Usage Descriptions (Guideline 5.1.1(ii))
                if f.endswith((".swift", ".m")):
                    for fw, (plist_key, msg) in cls.SENSITIVE_FRAMEWORKS.items():
                        if f"import {fw}" in content:
                            if not info_plist_content or plist_key not in info_plist_content:
                                findings.append(ComplianceFinding(
                                    pattern_id="APPLE-5.1.1-MISSING-USAGE-DESCRIPTION",
                                    guideline="5.1.1(ii)",
                                    title=f"Linked {fw} without {plist_key} in Info.plist",
                                    severity="critical",
                                    file_path=rel_path,
                                    line_number=1,
                                    matched_signal=f"import {fw}",
                                    fix_recommendation=f"Add `{plist_key}` to Info.plist with a concrete explanation of user benefit.",
                                ))

                # 3. Required Reason APIs without Privacy Manifest (Apple 2024-2026)
                if not has_privacy_manifest and f.endswith((".swift", ".m")):
                    for api_signal, cat, desc in cls.REQUIRED_REASON_SIGNALS:
                        if api_signal in content:
                            findings.append(ComplianceFinding(
                                pattern_id="APPLE-PRIVACY-MANIFEST-MISSING",
                                guideline="Privacy Manifest 2024+",
                                title=f"Required reason API `{api_signal}` used without PrivacyInfo.xcprivacy",
                                severity="critical",
                                file_path=rel_path,
                                line_number=1,
                                matched_signal=api_signal,
                                fix_recommendation=f"Include `PrivacyInfo.xcprivacy` with `{cat}` declared.",
                            ))
                            break  # Flag once per file

                # 4. In-App Purchase Alternative Bypass (Guideline 3.1.1)
                if f.endswith((".swift", ".m")):
                    if ("stripe.com" in content or "paypal.com" in content) and not "StoreKit" in content:
                        findings.append(ComplianceFinding(
                            pattern_id="APPLE-3.1.1-EXTERNAL-PAYMENT-BYPASS",
                            guideline="3.1.1",
                            title="External payment provider detected without StoreKit in-app purchase flow",
                            severity="critical",
                            file_path=rel_path,
                            line_number=1,
                            matched_signal="external payment gateway",
                            fix_recommendation="Digital goods must use Apple StoreKit In-App Purchase. External payment is only permitted for physical goods/services or under approved EU/US external purchase entitlements.",
                        ))

                # 5. Placeholder / Lorem Ipsum text in production (Guideline 2.1)
                if "lorem ipsum" in content.lower():
                    findings.append(ComplianceFinding(
                        pattern_id="APPLE-2.1-PLACEHOLDER-CONTENT",
                        guideline="2.1",
                        title="Placeholder 'Lorem Ipsum' text detected in release code",
                        severity="high",
                        file_path=rel_path,
                        line_number=1,
                        matched_signal="Lorem Ipsum",
                        fix_recommendation="Replace all placeholder strings with finalized product copy.",
                    ))

        # 6. Global Check: Account creation without account deletion (Guideline 5.1.1(v))
        if has_account_creation and not has_account_deletion:
            findings.append(ComplianceFinding(
                pattern_id="APPLE-5.1.1-NO-ACCOUNT-DELETION",
                guideline="5.1.1(v)",
                title="Account creation supported without an in-app account deletion flow",
                severity="critical",
                file_path=info_plist_path or "Project Configuration",
                line_number=1,
                matched_signal="createAccount without deleteAccount",
                fix_recommendation="Provide an in-app button to immediately delete the user account and associated personal data (not just a mailto: link).",
            ))

        # 7. Encryption Declaration Check (ITSAppUsesNonExemptEncryption)
        if info_plist_content and "ITSAppUsesNonExemptEncryption" not in info_plist_content:
            findings.append(ComplianceFinding(
                pattern_id="APPLE-EXPORT-COMPLIANCE-MISSING",
                guideline="Export Compliance",
                title="Missing ITSAppUsesNonExemptEncryption in Info.plist",
                severity="medium",
                file_path=info_plist_path or "Info.plist",
                line_number=1,
                matched_signal="Missing ITSAppUsesNonExemptEncryption",
                fix_recommendation="Add `<key>ITSAppUsesNonExemptEncryption</key><false/>` to avoid export compliance prompts during App Store Connect release.",
            ))

        # Tally counts
        critical_c = sum(1 for f in findings if f.severity == "critical")
        high_c = sum(1 for f in findings if f.severity == "high")
        medium_c = sum(1 for f in findings if f.severity == "medium")
        low_c = sum(1 for f in findings if f.severity == "low")

        # Score calculation: 100 max, -20 per critical, -10 per high, -5 per medium
        deductions = (critical_c * 25) + (high_c * 12) + (medium_c * 5) + (low_c * 2)
        final_score = max(0, 100 - deductions)
        is_compliant = (critical_c == 0 and final_score >= 80)

        # Build Appeal Recommendations if findings exist
        appeals = []
        if critical_c > 0:
            appeals.append("CRITICAL: Resolve all blocking issues prior to App Store submission to avoid 1-2 week Resolution Center cycles.")
        if any(f.pattern_id == "APPLE-5.1.1-NO-ACCOUNT-DELETION" for f in findings):
            appeals.append("Guideline 5.1.1(v) Appeal: Demonstrate account deletion flow directly in App Review Notes with test account.")
        if any(f.pattern_id == "APPLE-PRIVACY-MANIFEST-MISSING" for f in findings):
            appeals.append("Privacy Manifest Gate: Apple requires NSPrivacyAccessedAPITypes in PrivacyInfo.xcprivacy for all App Store submissions.")

        return ComplianceReport(
            is_compliant=is_compliant,
            score=final_score,
            total_files_scanned=files_scanned,
            critical_count=critical_c,
            high_count=high_c,
            medium_count=medium_c,
            low_count=low_c,
            findings=findings,
            appeal_recommendations=appeals,
        )


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    report = AppStoreComplianceAuditor.audit_project(target)
    print(json.dumps(report.to_dict(), indent=2))
