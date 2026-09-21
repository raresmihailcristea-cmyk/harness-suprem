# Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea
# ECC (Enterprise Codebase Context & Agent Harness Operating System)
# Powered by AFFAAN-M/ECC architecture (https://github.com/AFFAAN-M/ECC)

from __future__ import annotations
import enum
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("supreme.ecc")

class ECCStage(str, enum.Enum):
    PLAN = "plan"
    TEST = "test"
    IMPLEMENT = "implement"
    REVIEW = "review"
    VERIFY = "verify"
    REMEMBER = "remember"

class ECCLifecycleManager:
    """
    Orchestrates the ECC engineering cycle:
    plan -> test -> implement -> review -> verify -> remember -> improve
    """

    ORDERED_STAGES = [
        ECCStage.PLAN,
        ECCStage.TEST,
        ECCStage.IMPLEMENT,
        ECCStage.REVIEW,
        ECCStage.VERIFY,
        ECCStage.REMEMBER,
    ]

    def __init__(self, task_name: str = "default_task"):
        self.task_name = task_name
        self.current_stage: ECCStage = ECCStage.PLAN
        self.stage_artifacts: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []

    def record_stage(self, stage: ECCStage, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Records work done in the current stage and advances the lifecycle."""
        record = {
            "stage": stage.value,
            "content": content,
            "metadata": metadata or {},
        }
        self.stage_artifacts[stage.value] = record
        self.history.append(record)

        # If reaching remember stage, persist to MemPalace
        if stage == ECCStage.REMEMBER:
            try:
                from core.memory import MemPalaceBridge
                MemPalaceBridge.append_diary(
                    agent=f"ECC-Orchestrator[{self.task_name}]",
                    entry=f"Completed ECC Cycle for {self.task_name}.\nKey Learnings:\n{content}"
                )
            except Exception as e:
                logger.warning(f"Could not persist ECC learnings to MemPalace: {e}")

        # Transition to next stage if available
        curr_idx = self.ORDERED_STAGES.index(stage)
        if curr_idx < len(self.ORDERED_STAGES) - 1:
            self.current_stage = self.ORDERED_STAGES[curr_idx + 1]
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "task_name": self.task_name,
            "current_stage": self.current_stage.value,
            "completed_stages": list(self.stage_artifacts.keys()),
            "total_stages": len(self.ORDERED_STAGES),
            "is_completed": ECCStage.REMEMBER.value in self.stage_artifacts,
        }


class ContextBudgetManager:
    """
    Monitors context window pressure for local models (Qwen3.6-35B at 32k/64k/128k context)
    and signals when to compact, chunk, or invoke Context AutoReset.
    """

    def __init__(self, context_limit: int = 32768):
        self.context_limit = context_limit

    def evaluate_pressure(self, current_tokens: int) -> Dict[str, Any]:
        usage_pct = (current_tokens / self.context_limit) * 100.0

        if usage_pct < 60.0:
            status = "HEALTHY"
            color = "GREEN"
            action = "none"
        elif usage_pct < 80.0:
            status = "MODERATE"
            color = "YELLOW"
            action = "monitor"
        elif usage_pct < 90.0:
            status = "HIGH"
            color = "ORANGE"
            action = "compress_prompt_or_archive"
        else:
            status = "CRITICAL"
            color = "RED"
            action = "trigger_autoreset"

        return {
            "current_tokens": current_tokens,
            "context_limit": self.context_limit,
            "usage_pct": round(usage_pct, 2),
            "status": status,
            "indicator": color,
            "recommended_action": action,
            "requires_autoreset": usage_pct >= 90.0,
        }


class AgentShieldScanner:
    """
    Security & integrity scanner inspired by ECC AgentShield.
    Detects secret leaks, command injections, and harmful prompt patterns.
    """

    SECRET_PATTERNS = [
        (re.compile(r"(sk-[a-zA-Z0-9]{20,})"), "OpenAI Secret Key"),
        (re.compile(r"(ghp_[a-zA-Z0-9]{36})"), "GitHub Personal Access Token"),
        (re.compile(r"(xox[baprs]-[0-9a-zA-Z]{10,48})"), "Slack Token"),
        (re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"), "Private Cryptographic Key"),
        (re.compile(r"AuthKey_[A-Z0-9]{10}\.p8"), "Apple StoreKit Private Key File Reference"),
    ]

    DANGEROUS_PATTERNS = [
        (re.compile(r"rm\s+-rf\s+/(?:\s|$)"), "Catastrophic root filesystem deletion"),
        (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"), "Fork bomb pattern"),
        (re.compile(r">\s*/dev/sd[a-z]"), "Direct raw block device overwrite"),
    ]

    @classmethod
    def scan_content(cls, content: str) -> Dict[str, Any]:
        findings = []

        # Check secrets
        for pattern, label in cls.SECRET_PATTERNS:
            if pattern.search(content):
                findings.append({
                    "severity": "CRITICAL",
                    "category": "secret_leak",
                    "label": label,
                    "remediation": "Do not hardcode secret keys or API tokens in prompts or repository files.",
                })

        # Check dangerous system calls
        for pattern, label in cls.DANGEROUS_PATTERNS:
            if pattern.search(content):
                findings.append({
                    "severity": "FATAL",
                    "category": "malicious_command",
                    "label": label,
                    "remediation": "Execution blocked by AgentShield safety gate.",
                })

        return {
            "is_safe": len(findings) == 0,
            "total_findings": len(findings),
            "findings": findings,
        }
