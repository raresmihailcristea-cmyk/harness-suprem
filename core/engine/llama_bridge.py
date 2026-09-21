#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Native llama.cpp Metal GPU Bridge & Server Supervisor for Harness-Suprem

from __future__ import annotations
import json
import logging
import os
import signal
import subprocess
import time
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

logger = logging.getLogger("core.engine.llama")

class LlamaBridge:
    """Supervises and interfaces with the local llama.cpp llama-server binary."""

    DEFAULT_BIN = "/opt/homebrew/bin/llama-server"
    DEFAULT_PORT = 5249
    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_GGUF_MODEL = "/Users/rarescristea/.cache/huggingface/hub/models--unsloth--gemma-4-26B-A4B-it-GGUF/snapshots/c099eb48e663fd284577b04978a94ffccb261841/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
    PID_FILE = "/tmp/harness_suprem_llama.pid"

    def __init__(
        self,
        bin_path: str = DEFAULT_BIN,
        model_path: Optional[str] = None,
        port: int = DEFAULT_PORT,
        host: str = DEFAULT_HOST,
        ctx_size: int = 16384,
        gpu_layers: int = 99,
    ):
        self.bin_path = bin_path
        self.model_path = model_path or self.DEFAULT_GGUF_MODEL
        self.port = port
        self.host = host
        self.ctx_size = ctx_size
        self.gpu_layers = gpu_layers

    def is_installed(self) -> bool:
        return os.path.exists(self.bin_path) and os.access(self.bin_path, os.X_OK)

    def is_model_available(self) -> bool:
        return os.path.exists(self.model_path)

    def is_running(self) -> bool:
        """Checks if llama-server is alive via HTTP health endpoint."""
        url = f"http://{self.host}:{self.port}/health"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Harness-Suprem"})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                return response.status == 200
        except Exception:
            return False

    def start(self, wait_seconds: int = 15) -> bool:
        """Starts llama-server in the background on Apple Silicon Metal GPU."""
        if self.is_running():
            logger.info("llama-server is already running on %s:%d", self.host, self.port)
            return True

        if not self.is_installed():
            logger.error("llama-server binary not found at %s", self.bin_path)
            return False

        if not self.is_model_available():
            logger.error("GGUF model not found at %s", self.model_path)
            return False

        cmd = [
            self.bin_path,
            "-m", self.model_path,
            "--host", self.host,
            "--port", str(self.port),
            "-ngl", str(self.gpu_layers),
            "-c", str(self.ctx_size),
            "--cont-batching",
            "--slots",
        ]

        log_file = "/tmp/harness_llama_server.log"
        logger.info("Launching llama-server: %s", " ".join(cmd))
        
        with open(log_file, "a") as f_out:
            proc = subprocess.Popen(
                cmd,
                stdout=f_out,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,
            )

        with open(self.PID_FILE, "w") as f_pid:
            f_pid.write(str(proc.pid))

        # Wait for health endpoint
        start_time = time.time()
        while time.time() - start_time < wait_seconds:
            if self.is_running():
                logger.info("llama-server started successfully on port %d (PID %d)", self.port, proc.pid)
                return True
            time.sleep(0.5)

        logger.warning("llama-server started process %d, but health check timed out.", proc.pid)
        return False

    def stop(self) -> bool:
        """Stops the running llama-server daemon."""
        stopped = False
        if os.path.exists(self.PID_FILE):
            try:
                with open(self.PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                stopped = True
            except Exception as e:
                logger.warning("Error stopping via PID file: %s", e)
            try:
                os.remove(self.PID_FILE)
            except OSError:
                pass

        # Also kill by binary and port fallback
        subprocess.run(["pkill", "-f", f"llama-server.*{self.port}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return stopped or not self.is_running()

    def get_status(self) -> Dict[str, Any]:
        """Returns diagnostic telemetry about the llama-server engine."""
        running = self.is_running()
        model_name = os.path.basename(self.model_path) if self.model_path else "none"
        model_size_gb = 0.0
        if self.is_model_available():
            model_size_gb = round(os.path.getsize(self.model_path) / (1024 ** 3), 2)

        return {
            "engine": "llama.cpp",
            "is_installed": self.is_installed(),
            "binary_path": self.bin_path,
            "is_running": running,
            "port": self.port,
            "host": self.host,
            "model_path": self.model_path,
            "model_name": model_name,
            "model_size_gb": model_size_gb,
            "metal_acceleration": "Metal GPU Enabled (-ngl 99)",
            "context_size": self.ctx_size,
        }

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        grammar: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Sends a synchronous chat completion to llama-server."""
        url = f"http://{self.host}:{self.port}/v1/chat/completions"
        payload: Dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if grammar:
            payload["grammar"] = grammar

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "Harness-Suprem"}
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    import sys
    bridge = LlamaBridge()
    if "--start" in sys.argv:
        success = bridge.start()
        print(f"llama-server start result: {success}")
    elif "--stop" in sys.argv:
        success = bridge.stop()
        print(f"llama-server stop result: {success}")
    else:
        print(json.dumps(bridge.get_status(), indent=2))
