#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Secret Scrubber with Regex & Shannon Entropy Detection (AutoHarness)

from __future__ import annotations
import math
import re
from typing import Any, Dict, List, Tuple

class SecretScrubber:
    """Detects and redacts sensitive credentials, API keys, and high-entropy strings from agent payloads."""

    PATTERNS = {
        "OPENAI_KEY": re.compile(r"\bsk-[a-zA-Z0-9_\-]{24,}\b"),
        "ANTHROPIC_KEY": re.compile(r"\bsk-ant-[a-zA-Z0-9_\-]{24,}\b"),
        "GITHUB_TOKEN": re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b"),
        "AWS_ACCESS_KEY": re.compile(r"\b(AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b"),
        "PRIVATE_KEY": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
        "JWT_TOKEN": re.compile(r"\beyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b"),
        "GENERIC_ENV_SECRET": re.compile(r'(?i)(?:api_key|token|secret|password|passwd)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{16,})["\']?'),
    }

    @staticmethod
    def calculate_entropy(text: str) -> float:
        """Calculates Shannon entropy for string randomness detection."""
        if not text:
            return 0.0
        entropy = 0.0
        length = len(text)
        frequencies = {}
        for char in text:
            frequencies[char] = frequencies.get(char, 0) + 1
        for count in frequencies.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    @classmethod
    def scrub_text(cls, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Redacts known token signatures and high-entropy secrets from text."""
        if not text or not isinstance(text, str):
            return text, []

        redactions: List[Dict[str, Any]] = []
        scrubbed = text

        # 1. Regex Pattern Matching
        for pattern_name, pattern in cls.PATTERNS.items():
            for match in pattern.finditer(scrubbed):
                matched_val = match.group(0)
                # Avoid redacting already scrubbed placeholders
                if "[REDACTED_" in matched_val:
                    continue
                placeholder = f"[REDACTED_{pattern_name}]"
                redactions.append({
                    "type": pattern_name,
                    "entropy": round(cls.calculate_entropy(matched_val), 2),
                    "length": len(matched_val),
                })
                scrubbed = scrubbed.replace(matched_val, placeholder)

        # 2. Entropy Check on remaining candidate strings (long alphanumeric words)
        words = re.findall(r"\b[A-Za-z0-9+/=_\-]{20,}\b", scrubbed)
        for w in set(words):
            if "[REDACTED_" in w:
                continue
            ent = cls.calculate_entropy(w)
            # High-entropy threshold for random keys / hashes
            if ent > 4.3:
                placeholder = "[REDACTED_HIGH_ENTROPY_SECRET]"
                redactions.append({
                    "type": "HIGH_ENTROPY_SECRET",
                    "entropy": round(ent, 2),
                    "length": len(w),
                })
                scrubbed = scrubbed.replace(w, placeholder)

        return scrubbed, redactions

    @classmethod
    def scrub_payload(cls, payload: Any) -> Any:
        """Recursively scrubs secrets from dictionaries, lists, and primitives."""
        if isinstance(payload, str):
            clean_str, _ = cls.scrub_text(payload)
            return clean_str
        elif isinstance(payload, dict):
            return {k: cls.scrub_payload(v) for k, v in payload.items()}
        elif isinstance(payload, list):
            return [cls.scrub_payload(v) for v in payload]
        return payload
