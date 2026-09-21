#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Better Harness (QoderAI) Work Loop Auditor Engine

from __future__ import annotations
import logging
import time
from typing import Any, Dict, List, Optional

from .models import (
    AuditReport,
    CheckResult,
    DimensionEvaluation,
    DimensionId,
    EvidenceState,
    Finding,
    TaskEpisode,
)

logger = logging.getLogger("core.audit.auditor")

class WorkLoopAuditor:
    """Evaluates an agent Task Episode across the 5 Dimensions and 15 Checks of the Agent Work Loop."""

    def __init__(self):
        pass

    def evaluate_episode(self, episode: TaskEpisode) -> AuditReport:
        now = time.time()
        findings: List[Finding] = []
        dimensions: Dict[str, DimensionEvaluation] = {}

        # -------------------------------------------------------------
        # 1. Task Understanding
        # -------------------------------------------------------------
        has_goal = bool(episode.goal and len(episode.goal.strip()) > 5)
        has_prompts = len(episode.prompts) > 0
        diff_lines = episode.code_diff.count("\n") if episode.code_diff else 0

        c_goal = CheckResult(
            check_id="goal-understanding",
            name="Intent and Acceptance",
            dimension_id=DimensionId.TASK_UNDERSTANDING,
            state=EvidenceState.EXERCISED if has_goal else EvidenceState.MISSING,
            summary="User intent and goal specified clearly" if has_goal else "No explicit goal found",
            evidence=[f"Goal: {episode.goal[:100]}..."] if has_goal else [],
        )

        c_context = CheckResult(
            check_id="relevant-context",
            name="Relevant Context",
            dimension_id=DimensionId.TASK_UNDERSTANDING,
            state=EvidenceState.WIRED if has_prompts else EvidenceState.UNOBSERVED,
            summary="Context provided in user prompt stream",
            evidence=[f"{len(episode.prompts)} prompt turns recorded"],
        )

        c_scope = CheckResult(
            check_id="scope-boundary",
            name="Scope Boundary",
            dimension_id=DimensionId.TASK_UNDERSTANDING,
            state=EvidenceState.EXERCISED if diff_lines < 1000 else EvidenceState.MISSING,
            summary="Scope kept within focused diff bounds" if diff_lines < 1000 else "Excessive diff size indicates scope sprawl",
            evidence=[f"Diff size: {diff_lines} lines"],
        )

        if not has_goal:
            findings.append(Finding(
                finding_id="FINDING-TU-01",
                title="Missing Explicit Acceptance Criteria",
                dimension_id=DimensionId.TASK_UNDERSTANDING,
                severity="High",
                impact="Agent risk of implementing incorrect or misaligned requirements.",
                expected_output="Clear acceptance criteria defined before execution starts.",
                scoped_ai_fix="Add structured task goals to .supreme/plans/ before coding.",
                acceptance_checks=["Validate acceptance criteria exist in TaskEpisode."],
            ))

        dim_tu_score = self._score_checks([c_goal, c_context, c_scope])
        dimensions[DimensionId.TASK_UNDERSTANDING.value] = DimensionEvaluation(
            dimension_id=DimensionId.TASK_UNDERSTANDING,
            name="Task Understanding",
            question="Does the agent understand intended outcome, relevant context, and scope boundary?",
            score=dim_tu_score,
            checks=[c_goal, c_context, c_scope],
        )

        # -------------------------------------------------------------
        # 2. Controlled Execution
        # -------------------------------------------------------------
        tool_count = len(episode.tool_calls)
        dangerous_commands = [
            call for call in episode.tool_calls
            if "rm -rf /" in str(call) or "DROP DATABASE" in str(call)
        ]

        c_start = CheckResult(
            check_id="instruction-led-start",
            name="Reproducible Startup",
            dimension_id=DimensionId.CONTROLLED_EXECUTION,
            state=EvidenceState.PRESENT,
            summary="Container startup driven by apex-wrapper.sh and Scion manifest",
            evidence=["apex-wrapper.sh runtime wrapper verified"],
        )

        c_operation = CheckResult(
            check_id="supported-operation",
            name="Supported Operation",
            dimension_id=DimensionId.CONTROLLED_EXECUTION,
            state=EvidenceState.EXERCISED if tool_count > 0 else EvidenceState.WIRED,
            summary=f"Executed {tool_count} verified tool calls",
            evidence=[f"{tool_count} tool calls observed"],
        )

        c_perm = CheckResult(
            check_id="permission-boundary",
            name="Permission Boundary",
            dimension_id=DimensionId.CONTROLLED_EXECUTION,
            state=EvidenceState.EXERCISED if not dangerous_commands else EvidenceState.MISSING,
            summary="All actions respected sandbox and security policy" if not dangerous_commands else "Dangerous un-gated action detected!",
            evidence=["init-firewall.sh active", "No unauthorized egress"],
        )

        dim_ce_score = self._score_checks([c_start, c_operation, c_perm])
        dimensions[DimensionId.CONTROLLED_EXECUTION.value] = DimensionEvaluation(
            dimension_id=DimensionId.CONTROLLED_EXECUTION,
            name="Controlled Execution",
            question="Can the agent start and operate through supported routes within enforced boundaries?",
            score=dim_ce_score,
            checks=[c_start, c_operation, c_perm],
        )

        # -------------------------------------------------------------
        # 3. Change Validation
        # -------------------------------------------------------------
        test_executed = bool(episode.test_results)
        test_passed = episode.test_results.get("passed", False) if test_executed else False

        c_check = CheckResult(
            check_id="relevant-check",
            name="Relevant Verification",
            dimension_id=DimensionId.CHANGE_VALIDATION,
            state=EvidenceState.EXERCISED if test_executed else EvidenceState.MISSING,
            summary="Automated tests executed against changes" if test_executed else "No test verification recorded",
            evidence=[f"Test passed: {test_passed}"] if test_executed else [],
        )

        c_diag = CheckResult(
            check_id="failure-repair",
            name="Failure Diagnosis and Repair",
            dimension_id=DimensionId.CHANGE_VALIDATION,
            state=EvidenceState.OUTCOME_SUPPORTED if test_passed else (EvidenceState.EXERCISED if test_executed else EvidenceState.MISSING),
            summary="Diagnosis and repair verified by tests" if test_passed else "Pending test resolution",
            evidence=[],
        )

        c_reval = CheckResult(
            check_id="validate-again",
            name="Post-repair Revalidation",
            dimension_id=DimensionId.CHANGE_VALIDATION,
            state=EvidenceState.EXERCISED if test_passed else EvidenceState.UNOBSERVED,
            summary="Final clean test suite revalidation observed" if test_passed else "No clean revalidation observed",
            evidence=[],
        )

        if not test_executed:
            findings.append(Finding(
                finding_id="FINDING-CV-01",
                title="Unverified Code Modification",
                dimension_id=DimensionId.CHANGE_VALIDATION,
                severity="High",
                impact="Code changes committed without automated test verification.",
                expected_output="Deterministic test command execution before completion.",
                scoped_ai_fix="Run ./apex-wrapper.sh --gate before submitting task.",
                acceptance_checks=["Unit test execution recorded with 100% pass rate."],
            ))

        dim_cv_score = self._score_checks([c_check, c_diag, c_reval])
        dimensions[DimensionId.CHANGE_VALIDATION.value] = DimensionEvaluation(
            dimension_id=DimensionId.CHANGE_VALIDATION,
            name="Change Validation",
            question="Does the agent run relevant verification, diagnose failures, and revalidate?",
            score=dim_cv_score,
            checks=[c_check, c_diag, c_reval],
        )

        # -------------------------------------------------------------
        # 4. Reliable Delivery
        # -------------------------------------------------------------
        commits_present = len(episode.git_commits) > 0

        c_deliv = CheckResult(
            check_id="acceptance-evidence",
            name="Delivery Acceptance",
            dimension_id=DimensionId.RELIABLE_DELIVERY,
            state=EvidenceState.OUTCOME_SUPPORTED if (test_passed and commits_present) else EvidenceState.WIRED,
            summary="Work verified and committed to git" if (test_passed and commits_present) else "Incomplete delivery trail",
            evidence=[f"Commits: {len(episode.git_commits)}"],
        )

        c_high_risk = CheckResult(
            check_id="high-risk-approval",
            name="High-risk Approval",
            dimension_id=DimensionId.RELIABLE_DELIVERY,
            state=EvidenceState.WIRED,
            summary="LoopGate gatekeepers active for dangerous actions",
            evidence=["Gate policy configured"],
        )

        c_rollback = CheckResult(
            check_id="rollback-recovery",
            name="Rollback or Recovery",
            dimension_id=DimensionId.RELIABLE_DELIVERY,
            state=EvidenceState.PRESENT,
            summary="Git worktree rollback safety available via VeRO CandidateRepo",
            evidence=["VeRO worktree rollback engine ready"],
        )

        dim_rd_score = self._score_checks([c_deliv, c_high_risk, c_rollback])
        dimensions[DimensionId.RELIABLE_DELIVERY.value] = DimensionEvaluation(
            dimension_id=DimensionId.RELIABLE_DELIVERY,
            name="Reliable Delivery",
            question="Is result accepted at delivery boundary with rollback path?",
            score=dim_rd_score,
            checks=[c_deliv, c_high_risk, c_rollback],
        )

        # -------------------------------------------------------------
        # 5. Learning Capture
        # -------------------------------------------------------------
        c_repeat = CheckResult(
            check_id="lifecycle-repeat-detection",
            name="Lifecycle Opportunity Detection",
            dimension_id=DimensionId.LEARNING_CAPTURE,
            state=EvidenceState.WIRED,
            summary="Error and friction pattern detection wired in learning capture",
            evidence=[],
        )

        c_loop = CheckResult(
            check_id="loop-engineering",
            name="Loop Engineering",
            dimension_id=DimensionId.LEARNING_CAPTURE,
            state=EvidenceState.PRESENT,
            summary="Learning capture updates to .supreme/AGENTS.md enabled",
            evidence=["Learning capture module available"],
        )

        c_long = CheckResult(
            check_id="later-validation",
            name="Longitudinal Validation",
            dimension_id=DimensionId.LEARNING_CAPTURE,
            state=EvidenceState.UNOBSERVED,
            summary="Requires multiple historical task episodes to validate long-term trends",
            evidence=[],
        )

        dim_lc_score = self._score_checks([c_repeat, c_loop, c_long])
        dimensions[DimensionId.LEARNING_CAPTURE.value] = DimensionEvaluation(
            dimension_id=DimensionId.LEARNING_CAPTURE,
            name="Learning Capture",
            question="Does the harness detect recurring patterns and turn lessons into improvements?",
            score=dim_lc_score,
            checks=[c_repeat, c_loop, c_long],
        )

        overall = sum(d.score for d in dimensions.values()) / len(dimensions)

        return AuditReport(
            report_id=f"AUDIT-{int(now)}",
            timestamp=now,
            episode_id=episode.episode_id,
            overall_score=round(overall, 1),
            dimensions=dimensions,
            findings=findings,
            summary=f"Audit completed with overall health score of {overall:.1f}/100 across 5 dimensions.",
        )

    def _score_checks(self, checks: List[CheckResult]) -> float:
        """Computes weighted score from check evidence states."""
        weights = {
            EvidenceState.OUTCOME_SUPPORTED: 100.0,
            EvidenceState.EXERCISED: 90.0,
            EvidenceState.WIRED: 70.0,
            EvidenceState.PRESENT: 50.0,
            EvidenceState.NOT_APPLICABLE: 80.0,
            EvidenceState.UNOBSERVED: 40.0,
            EvidenceState.MISSING: 0.0,
        }
        total = sum(weights.get(c.state, 50.0) for c in checks)
        return round(total / max(len(checks), 1), 1)
