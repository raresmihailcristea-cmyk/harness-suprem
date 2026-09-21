#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# VeRO Inference Gateway & FinOps Spend Meter

from __future__ import annotations
from dataclasses import dataclass, field
import logging
from typing import Dict, Optional

logger = logging.getLogger("vero.gateway")

class BudgetExceededError(Exception):
    """Raised when token or dollar budget is exhausted for a candidate scope."""
    pass

@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.reasoning_tokens

@dataclass
class ScopeBudget:
    max_tokens: int = 200_000
    max_usd: float = 5.00

# Estimated rates per 1M tokens (USD)
MODEL_RATES = {
    "deepseek-ai/deepseek-v3": {"input": 0.14, "output": 0.28, "cache": 0.014},
    "deepseek-ai/deepseek-r1": {"input": 0.55, "output": 2.19, "cache": 0.14},
    "anthropic/claude-sonnet-4": {"input": 3.00, "output": 15.00, "cache": 0.30},
    "anthropic/claude-opus-4": {"input": 15.00, "output": 75.00, "cache": 1.50},
    "openai/gpt-4o": {"input": 2.50, "output": 10.00, "cache": 1.25},
    "xai/grok-4": {"input": 2.00, "output": 10.00, "cache": 0.20},
}

class InferenceGateway:
    """Manages token consumption, cost tracking, and budget enforcement across optimization rounds."""

    def __init__(self, default_budget: Optional[ScopeBudget] = None):
        self.default_budget = default_budget or ScopeBudget()
        self.scopes: Dict[str, TokenUsage] = {}
        self.scope_budgets: Dict[str, ScopeBudget] = {}

    def register_scope(self, scope_id: str, budget: Optional[ScopeBudget] = None) -> None:
        self.scopes[scope_id] = TokenUsage()
        self.scope_budgets[scope_id] = budget or self.default_budget

    def record_call(
        self,
        scope_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        reasoning_tokens: int = 0,
    ) -> float:
        """Records an inference call and returns its incremental cost in USD."""
        if scope_id not in self.scopes:
            self.register_scope(scope_id)

        usage = self.scopes[scope_id]
        usage.input_tokens += input_tokens
        usage.output_tokens += output_tokens
        usage.cached_tokens += cached_tokens
        usage.reasoning_tokens += reasoning_tokens

        # Calculate incremental cost
        rates = MODEL_RATES.get(model, {"input": 1.0, "output": 2.0, "cache": 0.1})
        cost = (
            (input_tokens / 1_000_000) * rates["input"]
            + (output_tokens / 1_000_000) * rates["output"]
            + (cached_tokens / 1_000_000) * rates["cache"]
            + (reasoning_tokens / 1_000_000) * rates["output"]
        )

        total_cost = self.get_scope_cost(scope_id, model)
        budget = self.scope_budgets[scope_id]

        if usage.total_tokens > budget.max_tokens:
            raise BudgetExceededError(
                f"Scope '{scope_id}' exceeded token budget: {usage.total_tokens} > {budget.max_tokens}"
            )
        if total_cost > budget.max_usd:
            raise BudgetExceededError(
                f"Scope '{scope_id}' exceeded USD budget: ${total_cost:.4f} > ${budget.max_usd:.2f}"
            )

        return cost

    def get_scope_usage(self, scope_id: str) -> TokenUsage:
        return self.scopes.get(scope_id, TokenUsage())

    def get_scope_cost(self, scope_id: str, model: str = "deepseek-ai/deepseek-v3") -> float:
        usage = self.get_scope_usage(scope_id)
        rates = MODEL_RATES.get(model, {"input": 1.0, "output": 2.0, "cache": 0.1})
        return (
            (usage.input_tokens / 1_000_000) * rates["input"]
            + (usage.output_tokens / 1_000_000) * rates["output"]
            + (usage.cached_tokens / 1_000_000) * rates["cache"]
            + (usage.reasoning_tokens / 1_000_000) * rates["output"]
        )
