#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Apple Platform Specialization Package for Supreme Harness
# Built on Apple Developer Documentation & App Store Compliance Guidelines (Swift 6, Xcode 16/27, simctl, notarytool, HIG, Review Guidelines)

from .build_system import XcodeBuilder, XCResultParser, Diagnostic, BuildResult
from .simulator_manager import SimulatorManager, SimulatorDevice
from .notarization import NotaryPipeline, CodeSignStatus
from .swift_concurrency_gate import SwiftConcurrencyGate, ConcurrencyAuditResult
from .hig_audit import HIGAccessibilityAuditor, HIGAuditReport, HIGIssue
from .app_store_compliance import AppStoreComplianceAuditor, ComplianceReport, ComplianceFinding
from .app_store_distribution import AppStoreDistributionGenerator, AppStoreMetadata
from .monetization_intel import CompetitorMonetizationAdvisor, MonetizationStrategy

__all__ = [
    "XcodeBuilder",
    "XCResultParser",
    "Diagnostic",
    "BuildResult",
    "SimulatorManager",
    "SimulatorDevice",
    "NotaryPipeline",
    "CodeSignStatus",
    "SwiftConcurrencyGate",
    "ConcurrencyAuditResult",
    "HIGAccessibilityAuditor",
    "HIGAuditReport",
    "HIGIssue",
    "AppStoreComplianceAuditor",
    "ComplianceReport",
    "ComplianceFinding",
    "AppStoreDistributionGenerator",
    "AppStoreMetadata",
    "CompetitorMonetizationAdvisor",
    "MonetizationStrategy",
]
