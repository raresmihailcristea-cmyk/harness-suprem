#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Better Harness (QoderAI) 5-Dimension Work Loop Data Models

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Dict, List, Optional

class EvidenceState(str, Enum):
    PRESENT = "Present"                   # Mechanism or contract exists in repo
    WIRED = "Wired"                       # Reachable by configured route or task
    EXERCISED = "Exercised"               # Actually invoked with retained result
    OUTCOME_SUPPORTED = "Outcome-supported"# Observed subsequent beneficial effect
    MISSING = "Missing"                   # Confirmed absent when required
    UNOBSERVED = "Unobserved"             # Available data cannot decide
    NOT_APPLICABLE = "Not applicable"     # Clearly not relevant to this task

class DimensionId(str, Enum):
    TASK_UNDERSTANDING = "task-understanding"
    CONTROLLED_EXECUTION = "controlled-execution"
    CHANGE_VALIDATION = "change-validation"
    RELIABLE_DELIVERY = "reliable-delivery"
    LEARNING_CAPTURE = "learning-capture"

@dataclass
class CheckResult:
    check_id: str
    name: str
    dimension_id: DimensionId
    state: EvidenceState
    summary: str
    evidence: List[str] = field(default_factory=list)

@dataclass
class DimensionEvaluation:
    dimension_id: DimensionId
    name: str
    question: str
    score: float  # 0.0 to 100.0
    checks: List[CheckResult] = field(default_factory=list)

@dataclass
class Finding:
    finding_id: str
    title: str
    dimension_id: DimensionId
    severity: str  # "High", "Medium", "Low"
    impact: str
    expected_output: str
    scoped_ai_fix: str
    acceptance_checks: List[str] = field(default_factory=list)

@dataclass
class TaskEpisode:
    episode_id: str
    goal: str
    prompts: List[str] = field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    code_diff: str = ""
    test_results: Dict[str, Any] = field(default_factory=dict)
    git_commits: List[str] = field(default_factory=list)

@dataclass
class AuditReport:
    report_id: str
    timestamp: float
    episode_id: str
    overall_score: float
    dimensions: Dict[str, DimensionEvaluation] = field(default_factory=dict)
    findings: List[Finding] = field(default_factory=list)
    summary: str = ""
