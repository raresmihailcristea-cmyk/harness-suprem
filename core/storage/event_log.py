#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Append-Only Crash-Safe Event Log & Multi-Agent Convoy Coordinator (neul-labs/brat Paradigm)

from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("core.storage.event_log")

@dataclass
class LoggedEvent:
    seq: int
    timestamp: float
    event_type: str
    payload: Dict[str, Any]
    checksum: str = ""

    def calculate_checksum(self) -> str:
        data = f"{self.seq}:{self.timestamp}:{self.event_type}:{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]

class AppendOnlyEventLog:
    """Crash-safe append-only journal with integrity checksums and deterministic state reconstruction."""

    def __init__(self, log_path: str):
        self.log_path = os.path.abspath(log_path)
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self.current_seq = 0
        self.events: List[LoggedEvent] = []
        self.file_locks: Dict[str, str] = {}  # filepath -> agent_id
        self._recover_and_replay()

    def _recover_and_replay(self) -> None:
        """Reads the journal, discards uncommitted/corrupted trailing writes, and replays state."""
        if not os.path.exists(self.log_path):
            return

        valid_lines = []
        last_valid_offset = 0

        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    raw = json.loads(stripped)
                    evt = LoggedEvent(
                        seq=raw["seq"],
                        timestamp=raw["timestamp"],
                        event_type=raw["event_type"],
                        payload=raw["payload"],
                        checksum=raw.get("checksum", ""),
                    )
                    # Verify integrity
                    expected = evt.calculate_checksum()
                    if evt.checksum and evt.checksum != expected:
                        logger.warning("Checksum mismatch at seq %d. Truncating journal to valid prefix.", evt.seq)
                        break

                    self.events.append(evt)
                    self.current_seq = max(self.current_seq, evt.seq)
                    valid_lines.append(stripped)
                    self._apply_to_projection(evt)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("Corrupt trailing line detected during crash recovery: %s. Truncating.", e)
                    break

        # If corruption was encountered, rewrite cleanly to last valid prefix
        total_nonempty = 0
        with open(self.log_path, "r", encoding="utf-8") as f:
            total_nonempty = sum(1 for line in f if line.strip())

        if len(valid_lines) != total_nonempty:
            with open(self.log_path, "w", encoding="utf-8") as f:
                for vl in valid_lines:
                    f.write(vl + "\n")
                f.flush()
                os.fsync(f.fileno())

    def _apply_to_projection(self, evt: LoggedEvent) -> None:
        """Projects events into current in-memory multi-agent coordinator state."""
        if evt.event_type == "lock_acquired":
            path = evt.payload.get("path", "")
            agent = evt.payload.get("agent_id", "")
            if path and agent:
                self.file_locks[path] = agent
        elif evt.event_type == "lock_released":
            path = evt.payload.get("path", "")
            if path in self.file_locks:
                del self.file_locks[path]

    def append(self, event_type: str, payload: Dict[str, Any]) -> LoggedEvent:
        """Atomically appends an event with a verifiable SHA-256 checksum."""
        self.current_seq += 1
        evt = LoggedEvent(
            seq=self.current_seq,
            timestamp=time.time(),
            event_type=event_type,
            payload=payload,
        )
        evt.checksum = evt.calculate_checksum()

        line = json.dumps(asdict(evt)) + "\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

        self.events.append(evt)
        self._apply_to_projection(evt)
        return evt

    def acquire_lock(self, path: str, agent_id: str) -> bool:
        """Multi-agent convoy lock: prevents conflicting writes between parallel agents."""
        norm_path = os.path.normpath(path)
        holder = self.file_locks.get(norm_path)
        if holder and holder != agent_id:
            return False  # Locked by someone else
        self.append("lock_acquired", {"path": norm_path, "agent_id": agent_id})
        return True

    def release_lock(self, path: str, agent_id: str) -> bool:
        """Releases lock held by an agent."""
        norm_path = os.path.normpath(path)
        if self.file_locks.get(norm_path) == agent_id:
            self.append("lock_released", {"path": norm_path, "agent_id": agent_id})
            return True
        return False
