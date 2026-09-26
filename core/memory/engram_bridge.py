# Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea
# Engram Persistent Memory Bridge for Harness-Suprem & LM Studio
# High-speed SQLite + FTS5 full-text search, topic-key deduplication, and session summaries (Gentleman-Programming/engram).

from __future__ import annotations
import json
import logging
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("core.memory.engram")


@dataclass
class EngramObservation:
    id: Optional[int]
    title: str
    content: str
    type: str = "decision"
    topic_key: Optional[str] = None
    project: Optional[str] = None
    scope: str = "project"
    created_at: Optional[str] = None


@dataclass
class EngramSessionSummary:
    goal: str
    instructions: str = ""
    discoveries: List[str] = field(default_factory=list)
    accomplished: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    relevant_files: List[str] = field(default_factory=list)

    def format_markdown(self) -> str:
        disc = "\n".join(f"- {d}" for d in self.discoveries) if self.discoveries else "- None"
        acc = "\n".join(f"- {a}" for a in self.accomplished) if self.accomplished else "- In progress"
        next_s = "\n".join(f"- {n}" for n in self.next_steps) if self.next_steps else "- None"
        files = "\n".join(f"- {f}" for f in self.relevant_files) if self.relevant_files else "- None"

        return (
            f"## Goal\n{self.goal}\n\n"
            f"## Instructions\n{self.instructions or 'Standard autonomous execution.'}\n\n"
            f"## Discoveries\n{disc}\n\n"
            f"## Accomplished\n{acc}\n\n"
            f"## Next Steps\n{next_s}\n\n"
            f"## Relevant Files\n{files}\n"
        )


class EngramBridge:
    """
    Programmatic interface to the native Engram CLI binary (~/.local/bin/engram).
    Provides zero-leakage, persistent SQLite+FTS5 project memory across agent sessions.
    """

    DEFAULT_BINARY = "/Users/rarescristea/.local/bin/engram"

    @classmethod
    def get_binary_path(cls) -> str:
        if os.path.exists(cls.DEFAULT_BINARY):
            return cls.DEFAULT_BINARY
        which_path = shutil.which("engram")
        return which_path or cls.DEFAULT_BINARY

    @classmethod
    def is_available(cls) -> bool:
        bin_path = cls.get_binary_path()
        return bool(bin_path and os.path.exists(bin_path) and os.access(bin_path, os.X_OK))

    @classmethod
    def run_cmd(cls, args: List[str], cwd: Optional[str] = None, timeout: int = 15) -> Tuple[int, str, str]:
        bin_path = cls.get_binary_path()
        if not os.path.exists(bin_path):
            raise FileNotFoundError(f"Engram binary not found at {bin_path}")

        cmd = [bin_path] + args
        try:
            res = subprocess.run(
                cmd,
                cwd=cwd or os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return 124, "", "Engram process timed out"
        except Exception as e:
            return 1, "", str(e)

    @classmethod
    def init_project(cls, project_name: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Initializes an Engram project (.engram/config.json)."""
        ret, stdout, stderr = cls.run_cmd(["init", project_name, "--force"], cwd=cwd)
        return {
            "success": ret == 0,
            "project": project_name,
            "stdout": stdout.strip(),
            "stderr": stderr.strip()
        }

    @classmethod
    def save_observation(
        cls,
        title: str,
        content: str,
        type: str = "decision",
        topic_key: Optional[str] = None,
        project: Optional[str] = None,
        scope: str = "project",
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Saves a structured observation into Engram SQLite DB.
        If topic_key is provided, subsequent saves to this topic update the memory gracefully.
        """
        args = ["save", title, content, "--type", type, "--scope", scope]
        if topic_key:
            args.extend(["--topic", topic_key])
        if project:
            args.extend(["--project", project])

        ret, stdout, stderr = cls.run_cmd(args, cwd=cwd)
        # Parse memory ID if present in output
        mem_id = None
        match = re.search(r'#(\d+)', stdout)
        if match:
            mem_id = int(match.group(1))

        return {
            "success": ret == 0,
            "id": mem_id,
            "title": title,
            "type": type,
            "topic_key": topic_key,
            "project": project,
            "stdout": stdout.strip(),
            "stderr": stderr.strip()
        }

    @classmethod
    def search_memory(
        cls,
        query: str,
        project: Optional[str] = None,
        all_projects: bool = False,
        limit: int = 10,
        type_filter: Optional[str] = None,
        cwd: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Full-text lexical search using Engram's SQLite FTS5 engine.
        Returns candidate memories matching the query.
        """
        args = ["search", query]
        if all_projects:
            args.append("--all")
        elif project:
            args.extend(["--project", project])

        ret, stdout, stderr = cls.run_cmd(args, cwd=cwd)
        if ret != 0:
            logger.warning(f"Engram search error: {stderr}")
            return []

        results = []
        # Pattern match memories: [1] #1 (type) — Title \n Content \n Date | project: ...
        blocks = re.split(r'\n(?=\[\d+\]\s+#\d+)', stdout)
        for b in blocks:
            header_match = re.search(r'\[\d+\]\s+#(\d+)\s+\(([^)]+)\)\s+[—\-]\s+(.+)', b)
            if header_match:
                obs_id = int(header_match.group(1))
                obs_type = header_match.group(2).strip()
                title = header_match.group(3).strip()

                lines = b.splitlines()
                body = lines[1].strip() if len(lines) > 1 else ""
                meta = lines[2].strip() if len(lines) > 2 else ""

                if type_filter and obs_type.lower() != type_filter.lower():
                    continue

                results.append({
                    "id": obs_id,
                    "type": obs_type,
                    "title": title,
                    "content": body,
                    "meta": meta
                })

        return results[:limit]

    @classmethod
    def save_session_summary(
        cls,
        summary: EngramSessionSummary,
        project: Optional[str] = None,
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Saves a structured end-of-session summary (Goal, Instructions, Discoveries, Accomplished, Next Steps, Files).
        """
        md_content = summary.format_markdown()
        title = f"Session Summary: {summary.goal[:60]}"
        return cls.save_observation(
            title=title,
            content=md_content,
            type="session_summary",
            topic_key="session/latest-summary",
            project=project,
            cwd=cwd
        )

    @classmethod
    def get_context(cls, project: Optional[str] = None, cwd: Optional[str] = None) -> str:
        """Retrieves recent session context and durable memories for orientation."""
        args = ["context"]
        if project:
            args.extend(["--project", project])
        else:
            args.append("--all")

        ret, stdout, stderr = cls.run_cmd(args, cwd=cwd)
        return stdout.strip() if ret == 0 else ""

    @classmethod
    def get_stats(cls, project: Optional[str] = None, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Returns statistics on stored memories and sessions."""
        args = ["stats"]
        if project:
            args.extend(["--project", project])
        else:
            args.append("--all")

        ret, stdout, stderr = cls.run_cmd(args, cwd=cwd)
        return {
            "success": ret == 0,
            "raw": stdout.strip()
        }

    @classmethod
    def run_doctor(cls, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Runs read-only diagnostics on the local SQLite DB."""
        ret, stdout, stderr = cls.run_cmd(["doctor", "--json"], cwd=cwd)
        if ret == 0:
            try:
                return json.loads(stdout)
            except Exception:
                pass
        return {"status": "ok" if ret == 0 else "error", "output": stdout.strip(), "stderr": stderr.strip()}
