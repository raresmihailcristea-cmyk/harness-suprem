#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Supreme Plugin Manager & Registry for the 16 System Plugins + VeRO Integration

from __future__ import annotations
import json
import logging
import os
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("supreme.plugins")

class SupremePlugin:
    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category  # "provider", "execution", "interaction", "system", "memory"
        self.enabled = True

    @property
    def is_enabled(self) -> bool:
        return self.enabled

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "enabled": self.enabled,
        }

    def get_mcp_spec(self) -> Optional[Dict[str, Any]]:
        """Optional MCP server specification to expose this plugin as an MCP tool provider."""
        return None

    def initialize(self, context: Dict[str, Any]) -> bool:
        """Initialize plugin inside the container environment."""
        return True

    def run_conformance_check(self) -> bool:
        """VeRO conformance verification for this individual plugin."""
        return True


# -------------------------------------------------------------
# 1. Model & Provider Plugins (5 plugins)
# -------------------------------------------------------------
class AnthropicPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("anthropic", "Anthropic Claude model router & Claude Code execution bridge", "provider")

class OpenAIPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("openai", "OpenAI GPT-4o, o1, and o3 reasoning model connector", "provider")

class XAIPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("xai", "xAI Grok reasoning engine with real-time knowledge and fast decoding", "provider")

class NvidiaPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("nvidia", "NVIDIA NIM / Cloud provider supporting DeepSeek-V3 & DeepSeek-R1", "provider")

class OllamaPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("ollama", "Offline and air-gapped local model runner for zero-leakage enterprise execution", "provider")


# -------------------------------------------------------------
# 2. Execution, Code & Desktop Automation Plugins (3 plugins)
# -------------------------------------------------------------
class CodexPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("codex", "Advanced code transformation, AST parsing, test generation & smart patching", "execution")

class LinuxNodePlugin(SupremePlugin):
    def __init__(self):
        super().__init__("linux-node", "Container runtime supervisor, sandbox isolation, process management and metrics", "execution")

class CUAComputerPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("cua-computer", "Computer-Use Agent (CUA) for desktop automation, GUI interaction and OS input", "execution")


# -------------------------------------------------------------
# 3. Web, Artifacts & User Interaction Plugins (3 plugins)
# -------------------------------------------------------------
class BrowserPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("browser", "Headless browser automation, web search, DOM tree extraction and screenshots", "interaction")

class CanvasPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("canvas", "Generative UI renderer, live interactive component preview and visual canvas", "interaction")

class TalkVoicePlugin(SupremePlugin):
    def __init__(self):
        super().__init__("talk-voice", "Bidirectional voice streaming, speech-to-text audio ingestion and synthesis", "interaction")


# -------------------------------------------------------------
# 4. Networking, Synchronization & Discovery Plugins (3 plugins)
# -------------------------------------------------------------
class BonjourPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("bonjour", "mDNS / Zero-conf local service discovery for adjacent agent swarms and sidecars", "system")

class DevicePairPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("device-pair", "Secure cryptographic device pairing and multi-node worktree coordination", "system")

class FileTransferPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("file-transfer", "High-speed encrypted file synchronization and artifact staging between host and agent", "system")


# -------------------------------------------------------------
# 5. Context, Localization & Memory Plugins (2 plugins)
# -------------------------------------------------------------
class GeolocationPlugin(SupremePlugin):
    def __init__(self):
        super().__init__("geolocation", "Contextual localization, timezone normalization and geo-aware environmental presets", "memory")

class MemoryCorePlugin(SupremePlugin):
    def __init__(self):
        super().__init__("memory-core", "Persistent episodic and semantic memory with vector retrieval (MemPalace integration)", "memory")

    def get_wake_up_context(self, wing: Optional[str] = None, max_tokens: int = 800) -> str:
        from core.memory import MemPalaceBridge
        return MemPalaceBridge.get_wake_up_context(wing=wing, max_tokens=max_tokens)

    def search(self, query: str, wing: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        from core.memory import MemPalaceBridge
        return MemPalaceBridge.search_memory(query=query, wing=wing, limit=limit)

    def record_diary(self, agent: str, entry: str) -> bool:
        from core.memory import MemPalaceBridge
        return MemPalaceBridge.append_diary(agent=agent, entry=entry)

    def get_status(self) -> Dict[str, Any]:
        from core.memory import MemPalaceBridge
        return MemPalaceBridge.get_status()

# -------------------------------------------------------------
# 6. Apple Platform & Native Ecosystem Plugins
# -------------------------------------------------------------
class AppleDeveloperPlugin(SupremePlugin):
    def __init__(self):
        super().__init__(
            "apple-developer",
            "Apple native build system (Xcode/Swift 6), simctl, notarytool, HIG/a11y and App Store Review Compliance (mjmirza/app-store-compliance)",
            "platform"
        )

    def audit_compliance(self, target_dir: str = ".") -> Dict[str, Any]:
        """Runs the App Store pre-submission compliance audit."""
        from core.apple.app_store_compliance import AppStoreComplianceAuditor
        report = AppStoreComplianceAuditor.audit_project(target_dir)
        return report.to_dict()

    def audit_hig(self, target_dir: str = ".") -> Dict[str, Any]:
        from core.apple.hig_audit import HIGAccessibilityAuditor
        report = HIGAccessibilityAuditor.audit_directory(target_dir)
        return {
            "score": report.score,
            "total_files": report.total_files_scanned,
            "issues_count": len(report.issues),
            "issues": [
                {
                    "rule_id": iss.rule_id,
                    "severity": iss.severity,
                    "file": iss.file_path,
                    "message": iss.message,
                    "remediation": iss.remediation,
                }
                for iss in report.issues
            ]
        }

    def audit_concurrency(self, target_dir: str = ".") -> Dict[str, Any]:
        from core.apple.swift_concurrency_gate import SwiftConcurrencyGate
        res = SwiftConcurrencyGate.audit_directory(target_dir)
        return {
            "is_compliant": res.is_compliant,
            "total_files": res.total_files_scanned,
            "issues": res.issues_found,
            "swift_testing_suites": res.swift_testing_suites,
            "xctest_suites": res.xctest_suites,
        }

    def get_asc_credentials(self) -> Dict[str, Any]:
        """Returns App Store Connect API credentials for automated distribution."""
        return {
            "key_id": "9KRPNNB5X4",
            "issuer_id": "f01a396b-c350-4e06-b767-47e70e031e12",
            "key_path": os.path.expanduser("~/private_keys/AuthKey_9KRPNNB5X4.p8"),
            "team_id": "FD7Q764N23",
        }

    def generate_distribution_metadata(self, project_dir: str = ".", output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generates comprehensive App Store Connect distribution metadata in English."""
        from core.apple.app_store_distribution import AppStoreDistributionGenerator
        metadata, md = AppStoreDistributionGenerator.analyze_and_generate(project_dir, output_file=output_file)
        return {
            "app_name": metadata.app_name,
            "app_subtitle": metadata.app_subtitle,
            "bundle_id": metadata.bundle_id,
            "sku": metadata.sku,
            "apple_id": metadata.apple_id,
            "primary_category": metadata.primary_category,
            "promotional_text": metadata.promotional_text,
            "description": metadata.description,
            "keywords": metadata.keywords,
            "support_url": metadata.support_url,
            "marketing_url": metadata.marketing_url,
            "app_review_notes": metadata.app_review_notes,
            "app_encryption_doc": metadata.app_encryption_doc,
            "report_markdown": md
        }


class MonetizationIntelPlugin(SupremePlugin):
    def __init__(self):
        super().__init__(
            "app-monetization-intel",
            "App competitor pricing benchmark, marketing plan, In-App Purchases, Subscriptions & StoreKit 2 streamlined purchasing",
            "platform"
        )

    def analyze_monetization(self, project_dir: str = ".", output_file: Optional[str] = None) -> Dict[str, Any]:
        from core.apple.monetization_intel import CompetitorMonetizationAdvisor
        strategy, md = CompetitorMonetizationAdvisor.analyze_project_monetization(project_dir, output_file=output_file)
        return {
            "app_name": strategy.app_name,
            "category": strategy.category,
            "pricing_model": strategy.pricing_model,
            "marketing_plan": strategy.marketing_plan,
            "subscriptions": strategy.subscriptions,
            "in_app_purchases": strategy.in_app_purchases,
            "subscription_groups": strategy.subscription_groups,
            "billing_grace_period": strategy.billing_grace_period,
            "streamlined_purchasing": strategy.streamlined_purchasing,
            "report_markdown": md
        }


# -------------------------------------------------------------
# 7. Codebase Ingestion, Remote Docs & Agent OS (gitingest, git-mcp, ECC)
# -------------------------------------------------------------
class GitingestPlugin(SupremePlugin):
    def __init__(self):
        super().__init__(
            "repo-ingest",
            "Prompt-friendly codebase digestion, token estimation, and directory tree ingestion (coderamp-labs/gitingest)",
            "execution"
        )

    def ingest(self, path: str, token_budget: Optional[int] = None) -> Dict[str, Any]:
        from core.ingest import GitingestBridge
        return GitingestBridge.ingest_path(path, token_budget=token_budget)

    def get_tree(self, path: str) -> str:
        from core.ingest import GitingestBridge
        return GitingestBridge.get_tree_only(path)

    def persist_to_memory(self, path: str) -> bool:
        from core.ingest import GitingestBridge
        res = GitingestBridge.ingest_path(path)
        return GitingestBridge.save_to_mempalace(res)


class GitMCPPlugin(SupremePlugin):
    def __init__(self):
        super().__init__(
            "git-mcp",
            "Live GitHub documentation & code fetcher via GitMCP (idosal/git-mcp) eliminating hallucinations on cutting-edge APIs",
            "provider"
        )

    def fetch_docs(self, owner: str, repo: str, path: str = "README.md") -> Dict[str, Any]:
        from core.git_mcp import GitMCPBridge
        return GitMCPBridge.fetch_repo_docs(owner, repo, path)

    def get_mcp_config(self, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, Any]:
        from core.git_mcp import GitMCPBridge
        return GitMCPBridge.generate_lmstudio_mcp_config(owner, repo)

    def get_supported_catalogs(self) -> List[Dict[str, str]]:
        from core.git_mcp import GitMCPBridge
        return GitMCPBridge.get_supported_catalogs()


class ECCWorkflowPlugin(SupremePlugin):
    def __init__(self):
        super().__init__(
            "ecc-os",
            "Enterprise Codebase Context & Agent Harness OS workflow (AFFAAN-M/ECC) - plan -> test -> implement -> review -> verify -> remember",
            "system"
        )

    def create_lifecycle(self, task_name: str = "default_task"):
        from core.ecc import ECCLifecycleManager
        return ECCLifecycleManager(task_name=task_name)

    def evaluate_context_budget(self, current_tokens: int, limit: int = 32768) -> Dict[str, Any]:
        from core.ecc import ContextBudgetManager
        mgr = ContextBudgetManager(context_limit=limit)
        return mgr.evaluate_pressure(current_tokens)

    def scan_security(self, content: str) -> Dict[str, Any]:
        from core.ecc import AgentShieldScanner
        return AgentShieldScanner.scan_content(content)


class WorktreeFanoutPlugin(SupremePlugin):
    def __init__(self):
        super().__init__(
            "worktree-fanout",
            "Parallel Git worktree multi-agent fan-out orchestrator for simultaneous candidate execution (stablyai/orca)",
            "execution"
        )

    def dispatch(
        self,
        repo_path: str,
        agents: List[Dict[str, Any]],
        task_fn: Callable[[str, Any], None],
        test_command: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        from core.orchestration.worktree_fanout import WorktreeFanoutManager, FanoutAgentConfig
        mgr = WorktreeFanoutManager(repo_root=repo_path)
        configs = [
            FanoutAgentConfig(
                agent_id=a.get("agent_id", f"ag_{i}"),
                name=a.get("name", f"Agent {i}"),
                engine=a.get("engine", "mlx"),
                temperature=a.get("temperature", 0.2)
            )
            for i, a in enumerate(agents)
        ]
        results = mgr.dispatch_parallel(configs, task_fn, test_command=test_command)
        return [r.to_dict() for r in results]

    def merge_winner(self, repo_path: str, winner_id: str) -> bool:
        from core.orchestration.worktree_fanout import WorktreeFanoutManager
# -------------------------------------------------------------
# 8. System 1 Non-Autoregressive Decisions & Routing (Laya)
# -------------------------------------------------------------
class LayaFastRouterPlugin(SupremePlugin):
    def __init__(self):
        super().__init__(
            "laya-fast-router",
            "Non-autoregressive System 1 sub-35ms routing, prompt guardrails, and tool shortlisting (nandhakishorm/laya)",
            "system"
        )

    def route(self, prompt: str) -> Dict[str, Any]:
        from core.system1 import get_system1_engine
        engine = get_system1_engine()
        dec = engine.route_task(prompt)
        return {
            "target_tier": dec.target_tier,
            "recommended_model": dec.recommended_model,
            "confidence": dec.confidence,
            "complexity_score": dec.complexity_score,
            "latency_ms": dec.latency_ms,
            "language": dec.language,
            "script": dec.script,
            "reason": dec.reason
        }

    def guard(self, prompt: str) -> Dict[str, Any]:
        from core.system1 import get_system1_engine
        engine = get_system1_engine()
        verdict = engine.guard_prompt(prompt)
        return {
            "is_safe": verdict.is_safe,
            "risk_score": verdict.risk_score,
            "verdict": verdict.verdict,
            "flags": verdict.flags,
            "latency_ms": verdict.latency_ms,
            "reason": verdict.reason
        }

    def shortlist_tools(self, prompt: str, tools: List[Dict[str, Any]], k: int = 6) -> List[Dict[str, Any]]:
        from core.system1 import get_system1_engine
        engine = get_system1_engine()
        return engine.shortlist_tools(prompt, tools, k=k)

    def evaluate_decision(self, state: Any, question_schema: Dict[str, Any]) -> Dict[str, Any]:
        from core.system1 import get_system1_engine
        engine = get_system1_engine()
        res = engine.evaluate_typed_decision(state, question_schema)
        return {
            "primitive": res.primitive,
            "result": res.result,
            "confidence": res.confidence,
            "distribution": res.distribution,
            "latency_ms": res.latency_ms,
            "reason": res.reason
        }


# -------------------------------------------------------------
# 9. Universal Mobile Platform & App Scaffolding (Expo / expo)
# -------------------------------------------------------------
class ExpoUniversalPlugin(SupremePlugin):
    def __init__(self):
        super().__init__(
            "expo-universal-mobile",
            "Universal Mobile application platform, declarative Config Plugins, EAS dual-store build/submit and live QR Expo Go preview (expo/expo)",
            "platform"
        )

    def detect_project(self, path: str = ".") -> Dict[str, Any]:
        from core.expo import ExpoManager
        return ExpoManager.detect_project(path)

    def scaffold_app(
        self,
        target_dir: str,
        name: str,
        bundle_id: Optional[str] = None,
        package_name: Optional[str] = None,
        template: str = "tabs"
    ) -> Dict[str, Any]:
        from core.expo import ExpoManager
        return ExpoManager.scaffold_universal_app(
            target_dir=target_dir,
            name=name,
            bundle_id=bundle_id,
            package_name=package_name,
            template=template
        )

    def apply_plugin(self, project_dir: str, plugin_name: str, plugin_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from core.expo import ExpoManager
        return ExpoManager.apply_config_plugin(project_dir, plugin_name, plugin_options=plugin_options)

    def generate_eas(self, project_dir: str, apple_team_id: Optional[str] = "FD7Q764N23") -> Dict[str, Any]:
        from core.expo import ExpoManager
        return ExpoManager.generate_eas_config(project_dir, apple_team_id=apple_team_id)

    def get_dev_session(self, project_dir: str = ".", port: int = 8081, tunnel: bool = False) -> Dict[str, Any]:
        from core.expo import ExpoManager
        sess = ExpoManager.get_dev_session(project_dir, port=port, tunnel=tunnel)
        return {
            "url": sess.url,
            "exp_url": sess.exp_url,
            "qr_ascii": sess.qr_ascii,
            "port": sess.port,
            "host_ip": sess.host_ip,
            "deep_link": sess.deep_link
        }

    def doctor(self, project_dir: str = ".") -> Dict[str, Any]:
        from core.expo import ExpoManager
        rep = ExpoManager.run_doctor_audit(project_dir)
        return {
            "is_healthy": rep.is_healthy,
            "sdk_version": rep.sdk_version,
            "warnings": rep.warnings,
            "errors": rep.errors,
            "recommendations": rep.recommendations,
            "details": rep.details
        }


# -------------------------------------------------------------
# Central Registry
# -------------------------------------------------------------
ALL_PLUGINS = [
    AnthropicPlugin(),
    AppleDeveloperPlugin(),
    BonjourPlugin(),
    BrowserPlugin(),
    CanvasPlugin(),
    CodexPlugin(),
    CUAComputerPlugin(),
    DevicePairPlugin(),
    ECCWorkflowPlugin(),
    ExpoUniversalPlugin(),
    FileTransferPlugin(),
    GeolocationPlugin(),
    GitingestPlugin(),
    GitMCPPlugin(),
    LayaFastRouterPlugin(),
    LinuxNodePlugin(),
    MemoryCorePlugin(),
    MonetizationIntelPlugin(),
    NvidiaPlugin(),
    OllamaPlugin(),
    OpenAIPlugin(),
    TalkVoicePlugin(),
    WorktreeFanoutPlugin(),
    XAIPlugin(),
]

ALL_16_PLUGINS = ALL_PLUGINS  # Backwards compatibility alias

def get_plugin_catalog() -> List[Dict[str, Any]]:
    return [p.get_metadata() for p in ALL_PLUGINS]

def export_plugins_manifest(target_path: str) -> None:
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_plugins": len(ALL_PLUGINS),
            "plugins": {p.name: p.get_metadata() for p in ALL_PLUGINS},
            "vero_optimization_enabled": True
        }, f, indent=2)

class PluginManager:
    """Manager and registry interface for all Supreme Harness plugins."""
    def __init__(self):
        self.plugins: Dict[str, SupremePlugin] = {p.name: p for p in ALL_PLUGINS}

    def get_plugin(self, name: str) -> Optional[SupremePlugin]:
        return self.plugins.get(name)

    def list_plugins(self) -> List[SupremePlugin]:
        return list(self.plugins.values())

    def get_catalog(self) -> List[Dict[str, Any]]:
        return [p.get_metadata() for p in self.plugins.values()]

if __name__ == "__main__":
    print(f"Loaded Supreme Plugin Manager: {len(ALL_PLUGINS)} plugins ready.")
    for p in ALL_PLUGINS:
        print(f" - [{p.category.upper()}] {p.name}: {p.description}")
