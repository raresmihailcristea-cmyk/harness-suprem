#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Dual-Engine Router (Apple MLX Metal + llama.cpp Metal GGUF)

from __future__ import annotations
from enum import Enum
import json
import logging
from typing import Any, Dict, List, Optional
import urllib.request

from .llama_bridge import LlamaBridge

logger = logging.getLogger("core.engine.router")

class EngineType(str, Enum):
    MLX = "mlx"
    LLAMA_CPP = "llama_cpp"

class DualEngineRouter:
    """Manages routing between Apple MLX (port 5248) and llama.cpp (port 5249)."""

    MLX_PORT = 5248
    LLAMA_PORT = 5249

    def __init__(self, default_engine: EngineType = EngineType.MLX):
        self.active_engine = default_engine
        self.llama_bridge = LlamaBridge(port=self.LLAMA_PORT)

    def set_engine(self, engine: EngineType) -> None:
        self.active_engine = engine

    def get_active_port(self) -> int:
        if self.active_engine == EngineType.LLAMA_CPP:
            return self.LLAMA_PORT
        return self.MLX_PORT

    def is_mlx_running(self) -> bool:
        url = f"http://127.0.0.1:{self.MLX_PORT}/v1/models"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def is_llama_running(self) -> bool:
        return self.llama_bridge.is_running()

    def get_status(self) -> Dict[str, Any]:
        return {
            "active_engine": self.active_engine.value,
            "active_port": self.get_active_port(),
            "mlx": {
                "port": self.MLX_PORT,
                "is_running": self.is_mlx_running(),
                "model": "Qwen3.6-35B-A3B-8bit",
                "backend": "Apple MLX (Metal GPU)",
            },
            "llama_cpp": self.llama_bridge.get_status(),
        }


if __name__ == "__main__":
    router = DualEngineRouter()
    print(json.dumps(router.get_status(), indent=2))
