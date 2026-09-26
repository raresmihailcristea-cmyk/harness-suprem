# Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea
# Organic-Driven Development (ODD) Workflow Engine (Gentleman-Programming/gentle-ai & gentle-shell)
# Keeps small work lightweight and keeps substantial work recoverable with TDD evidence and Engram sync.

from __future__ import annotations
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ODDTaskScope(str, Enum):
    LIGHTWEIGHT = "LIGHTWEIGHT"      # Direct execution, no planning overhead, instant verification
    SUBSTANTIAL = "SUBSTANTIAL"      # Recoverable feature record, architectural decisions, strict TDD gate


@dataclass
class ODDFeatureRecord:
    feature_id: str
    name: str
    goal: str
    status: str = "IN_PROGRESS"      # "PLANNING", "IN_PROGRESS", "VERIFIED", "COMPLETED"
    decisions: List[Dict[str, str]] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)
    tdd_evidence: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_markdown(self) -> str:
        decisions_md = "\n".join(
            f"- **{d.get('decision')}**: {d.get('reason')} *(topic: `{d.get('topic_key', 'general')}`)*"
            for d in self.decisions
        ) if self.decisions else "- No architectural decisions recorded."

        files_md = "\n".join(f"- `{f}`" for f in self.files_changed) if self.files_changed else "- None yet."

        tdd_status = "✅ PASSED" if self.tdd_evidence.get("passed") else "⏳ PENDING / NOT RUN"
        tdd_detail = self.tdd_evidence.get("summary", "No test run recorded.")

        return (
            f"# ODD Feature Record: {self.name}\n\n"
            f"> **ID**: `{self.feature_id}` | **Status**: `{self.status}`\n\n"
            f"## Goal\n{self.goal}\n\n"
            f"## Key Architectural Decisions\n{decisions_md}\n\n"
            f"## Files Touched\n{files_md}\n\n"
            f"## TDD Evidence Gate\n- **Status**: {tdd_status}\n- **Detail**: {tdd_detail}\n"
        )


class ODDWorkflowEngine:
    """
    Organic-Driven Development (ODD) governor for Harness-Suprem.
    Avoids planning ceremony for small tasks; creates recoverable audit state for substantial tasks.
    """

    LIGHTWEIGHT_PATTERNS = [
        r'\b(typo|rename|format|lint|comment|log|readme|doc|small fix|quick fix)\b',
        r'\b(run|executa|testeaza|test|status|git status|commit|check|version)\b',
        r'\b(afiseaza|vezi|citeste|read|inspect|cat|ls|show|display)\b'
    ]

    SUBSTANTIAL_PATTERNS = [
        r'\b(arhitectura|architecture|refactor|redesign|migration|migrare|schema)\b',
        r'\b(new feature|modul nou|pipeline|full stack|security|concurrency|deadlock)\b',
        r'\b(engram|mcp|system1|laya|expo|eas|storekit|monetization|distribution)\b'
    ]

    @classmethod
    def classify_scope(cls, prompt: str) -> Tuple[ODDTaskScope, str, float]:
        """
        Classifies incoming prompt into LIGHTWEIGHT or SUBSTANTIAL with reasoning and score.
        """
        p_lower = prompt.lower()
        word_count = len(prompt.split())

        light_matches = sum(1 for pat in cls.LIGHTWEIGHT_PATTERNS if re.search(pat, p_lower))
        sub_matches = sum(1 for pat in cls.SUBSTANTIAL_PATTERNS if re.search(pat, p_lower))

        # Base score from 0.0 (trivial) to 1.0 (deeply substantial)
        score = 0.35
        if word_count > 80:
            score += 0.25
        elif word_count < 15:
            score -= 0.15

        score += (sub_matches * 0.25) - (light_matches * 0.20)
        score = max(0.05, min(0.98, score))

        if score >= 0.50 or sub_matches > light_matches:
            scope = ODDTaskScope.SUBSTANTIAL
            reason = f"Substantial scope detected (score={score:.2f}, {sub_matches} major patterns, {word_count} words)"
        else:
            scope = ODDTaskScope.LIGHTWEIGHT
            reason = f"Lightweight scope detected (score={score:.2f}, {light_matches} quick patterns) - no planning overhead needed"

        return scope, reason, score

    @classmethod
    def get_odd_dir(cls, project_dir: str = ".") -> str:
        odd_dir = os.path.join(os.path.abspath(project_dir), ".odd")
        os.makedirs(odd_dir, exist_ok=True)
        return odd_dir

    @classmethod
    def create_or_resume_feature(
        cls,
        feature_name: str,
        goal: str,
        project_dir: str = "."
    ) -> ODDFeatureRecord:
        """
        Creates or recovers a feature record in .odd/<feature_id>.json.
        """
        odd_dir = cls.get_odd_dir(project_dir)
        slug = re.sub(r'[^a-zA-Z0-9_-]', '', feature_name.lower().replace(" ", "-"))
        feature_id = f"feat-{slug}"

        record_file = os.path.join(odd_dir, f"{feature_id}.json")
        md_file = os.path.join(odd_dir, f"{feature_id}.md")

        if os.path.exists(record_file):
            try:
                with open(record_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                record = ODDFeatureRecord(**data)
                record.updated_at = time.time()
            except Exception:
                record = ODDFeatureRecord(feature_id=feature_id, name=feature_name, goal=goal)
        else:
            record = ODDFeatureRecord(feature_id=feature_id, name=feature_name, goal=goal)

        # Write state to disk
        with open(record_file, "w", encoding="utf-8") as f:
            json.dump(record.__dict__, f, indent=2)

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(record.to_markdown())

        return record

    @classmethod
    def record_decision(
        cls,
        feature_id: str,
        decision: str,
        reason: str,
        topic_key: Optional[str] = None,
        sync_to_engram: bool = True,
        project_dir: str = "."
    ) -> Dict[str, Any]:
        """
        Appends an architectural decision to the feature record and synchronizes to Engram.
        """
        odd_dir = cls.get_odd_dir(project_dir)
        record_file = os.path.join(odd_dir, f"{feature_id}.json")
        md_file = os.path.join(odd_dir, f"{feature_id}.md")

        if not os.path.exists(record_file):
            raise FileNotFoundError(f"Feature {feature_id} not found in {odd_dir}")

        with open(record_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        record = ODDFeatureRecord(**data)

        entry = {
            "decision": decision,
            "reason": reason,
            "topic_key": topic_key or f"odd/{feature_id}/decision",
            "timestamp": time.time()
        }
        record.decisions.append(entry)
        record.updated_at = time.time()

        with open(record_file, "w", encoding="utf-8") as f:
            json.dump(record.__dict__, f, indent=2)

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(record.to_markdown())

        engram_res = None
        if sync_to_engram:
            try:
                from core.memory.engram_bridge import EngramBridge
                if EngramBridge.is_available():
                    engram_res = EngramBridge.save_observation(
                        title=f"ODD [{record.name}]: {decision[:50]}",
                        content=f"**Decision**: {decision}\n**Reason**: {reason}\n**Feature**: {feature_id}",
                        type="decision",
                        topic_key=entry["topic_key"],
                        cwd=project_dir
                    )
            except Exception:
                pass

        return {
            "feature_id": feature_id,
            "decision": decision,
            "total_decisions": len(record.decisions),
            "engram_synced": engram_res is not None and engram_res.get("success", False)
        }

    @classmethod
    def verify_tdd_evidence(
        cls,
        test_command: str,
        feature_id: Optional[str] = None,
        project_dir: str = "."
    ) -> Dict[str, Any]:
        """
        Executes strict TDD validation and attaches evidence to the feature record.
        """
        t0 = time.perf_counter()
        proc = subprocess.run(
            test_command,
            shell=True,
            cwd=os.path.abspath(project_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120
        )
        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        passed = proc.returncode == 0
        summary = f"Command '{test_command}' exited {proc.returncode} in {duration_ms}ms"

        evidence = {
            "command": test_command,
            "passed": passed,
            "returncode": proc.returncode,
            "duration_ms": duration_ms,
            "summary": summary,
            "stdout_tail": proc.stdout[-500:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-500:] if proc.stderr else ""
        }

        if feature_id:
            odd_dir = cls.get_odd_dir(project_dir)
            record_file = os.path.join(odd_dir, f"{feature_id}.json")
            if os.path.exists(record_file):
                with open(record_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                record = ODDFeatureRecord(**data)
                record.tdd_evidence = evidence
                if passed:
                    record.status = "VERIFIED"
                record.updated_at = time.time()

                with open(record_file, "w", encoding="utf-8") as f:
                    json.dump(record.__dict__, f, indent=2)

                md_file = os.path.join(odd_dir, f"{feature_id}.md")
                with open(md_file, "w", encoding="utf-8") as f:
                    f.write(record.to_markdown())

        return evidence
