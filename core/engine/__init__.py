"""Core Inference Engine Package for Harness-Suprem.
Dual-Engine Support: Apple MLX (Metal) & llama.cpp (GGUF Metal).
"""

from .llama_bridge import LlamaBridge
from .engine_router import DualEngineRouter, EngineType

__all__ = ["LlamaBridge", "DualEngineRouter", "EngineType"]
