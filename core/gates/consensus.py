#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Multi-Role Consensus Planning Engine (oh-my-githubcopilot Paradigm)

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class ConsensusStatus(str, Enum):
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    VETOED = "VETOED"

@dataclass
class PersonaVote:
    role: str             # "Architect", "SecurityAuditor", "TestLead"
    approved: bool
    score: float          # 0.0 to 1.0
    rationale: str
    concerns: List[str] = field(default_factory=list)

@dataclass
class ConsensusDecision:
    status: ConsensusStatus
    overall_score: float
    votes: List[PersonaVote] = field(default_factory=list)
    summary: str = ""

class ConsensusEngine:
    """Evaluates proposals using a multi-agent triumvirate: Architect, Security Auditor, and Test Lead."""

    @classmethod
    def evaluate_proposal(
        cls,
        title: str,
        description: str,
        files_to_modify: List[str],
        has_tests: bool,
        has_security_risks: bool = False,
    ) -> ConsensusDecision:
        votes: List[PersonaVote] = []

        # 1. Architect Role: Checks blast radius and scope
        arch_concerns = []
        arch_score = 1.0
        if len(files_to_modify) > 10:
            arch_score -= 0.3
            arch_concerns.append("Large blast radius: touches more than 10 files simultaneously.")
        if any("core/" in f for f in files_to_modify) and not any("tests/" in f for f in files_to_modify):
            arch_score -= 0.4
            arch_concerns.append("Core runtime modified without accompanying tests.")

        votes.append(PersonaVote(
            role="Architect",
            approved=arch_score >= 0.7,
            score=round(arch_score, 2),
            rationale="Architectural integrity verified" if arch_score >= 0.7 else "Architecture concerns identified",
            concerns=arch_concerns,
        ))

        # 2. Security Auditor Role: Checks sensitive paths and credentials
        sec_concerns = []
        sec_score = 1.0
        if has_security_risks:
            sec_score = 0.0
            sec_concerns.append("High risk security signatures or unscrubbed secrets detected.")
        elif any(f.endswith(".env") or "credential" in f.lower() for f in files_to_modify):
            sec_score = max(0.0, sec_score - 0.6)
            sec_concerns.append("Direct mutation of credential or environment configuration.")

        votes.append(PersonaVote(
            role="SecurityAuditor",
            approved=sec_score >= 0.7,
            score=round(max(0.0, sec_score), 2),
            rationale="Security audit cleared" if sec_score >= 0.7 else "Security objections raised",
            concerns=sec_concerns,
        ))

        # 3. Test Lead Role: Checks testing discipline
        test_concerns = []
        test_score = 1.0 if has_tests else 0.4
        if not has_tests:
            test_concerns.append("Zero test coverage proposed for implementation changes.")

        votes.append(PersonaVote(
            role="TestLead",
            approved=test_score >= 0.7,
            score=round(test_score, 2),
            rationale="Sufficient test coverage" if test_score >= 0.7 else "Insufficient test coverage",
            concerns=test_concerns,
        ))

        # Aggregate Decision
        avg_score = sum(v.score for v in votes) / len(votes)
        vetoes = [v for v in votes if not v.approved and v.score <= 0.0]
        rejections = [v for v in votes if not v.approved]

        if vetoes:
            status = ConsensusStatus.VETOED
            summary = f"Vetoed by {', '.join(v.role for v in vetoes)}."
        elif rejections:
            status = ConsensusStatus.CHANGES_REQUESTED
            summary = f"Changes requested by {', '.join(v.role for v in rejections)}."
        else:
            status = ConsensusStatus.APPROVED
            summary = "Unanimous consensus reached across Architect, Security, and Test Lead."

        return ConsensusDecision(
            status=status,
            overall_score=round(avg_score, 2),
            votes=votes,
            summary=summary,
        )
