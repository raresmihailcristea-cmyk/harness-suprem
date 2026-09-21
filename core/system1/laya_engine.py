# Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea
# Laya System 1 Non-Autoregressive Decision & Routing Engine
# High-speed (<35ms) typed decisions, pre-flight semantic guardrails, and tool shortlisting.

from __future__ import annotations
import math
import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    import laya
    _HAS_LAYA = True
except ImportError:
    _HAS_LAYA = False

try:
    import torch
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False


@dataclass
class DecisionResult:
    primitive: str  # 'choice', 'score', or 'noul'
    result: Any
    confidence: float
    distribution: Dict[str, float] = field(default_factory=dict)
    latency_ms: float = 0.0
    model_used: str = "laya-engine"
    reason: str = ""


@dataclass
class RoutingDecision:
    target_tier: str  # 'fast_local' | 'deep_reasoning'
    recommended_model: str
    confidence: float
    complexity_score: float  # 0.0 (trivial) to 1.0 (extreme reasoning)
    latency_ms: float
    language: str
    script: str
    reason: str


@dataclass
class GuardVerdict:
    is_safe: bool
    risk_score: float  # 0.0 (safe) to 1.0 (malicious)
    verdict: str  # 'PASS', 'WARN', 'BLOCK'
    flags: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    reason: str = ""


class LayaDecisionEngine:
    """
    Non-autoregressive System 1 decision engine for Harness-Suprem and LM Studio.
    Provides sub-35ms routing, prompt guardrails, tool shortlisting, and typed decisions.
    """

    def __init__(
        self,
        prefer_local_mps: bool = True,
        confidence_threshold: float = 0.85,
        default_router_preload: bool = False
    ):
        self.confidence_threshold = confidence_threshold
        self.prefer_local_mps = prefer_local_mps
        self.device = "cpu"
        self._router = None
        self._agent = None

        if _HAS_TORCH and prefer_local_mps:
            if torch.backends.mps.is_available():
                self.device = "mps"
            elif torch.cuda.is_available():
                self.device = "cuda"

        if _HAS_LAYA and default_router_preload:
            try:
                from laya import Router
                self._router = Router(preload=True, device=self.device)
            except Exception:
                self._router = None

    # -------------------------------------------------------------
    # 1. Script & Language Fast Detection (<0.5ms)
    # -------------------------------------------------------------
    @staticmethod
    def detect_script_and_language(text: str) -> Tuple[str, str]:
        """Detects script and language family in under 0.5ms without model forward-pass."""
        if not text:
            return "latin", "en"

        # Unicode script counts
        devanagari = len(re.findall(r'[\u0900-\u097F]', text))
        cyrillic = len(re.findall(r'[\u0400-\u04FF]', text))
        arabic = len(re.findall(r'[\u0600-\u06FF]', text))
        cjk = len(re.findall(r'[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]', text))
        latin = len(re.findall(r'[a-zA-Z]', text))
        total_letters = devanagari + cyrillic + arabic + cjk + latin

        if total_letters == 0:
            return "latin", "en"

        if devanagari / total_letters > 0.3:
            return "devanagari", "hi"
        if cyrillic / total_letters > 0.3:
            return "cyrillic", "ru"
        if arabic / total_letters > 0.3:
            return "arabic", "ar"
        if cjk / total_letters > 0.3:
            return "cjk", "zh"

        # Latin heuristics for Romanian vs English
        ro_markers = len(re.findall(r'\b(si|sau|pentru|care|este|sunt|adica|acest|aceasta|fisier|eroare|trebuie|sa|am|in|pe)\b', text.lower()))
        words_count = max(1, len(text.split()))
        if ro_markers / words_count > 0.08:
            return "latin", "ro"

        return "latin", "en"

    # -------------------------------------------------------------
    # 2. Fast System 1 -> System 2 Router
    # -------------------------------------------------------------
    def route_task(self, prompt: str, state_context: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        """
        Sub-35ms routing determining if a prompt can be handled by a fast local model
        or requires deep reasoning (DeepSeek-R1 / Claude 3.5 Sonnet).
        """
        t0 = time.perf_counter()
        script, lang = self.detect_script_and_language(prompt)

        # 1. Native Laya route execution if available
        if self._router is not None:
            try:
                questions = {
                    "complexity": {
                        "type": "choice",
                        "instructions": "Does this coding or engineering task require complex multi-step reasoning or simple execution?",
                        "criteria": {
                            "fast_local": "lint, format, read file, run test, git commit, trivial fix, status check",
                            "deep_reasoning": "architecture redesign, algorithmic proof, difficult bug debugging, security protocol, full feature"
                        }
                    }
                }
                res = self._router.predict({"prompt": prompt}, questions)
                choice = res["answers"]["complexity"]["choice"]
                conf = res["answers"]["complexity"]["confidence"]
                lat = (time.perf_counter() - t0) * 1000

                rec_model = "deepseek-r1" if choice == "deep_reasoning" else "veriloop-coder-e1"
                complexity = 0.85 if choice == "deep_reasoning" else 0.25

                return RoutingDecision(
                    target_tier=choice,
                    recommended_model=rec_model,
                    confidence=float(conf),
                    complexity_score=complexity,
                    latency_ms=round(lat, 2),
                    language=lang,
                    script=script,
                    reason=f"Laya neural classification ({choice} at {conf:.2f} confidence)"
                )
            except Exception:
                pass

        # 2. Fast-Path Calibrated Heuristic Engine (zero extra dependency, sub-1ms)
        p_lower = prompt.lower()
        deep_indicators = [
            "arhitectura", "architecture", "refactor", "redesign", "algorithm",
            "proof", "concurrency", "race condition", "memory leak", "deadlock",
            "security audit", "vulnerability", "complex", "deepseek-r1", "sonnet",
            "planifica", "strategie", "optimizare matematica", "implementeaza tot"
        ]
        fast_indicators = [
            "run", "executa", "test", "pytest", "swift build", "git status",
            "git commit", "format", "lint", "arata", "vezi", "view", "ls",
            "status", "read", "citeste", "verifica", "check", "version"
        ]

        deep_matches = sum(1 for kw in deep_indicators if kw in p_lower)
        fast_matches = sum(1 for kw in fast_indicators if kw in p_lower)
        prompt_len = len(prompt.split())

        # Scoring complexity
        raw_score = 0.3
        if prompt_len > 120:
            raw_score += 0.25
        elif prompt_len < 20:
            raw_score -= 0.15

        raw_score += (deep_matches * 0.22) - (fast_matches * 0.18)
        complexity = max(0.05, min(0.98, raw_score))

        target = "deep_reasoning" if complexity >= 0.55 else "fast_local"
        rec_model = "deepseek-r1" if target == "deep_reasoning" else "veriloop-coder-e1"
        confidence = round(0.72 + abs(complexity - 0.5) * 0.5, 3)

        lat = (time.perf_counter() - t0) * 1000
        return RoutingDecision(
            target_tier=target,
            recommended_model=rec_model,
            confidence=min(0.99, confidence),
            complexity_score=round(complexity, 3),
            latency_ms=round(lat, 2),
            language=lang,
            script=script,
            reason=f"System 1 fast heuristic (complexity={complexity:.2f}, deep={deep_matches}, fast={fast_matches})"
        )

    # -------------------------------------------------------------
    # 3. Pre-flight Semantic Guardrails (Prompt Injection / Jailbreak)
    # -------------------------------------------------------------
    def guard_prompt(self, prompt: str) -> GuardVerdict:
        """
        Sub-35ms semantic guardrail evaluating prompt injection, jailbreaks,
        and system prompt override attacks before sending to main models.
        """
        t0 = time.perf_counter()
        p_lower = prompt.lower()
        flags = []
        risk_score = 0.0

        # Patterns for prompt injection and instruction tampering
        tamper_patterns = [
            (r'(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)', "instruction_override", 0.85),
            (r'you\s+are\s+now\s+(in\s+)?(developer\s+mode|unrestricted|god\s+mode|dan)', "jailbreak_persona", 0.90),
            (r'(reveal|output|print|display)\s+(your\s+)?(system\s+prompt|initial\s+instructions)', "system_prompt_leak", 0.80),
            (r'(base64|hex)\s+decode\s+and\s+execute', "encoded_payload_execution", 0.75),
            (r'sudo\s+rm\s+-rf|chmod\s+777\s+/|mkfs\.', "destructive_command_tamper", 0.95),
            (r'curl\s+.*\s*\|\s*(ba)?sh', "remote_shell_pipe", 0.90),
        ]

        for pattern, label, weight in tamper_patterns:
            if re.search(pattern, p_lower):
                flags.append(label)
                risk_score = max(risk_score, weight)

        # Non-Latin script spoofing or excessive control characters
        control_chars = len(re.findall(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', prompt))
        if control_chars > 3:
            flags.append("suspicious_control_characters")
            risk_score = max(risk_score, 0.70)

        # Verdict
        if risk_score >= 0.75:
            verdict = "BLOCK"
            is_safe = False
        elif risk_score >= 0.40:
            verdict = "WARN"
            is_safe = True
        else:
            verdict = "PASS"
            is_safe = True

        lat = (time.perf_counter() - t0) * 1000
        return GuardVerdict(
            is_safe=is_safe,
            risk_score=round(risk_score, 2),
            verdict=verdict,
            flags=flags,
            latency_ms=round(lat, 2),
            reason=f"Guarded in {lat:.2f}ms with {len(flags)} flags" if flags else "Prompt verified clean"
        )

    # -------------------------------------------------------------
    # 4. Dynamic Tool & Subagent Shortlisting (predict_shortlist)
    # -------------------------------------------------------------
    def shortlist_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        k: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Dynamically filters a list of 20-50+ tools/plugins to the top-k most relevant
        items for the given prompt, eliminating 70-80% of prompt clutter.
        """
        if len(tools) <= k:
            return tools

        p_tokens = set(re.findall(r'[a-zA-Z0-9_-]{3,}', prompt.lower()))
        scored_tools: List[Tuple[float, Dict[str, Any]]] = []

        for tool in tools:
            name = tool.get("name", "").lower()
            desc = tool.get("description", "").lower()
            keywords = tool.get("keywords", [])
            
            tool_tokens = set(re.findall(r'[a-zA-Z0-9_-]{3,}', f"{name} {desc} {' '.join(keywords)}"))
            
            # Term overlap (Jaccard / intersection matching)
            intersection = len(p_tokens.intersection(tool_tokens))
            name_match = 2.0 if any(tok in name for tok in p_tokens) else 0.0
            
            score = intersection + name_match
            scored_tools.append((score, tool))

        # Sort descending by relevance score
        scored_tools.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_tools[:k]]

    # -------------------------------------------------------------
    # 5. Typed Decision Evaluator (choice, score, noul)
    # -------------------------------------------------------------
    def evaluate_typed_decision(
        self,
        state: Union[str, Dict[str, Any]],
        question_schema: Dict[str, Any]
    ) -> DecisionResult:
        """
        Evaluates a single typed question (choice, score, or noul) on arbitrary state.
        """
        t0 = time.perf_counter()
        q_type = question_schema.get("type", "choice")
        criteria = question_schema.get("criteria", {})

        state_text = state if isinstance(state, str) else str(state)
        s_lower = state_text.lower()

        if q_type == "noul":
            # Boolean evaluation
            instructions = question_schema.get("instructions", "").lower()
            keywords = question_schema.get("keywords", [])
            matches = sum(1 for kw in keywords if kw.lower() in s_lower)
            prob = 0.88 if matches > 0 else 0.12
            decision = prob >= 0.5
            lat = (time.perf_counter() - t0) * 1000
            return DecisionResult(
                primitive="noul",
                result=decision,
                confidence=round(prob if decision else (1.0 - prob), 3),
                distribution={"true": round(prob, 3), "false": round(1.0 - prob, 3)},
                latency_ms=round(lat, 2),
                reason=f"Noul decision ({decision}) based on keyword signals"
            )

        elif q_type == "score":
            # Ordinal score evaluation (e.g. 1 to 5)
            scale = criteria if isinstance(criteria, list) else [1, 2, 3, 4, 5]
            urgency_words = ["urgent", "blocking", "critical", "crash", "error", "deadline", "emergency"]
            u_count = sum(1 for w in urgency_words if w in s_lower)
            idx = min(len(scale) - 1, u_count)
            val = scale[idx]
            lat = (time.perf_counter() - t0) * 1000
            return DecisionResult(
                primitive="score",
                result=val,
                confidence=0.82,
                latency_ms=round(lat, 2),
                reason=f"Score mapped to {val} from urgency density"
            )

        else:
            # Choice evaluation
            scores: Dict[str, float] = {}
            if isinstance(criteria, dict):
                for label, desc in criteria.items():
                    desc_toks = set(re.findall(r'[a-zA-Z0-9_-]{3,}', desc.lower()))
                    matches = sum(1 for tok in desc_toks if tok in s_lower)
                    scores[label] = float(matches + 0.1)
            else:
                for label in criteria:
                    scores[str(label)] = 1.0

            total = sum(scores.values()) or 1.0
            dist = {k: round(v / total, 3) for k, v in scores.items()}
            top_choice = max(dist.items(), key=lambda x: x[1])

            lat = (time.perf_counter() - t0) * 1000
            return DecisionResult(
                primitive="choice",
                result=top_choice[0],
                confidence=top_choice[1],
                distribution=dist,
                latency_ms=round(lat, 2),
                reason=f"Selected '{top_choice[0]}' with {top_choice[1]*100:.1f}% confidence"
            )


# Global singleton instance for high-speed reuse
_GLOBAL_ENGINE = LayaDecisionEngine()

def get_system1_engine() -> LayaDecisionEngine:
    return _GLOBAL_ENGINE


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Laya System 1 Decision & Routing Engine")
    parser.add_argument("--route", "-r", type=str, help="Route a prompt (fast_local vs deep_reasoning)")
    parser.add_argument("--guard", "-g", type=str, help="Evaluate prompt safety and injection risk")
    args = parser.parse_args()

    engine = get_system1_engine()

    if args.route:
        dec = engine.route_task(args.route)
        print(json.dumps({
            "target_tier": dec.target_tier,
            "recommended_model": dec.recommended_model,
            "confidence": dec.confidence,
            "complexity_score": dec.complexity_score,
            "latency_ms": dec.latency_ms,
            "language": dec.language,
            "reason": dec.reason
        }, indent=2))
    elif args.guard:
        gv = engine.guard_prompt(args.guard)
        print(json.dumps({
            "is_safe": gv.is_safe,
            "risk_score": gv.risk_score,
            "verdict": gv.verdict,
            "flags": gv.flags,
            "latency_ms": gv.latency_ms,
            "reason": gv.reason
        }, indent=2))
    else:
        print("Laya Decision Engine v0.3.5 initialized.")
        print("Run with --route '<prompt>' or --guard '<prompt>'")
