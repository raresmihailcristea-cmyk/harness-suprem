#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Native Apple MLX Bridge Engine for Qwen3.6-35B-A3B-8bit (Direct Metal GPU execution)

from __future__ import annotations
import json
import logging
import os
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mlx_bridge")

MODEL_PATH = "/Users/rarescristea/.cache/huggingface/hub/models--mlx-community--Qwen3.6-35B-A3B-8bit/snapshots/e06a74e6236a60c8367e1a3214e83d8b61b637b0"
PYTHON_MLX = "/Users/rarescristea/.local/share/uv/tools/mtplx/bin/python3"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5248

def is_server_running(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
    """Checks if MLX API server is active and responding."""
    url = f"http://{host}:{port}/v1/models"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Harness-Suprem-Desktop"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False

def start_mlx_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, foreground: bool = False) -> subprocess.Popen | None:
    """Starts the native MLX HTTP server directly binding to Apple Metal GPU."""
    if is_server_running(host, port):
        logger.info("MLX Server is already running on %s:%d", host, port)
        return None

    if not os.path.exists(MODEL_PATH):
        logger.error("Model path does not exist: %s", MODEL_PATH)
        sys.exit(1)

    cmd = [
        PYTHON_MLX, "-m", "mlx_lm", "server",
        "--model", MODEL_PATH,
        "--host", host,
        "--port", str(port),
        "--max-tokens", "16384",
        "--prefill-step-size", "2048",
        "--temp", "0.2",
    ]

    logger.info("Launching Native MLX Engine: %s", " ".join(cmd))
    log_dir = os.path.expanduser("~/.supreme/logs")
    os.makedirs(log_dir, exist_ok=True)
    out_log = open(os.path.join(log_dir, "mlx_engine.log"), "a")

    proc = subprocess.Popen(
        cmd,
        stdout=out_log,
        stderr=out_log,
        preexec_fn=os.setsid if hasattr(os, "setsid") else None,
    )

    # Poll until ready
    logger.info("Waiting for Qwen3.6-35B-8bit to load into Apple M1 Ultra unified memory...")
    for _ in range(60):
        if is_server_running(host, port):
            logger.info(">>> MLX Engine Ready on http://%s:%d (PID: %d)", host, port, proc.pid)
            break
        if proc.poll() is not None:
            logger.error("MLX process terminated unexpectedly with code %d", proc.returncode)
            sys.exit(1)
        time.sleep(1)

    if foreground:
        try:
            proc.wait()
        except KeyboardInterrupt:
            logger.info("Shutting down MLX server...")
            proc.terminate()
            proc.wait()

    return proc

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Harness-Suprem MLX Bridge")
    parser.add_argument("--check", action="store_true", help="Check if running")
    parser.add_argument("--start", action="store_true", help="Start in background")
    parser.add_argument("--foreground", action="store_true", help="Start in foreground")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind")
    args = parser.parse_args()

    if args.check:
        running = is_server_running(port=args.port)
        print("RUNNING" if running else "STOPPED")
        sys.exit(0 if running else 1)

    start_mlx_server(port=args.port, foreground=args.foreground)
