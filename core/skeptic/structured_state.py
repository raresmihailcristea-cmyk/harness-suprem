#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Machine-Parseable JSON State & Task Plan Manager

from __future__ import annotations
from dataclasses import asdict, dataclass, field
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("core.skeptic.state")

@dataclass
class TaskItem:
    task_id: int
    title: str
    description: str
    acceptance_criteria: List[str]
    status: str = "pending"  # "pending", "in_progress", "completed", "failed"
    completed_at: Optional[float] = None
    commit_sha: Optional[str] = None

@dataclass
class PlanDocument:
    plan_id: str
    title: str
    summary: str
    created_at: float
    updated_at: float
    tasks: List[TaskItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class StructuredStateManager:
    """Manages durable JSON state (plans, progress, verdicts) that survives context window resets."""

    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        self.plans_dir = os.path.join(self.base_dir, "plans")
        self.verdicts_dir = os.path.join(self.base_dir, "eval_verdicts")
        os.makedirs(self.plans_dir, exist_ok=True)
        os.makedirs(self.verdicts_dir, exist_ok=True)

    def create_plan(self, plan_id: str, title: str, summary: str, tasks: List[Dict[str, Any]]) -> PlanDocument:
        now = time.time()
        task_items = [
            TaskItem(
                task_id=t.get("task_id", i + 1),
                title=t["title"],
                description=t.get("description", ""),
                acceptance_criteria=t.get("acceptance_criteria", []),
            )
            for i, t in enumerate(tasks)
        ]
        plan = PlanDocument(
            plan_id=plan_id,
            title=title,
            summary=summary,
            created_at=now,
            updated_at=now,
            tasks=task_items,
        )
        self.save_plan(plan)
        return plan

    def save_plan(self, plan: PlanDocument) -> str:
        plan.updated_at = time.time()
        file_path = os.path.join(self.plans_dir, f"{plan.plan_id}.json")
        data = asdict(plan)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return file_path

    def load_plan(self, plan_id: str) -> Optional[PlanDocument]:
        file_path = os.path.join(self.plans_dir, f"{plan_id}.json")
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tasks = [TaskItem(**t) for t in data.get("tasks", [])]
        data["tasks"] = tasks
        return PlanDocument(**data)

    def save_verdict(self, plan_id: str, verdict: Dict[str, Any]) -> str:
        verdict["timestamp"] = time.time()
        file_path = os.path.join(self.verdicts_dir, f"{plan_id}_verdict.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(verdict, f, indent=2)
        return file_path
