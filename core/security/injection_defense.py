#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Prompt Injection Detector & Defense Layer (AutoHarness)

from __future__ import annotations
from enum import Enum
import re
from typing import Dict, List, Tuple

class InjectionRiskLevel(str, Enum):
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    BLOCKED = "BLOCKED"

class PromptInjectionDetector:
    """Pre-flight analyzer to detect prompt injection, jailbreak attempts, and instruction override attacks."""

    INJECTION_SIGNATURES = [
        (re.compile(r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|rules|commands)\b"), 1.0, "Ignore previous instructions override"),
        (re.compile(r"(?i)\bforget\s+(?:all\s+)?(?:previous|prior)\s+(?:context|instructions|rules)\b"), 0.9, "Forget previous context"),
        (re.compile(r"(?i)\b(?:system\s+prompt\s+override|override\s+system\s+instructions)\b"), 1.0, "Direct system prompt override"),
        (re.compile(r"(?i)\byou\s+are\s+now\s+(?:in\s+developer\s+mode|dan|unrestricted|jailbroken)\b"), 0.95, "Jailbreak mode declaration"),
        (re.compile(r"(?:<\|im_start\|>|<\|im_end\|>|\[INST\]|\[\/INST\]|<<SYS>>|<\/SYS>)"), 0.85, "ChatML/LLM delimiter injection"),
        (re.compile(r"(?i)\bdisregard\s+(?:safety|all\s+guardrails|content\s+policies)\b"), 0.9, "Disregard guardrails"),
        (re.compile(r"(?i)\bdo\s+anything\s+now\b"), 0.8, "DAN signature"),
        (re.compile(r"(?i)\breturn\s+your\s+(?:system\s+prompt|initial\s+instructions)\b"), 0.75, "System prompt extraction probe"),
    ]

    @classmethod
    def scan_text(cls, text: str) -> Tuple[InjectionRiskLevel, float, List[Dict[str, str]]]:
        """Scans input string for prompt-injection markers and returns risk level, max score, and match details."""
        if not text or not isinstance(text, str):
            return InjectionRiskLevel.SAFE, 0.0, []

        matches = []
        max_score = 0.0

        for pattern, weight, description in cls.INJECTION_SIGNATURES:
            if pattern.search(text):
                matches.append({"description": description, "weight": str(weight)})
                if weight > max_score:
                    max_score = weight

        if max_score >= 0.9:
            risk = InjectionRiskLevel.BLOCKED
        elif max_score >= 0.7:
            risk = InjectionRiskLevel.SUSPICIOUS
        else:
            risk = InjectionRiskLevel.SAFE

        return risk, max_score, matches
