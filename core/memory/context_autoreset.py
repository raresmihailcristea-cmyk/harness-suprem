#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Context AutoReset & Memory Compaction Pipeline (LM Studio context-autoreset paradigm)

from __future__ import annotations
from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional, Tuple

from .mempalace import MemPalaceBridge

logger = logging.getLogger("core.memory.autoreset")

@dataclass
class ResetDecision:
    triggered: bool
    reason: str
    original_turns: int
    retained_turns: int
    archived_summary: str
    retained_messages: List[Dict[str, str]] = field(default_factory=list)

class ContextAutoResetter:
    """Monitors token capacity and compacts conversation history into MemPalace to prevent context overflow."""

    def __init__(self, max_context_tokens: int = 16384, trigger_threshold: float = 0.80):
        self.max_context_tokens = max_context_tokens
        self.trigger_threshold = trigger_threshold
        self.watermark_tokens = int(max_context_tokens * trigger_threshold)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Heuristic token estimator (~4 chars per token)."""
        return max(1, len(text) // 4)

    def evaluate_and_reset(
        self,
        messages: List[Dict[str, str]],
        agent_name: str = "Harness-Suprem",
    ) -> ResetDecision:
        """Evaluates whether message history exceeds watermark and compacts older turns into MemPalace."""
        total_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in messages)

        if total_tokens < self.watermark_tokens or len(messages) <= 6:
            return ResetDecision(
                triggered=False,
                reason=f"Context healthy: {total_tokens}/{self.max_context_tokens} tokens ({int(total_tokens / self.max_context_tokens * 100)}%).",
                original_turns=len(messages),
                retained_turns=len(messages),
                archived_summary="",
                retained_messages=messages,
            )

        # Split into historical turns (to compress) and active working turns (to keep)
        split_idx = max(2, len(messages) - 4)
        to_archive = messages[:split_idx]
        to_keep = messages[split_idx:]

        # Synthesize concise checkpoint
        archived_snippets = []
        for m in to_archive:
            role = m.get("role", "user").upper()
            content = m.get("content", "").strip().replace("\n", " ")
            archived_snippets.append(f"{role}: {content[:140]}...")

        summary_text = " | ".join(archived_snippets)
        archive_entry = f"[AutoReset Compaction] Archived {len(to_archive)} turns. Key thread: {summary_text[:500]}"

        # Persist to MemPalace cognitive diary
        MemPalaceBridge.append_diary(agent=f"autoreset:{agent_name}", entry=archive_entry)
        logger.info("Triggered Context AutoReset: Archived %d turns to MemPalace.", len(to_archive))

        # Inject checkpoint header into retained stream
        checkpoint_msg = {
            "role": "system",
            "content": f"## AUTOMATIC MEMPALACE CHECKPOINT\nEarlier context was compacted to preserve cognitive throughput. Stored state: {summary_text[:350]}"
        }
        retained = [checkpoint_msg] + to_keep

        return ResetDecision(
            triggered=True,
            reason=f"Context overflow threshold exceeded ({total_tokens} tokens >= {self.watermark_tokens} watermark).",
            original_turns=len(messages),
            retained_turns=len(retained),
            archived_summary=archive_entry,
            retained_messages=retained,
        )
