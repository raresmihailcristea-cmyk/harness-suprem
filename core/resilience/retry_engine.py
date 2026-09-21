#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Harness-Coder 1.3.3 Resilient Retry Engine

from __future__ import annotations
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("core.resilience.retry")

RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}

class ResilientRetryEngine:
    """Executes provider requests with capped exponential backoff and emits model_retry telemetry."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff_sec: float = 0.5,
        backoff_multiplier: float = 2.0,
        max_backoff_sec: float = 10.0,
    ):
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff_sec
        self.multiplier = backoff_multiplier
        self.max_backoff = max_backoff_sec
        self.retry_events: List[Dict[str, Any]] = []

    def execute_with_retry(
        self,
        func: Callable[[], Any],
        validator: Optional[Callable[[Any], Tuple[bool, str]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Executes func; retries on transient exceptions or invalid payloads."""
        current_delay = self.initial_backoff
        last_error = None

        for attempt in range(1, self.max_retries + 2):
            try:
                result = func()

                # If a validator is provided, verify response integrity
                if validator:
                    valid, reason = validator(result)
                    if not valid:
                        raise ValueError(f"Invalid model response: {reason}")

                return result

            except Exception as e:
                last_error = e
                if attempt > self.max_retries:
                    logger.error("Exhausted all %d retries. Failing with: %s", self.max_retries, str(e))
                    raise

                # Check if retryable
                error_msg = str(e)
                is_transient = any(str(code) in error_msg for code in RETRYABLE_STATUS_CODES)
                is_format_error = "Invalid model response" in error_msg or "JSONDecodeError" in error_msg

                event = {
                    "event": "model_retry",
                    "attempt": attempt,
                    "max_retries": self.max_retries,
                    "error": error_msg,
                    "delay_sec": current_delay,
                    "context": context or {},
                }
                self.retry_events.append(event)
                logger.warning(
                    "[model_retry #%d/%d] Transient error: %s. Retrying in %.2fs...",
                    attempt, self.max_retries, error_msg, current_delay
                )

                time.sleep(current_delay)
                current_delay = min(current_delay * self.multiplier, self.max_backoff)

        raise last_error or RuntimeError("Retry loop exited abnormally")

    def get_retry_count(self) -> int:
        return len(self.retry_events)
