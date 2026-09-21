#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Security Governor & Tool Approval Pipeline (AutoHarness)

from __future__ import annotations
import logging
import re
from typing import Any, Dict, Optional, Tuple

from .injection_defense import InjectionRiskLevel, PromptInjectionDetector
from .secret_scrubber import SecretScrubber

logger = logging.getLogger("core.security.governor")

class SecurityGovernor:
    """Centralized safety pipeline governing tool calls, prompt submissions, and credential security."""

    CRITICAL_DESTRUCTIVE_PATTERNS = [
        re.compile(r"(?i)\brm\s+-(?:r|f|rf|fr)\s+(?:/|\*|~|/\w+)\b"),
        re.compile(r"(?i)\bmkfs\b"),
        re.compile(r"(?i)\bdd\s+if="),
        re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"),  # Fork bomb
        re.compile(r"(?i)\bchmod\s+-(?:r|R)\s+777\s+(?:/|/etc|/var|/usr)\b"),
        re.compile(r"(?i)\bcurl\b.*\|\s*(?:bash|sh)\b"),          # Pipe to shell
        re.compile(r"(?i)\bwget\b.*\|\s*(?:bash|sh)\b"),
        re.compile(r"(?i)\bgit\s+push\b.*--force\b"),
    ]

    def __init__(self, block_injections: bool = True, scrub_credentials: bool = True):
        self.block_injections = block_injections
        self.scrub_credentials = scrub_credentials

    def inspect_prompt(self, user_prompt: str) -> Dict[str, Any]:
        """Scans incoming prompt for injection attacks and scrubs accidental secret pastes."""
        risk, score, matches = PromptInjectionDetector.scan_text(user_prompt)
        scrubbed_prompt, redactions = SecretScrubber.scrub_text(user_prompt) if self.scrub_credentials else (user_prompt, [])

        allowed = True
        reason = "OK"

        if self.block_injections and risk == InjectionRiskLevel.BLOCKED:
            allowed = False
            reason = f"Blocked by Prompt Injection Defense: {matches[0]['description'] if matches else 'High risk'}"

        return {
            "allowed": allowed,
            "risk_level": risk.value,
            "risk_score": score,
            "matches": matches,
            "redactions_count": len(redactions),
            "sanitized_prompt": scrubbed_prompt,
            "reason": reason,
        }

    def inspect_tool_execution(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates whether a tool invocation complies with security policies."""
        # 1. Scrub secrets in tool arguments
        sanitized_args = SecretScrubber.scrub_payload(arguments) if self.scrub_credentials else arguments

        # 2. Check for destructive shell commands
        if tool_name in ("exec", "bash", "shell", "run_command"):
            cmd = sanitized_args.get("command", "") or sanitized_args.get("cmd", "") or sanitized_args.get("CommandLine", "")
            if isinstance(cmd, str):
                for pat in self.CRITICAL_DESTRUCTIVE_PATTERNS:
                    if pat.search(cmd):
                        return {
                            "allowed": False,
                            "reason": f"Execution blocked: Critical destructive command pattern detected in '{cmd[:60]}'",
                            "sanitized_arguments": sanitized_args,
                        }

        return {
            "allowed": True,
            "reason": "Permitted",
            "sanitized_arguments": sanitized_args,
        }
