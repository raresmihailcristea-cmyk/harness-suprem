#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Harness-Coder 1.3.3 Compliant Action Normalizer

from __future__ import annotations
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("core.resilience.normalizer")

TOOL_ALIASES = {
    "bash": "exec",
    "shell": "exec",
    "sh": "exec",
    "terminal": "exec",
    "run_command": "exec",
    "run_test": "test",
    "pytest": "test",
    "search": "grep",
    "find": "find_files",
    "modify_file": "edit",
    "patch": "edit",
}

class ActionNormalizer:
    """Normalizes noisy, wrapped, or markdown-embedded model action responses into canonical action dictionaries."""

    @staticmethod
    def extract_json(raw_text: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON object from text that may contain markdown fences or surrounding chatter."""
        if not raw_text or not raw_text.strip():
            return None

        text = raw_text.strip()

        # 1. Try direct parse first
        try:
            val = json.loads(text)
            if isinstance(val, dict):
                return val
        except Exception:
            pass

        # 2. Extract from markdown code fences ```json ... ``` or ``` ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if fence_match:
            try:
                val = json.loads(fence_match.group(1).strip())
                if isinstance(val, dict):
                    return val
            except Exception:
                pass

        # 3. Find outermost matching braces { ... }
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            substring = text[start_idx : end_idx + 1]
            try:
                val = json.loads(substring)
                if isinstance(val, dict):
                    return val
            except Exception:
                pass

        return None

    @classmethod
    def normalize_action(cls, raw_payload: Any) -> Dict[str, Any]:
        """Normalizes action payload by unwrapping envelopes and standardizing tool names and arguments."""
        if isinstance(raw_payload, str):
            extracted = cls.extract_json(raw_payload)
            if not extracted:
                return {"tool": "raw_response", "args": {"content": raw_payload}, "valid": False}
            data = extracted
        elif isinstance(raw_payload, dict):
            data = raw_payload.copy()
        else:
            return {"tool": "unknown", "args": {}, "valid": False}

        # Unwrap nested wrappers
        for wrap_key in ["next_action", "model_action", "decision", "action"]:
            if wrap_key in data and isinstance(data[wrap_key], dict):
                data = data[wrap_key]

        # Extract tool name from multiple possible keys
        tool_name = (
            data.get("tool")
            or data.get("tool_name")
            or data.get("name")
            or data.get("kind")
            or data.get("type")
            or "exec"
        )
        normalized_tool = TOOL_ALIASES.get(str(tool_name).lower(), str(tool_name))

        # Extract arguments from multiple formats
        raw_args = data.get("args") or data.get("arguments") or data.get("parameters") or {}
        if isinstance(raw_args, str):
            # If string argument for command-like tool
            if normalized_tool == "exec":
                args = {"command": raw_args}
            else:
                try:
                    args = json.loads(raw_args)
                except Exception:
                    args = {"input": raw_args}
        elif isinstance(raw_args, dict):
            args = raw_args
        else:
            args = {"value": raw_args}

        return {
            "tool": normalized_tool,
            "args": args,
            "valid": True,
            "original_tool": str(tool_name),
        }
