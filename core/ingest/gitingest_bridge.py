# Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea
# Gitingest Codebase Digestion & Prompt Optimization Engine
# Powered by coderamp-labs/gitingest

from __future__ import annotations
import os
import sys
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("supreme.ingest")

class GitingestBridge:
    """
    Ingests any local directory or GitHub repository into a prompt-friendly markdown format
    with ASCII file tree, token statistics, and filtered file contents for LLMs.
    """

    @staticmethod
    def is_available() -> bool:
        try:
            import gitingest
            return True
        except ImportError:
            return False

    @classmethod
    def ingest_path(
        cls,
        path: str,
        max_file_size: int = 10 * 1024 * 1024,
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        token_budget: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Ingests a local directory path or remote Git URL.
        Returns a dict containing summary, tree, content, and token counts.
        """
        if not cls.is_available():
            raise RuntimeError("gitingest package is not installed. Run: pip install gitingest")

        import gitingest

        resolved_path = os.path.abspath(os.path.expanduser(path)) if not path.startswith("http") else path

        # Set default exclusions if none provided
        default_excludes = [
            "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico", "*.pdf", "*.zip", "*.tar.gz",
            "*.pyc", "__pycache__", ".git", ".build", "DerivedData", "node_modules",
            "*.dylib", "*.so", "*.a", "*.o", "*.bin", "*.lock", "package-lock.json"
        ]
        if exclude_patterns:
            default_excludes.extend(exclude_patterns)

        try:
            summary, tree, content = gitingest.ingest(
                resolved_path,
                max_file_size=max_file_size,
                exclude_patterns=set(default_excludes),
                include_patterns=set(include_patterns) if include_patterns else None,
            )
        except Exception as e:
            logger.error(f"Failed to ingest path {resolved_path}: {e}")
            raise

        # Calculate or parse estimated tokens
        estimated_tokens = 0
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            estimated_tokens = len(enc.encode(content))
        except Exception:
            # Fallback estimation (approx 4 chars per token)
            estimated_tokens = len(content) // 4

        is_truncated = False
        if token_budget and estimated_tokens > token_budget:
            # Smart truncation preserving tree and prioritizing first chunks
            is_truncated = True
            logger.warning(f"Digest ({estimated_tokens} tokens) exceeds budget ({token_budget} tokens). Truncating.")
            lines = content.splitlines()
            budget_chars = token_budget * 4
            running_chars = 0
            truncated_lines = []
            for line in lines:
                if running_chars + len(line) > budget_chars:
                    truncated_lines.append("\n... [REMAINDER OF DIGEST TRUNCATED TO FIT CONTEXT BUDGET] ...")
                    break
                truncated_lines.append(line)
                running_chars += len(line) + 1
            content = "\n".join(truncated_lines)
            estimated_tokens = token_budget

        return {
            "source": resolved_path,
            "summary": summary,
            "tree": tree,
            "content": content,
            "estimated_tokens": estimated_tokens,
            "is_truncated": is_truncated,
            "success": True,
        }

    @classmethod
    def get_tree_only(cls, path: str) -> str:
        """Extracts only the directory tree without full file content."""
        res = cls.ingest_path(path)
        return res.get("tree", "")

    @classmethod
    def save_to_mempalace(
        cls,
        ingest_result: Dict[str, Any],
        room: str = "codebase_maps",
        agent_name: str = "Harness-Suprem-Ingestor"
    ) -> bool:
        """
        Persists repository structure and key summary into MemPalace
        so the agent retains architectural memory across sessions.
        """
        try:
            from core.memory import MemPalaceBridge
            source = ingest_result.get("source", "unknown")
            tokens = ingest_result.get("estimated_tokens", 0)
            tree = ingest_result.get("tree", "")
            summary = ingest_result.get("summary", "")

            entry_content = (
                f"### Codebase Digest: {source}\n"
                f"- Analyzed Tokens: {tokens}\n"
                f"- Summary: {summary}\n\n"
                f"#### Directory Architecture:\n```\n{tree[:2000]}\n```"
            )
            return MemPalaceBridge.append_diary(agent=agent_name, entry=entry_content)
        except Exception as e:
            logger.warning(f"Could not persist ingest to MemPalace: {e}")
            return False
