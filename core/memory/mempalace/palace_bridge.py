#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# MemPalace Native Bridge for Supreme Harness (Connecting to ~/.config/mempalace & CLI)

from __future__ import annotations
from datetime import datetime, timezone
import json
import logging
import os
import re
import shutil
import sqlite3
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger("core.memory.mempalace")

class MemPalaceBridge:
    """Provides high-speed episodic memory retrieval and filing via MemPalace."""

    MEMPALACE_BIN = "/Users/rarescristea/.local/bin/mempalace"
    CONFIG_DIR = os.path.expanduser("~/.config/mempalace")
    KG_DB = os.path.join(CONFIG_DIR, "knowledge_graph.sqlite3")
    DIARY_FILE = os.path.join(CONFIG_DIR, "diary.jsonl")

    @classmethod
    def is_available(cls) -> bool:
        return os.path.exists(cls.MEMPALACE_BIN) or os.path.exists(cls.CONFIG_DIR)

    @classmethod
    def get_wake_up_context(cls, wing: Optional[str] = None, max_tokens: int = 900) -> str:
        """Retrieves L0 (Identity) and L1 (Essential Story) memory context (~600-900 tokens)."""
        if os.path.exists(cls.MEMPALACE_BIN):
            cmd = [cls.MEMPALACE_BIN, "wake-up"]
            if wing:
                cmd.extend(["--wing", wing])
            try:
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception as e:
                logger.warning("mempalace wake-up CLI call failed: %s", e)

        # Fallback to direct identity
        return (
            "## L0 — IDENTITY\n"
            "User: Rareș Cristea\n"
            "Environment: macOS (Apple Silicon M1 Ultra 128GB), Local AI Ecosystem.\n"
            "Principles: Local-First & Privacy, Never hallucinate past decisions, Query MemPalace.\n"
        )

    @classmethod
    def search_memory(cls, query: str, wing: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches MemPalace drawers and knowledge graph for relevant context."""
        results: List[Dict[str, Any]] = []
        if not query or not query.strip():
            return results

        # 1. Try mempalace search CLI
        if os.path.exists(cls.MEMPALACE_BIN):
            cmd = [cls.MEMPALACE_BIN, "search", query]
            if wing:
                cmd.extend(["--wing", wing])
            try:
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
                if res.returncode == 0 and res.stdout.strip():
                    for line in res.stdout.splitlines():
                        line_s = line.strip()
                        if line_s and not line_s.startswith("=") and not line_s.startswith("Found"):
                            results.append({
                                "source": "mempalace_drawer",
                                "snippet": line_s[:300],
                            })
                            if len(results) >= limit:
                                break
            except Exception as e:
                logger.warning("mempalace search error: %s", e)

        # 2. Query Knowledge Graph SQLite (Entities & Triples)
        if os.path.exists(cls.KG_DB):
            try:
                conn = sqlite3.connect(cls.KG_DB)
                cursor = conn.cursor()
                # Check entities using proper schema (name, type, properties)
                term = f"%{query.strip()}%"
                cursor.execute("SELECT name, type, properties FROM entities WHERE name LIKE ? OR properties LIKE ? LIMIT ?", (term, term, limit))
                for row in cursor.fetchall():
                    results.append({
                        "source": "knowledge_graph_entity",
                        "entity": row[0],
                        "type": row[1],
                        "properties": row[2] or "",
                    })
                conn.close()
            except Exception as e:
                logger.warning("Error querying knowledge_graph.sqlite3: %s", e)

        return results[:limit]

    @classmethod
    def append_diary(cls, agent: str, entry: str) -> bool:
        """Appends a cognitive step to ~/.config/mempalace/diary.jsonl."""
        os.makedirs(cls.CONFIG_DIR, exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "entry": entry,
        }
        try:
            with open(cls.DIARY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            return True
        except Exception as e:
            logger.error("Failed to append to diary.jsonl: %s", e)
            return False

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Queries status of MemPalace: total drawers, entities, triples, and diary length."""
        entities_count = 0
        triples_count = 0
        diary_entries = 0
        total_drawers = 0

        # Read SQLite
        if os.path.exists(cls.KG_DB):
            try:
                conn = sqlite3.connect(cls.KG_DB)
                cursor = conn.cursor()
                cursor.execute("SELECT count(*) FROM entities;")
                entities_count = cursor.fetchone()[0]
                cursor.execute("SELECT count(*) FROM triples;")
                triples_count = cursor.fetchone()[0]
                conn.close()
            except Exception:
                pass

        # Read Diary
        if os.path.exists(cls.DIARY_FILE):
            try:
                with open(cls.DIARY_FILE, "r", encoding="utf-8") as f:
                    diary_entries = sum(1 for _ in f if _.strip())
            except Exception:
                pass

        # Query CLI status
        if os.path.exists(cls.MEMPALACE_BIN):
            try:
                res = subprocess.run([cls.MEMPALACE_BIN, "status"], stdout=subprocess.PIPE, text=True, timeout=5)
                match = re.search(r"(\d+)\s+drawers", res.stdout)
                if match:
                    total_drawers = int(match.group(1))
            except Exception:
                pass

        return {
            "is_available": cls.is_available(),
            "total_drawers": total_drawers,
            "entities_count": entities_count,
            "triples_count": triples_count,
            "diary_entries": diary_entries,
            "palace_path": cls.CONFIG_DIR,
        }
