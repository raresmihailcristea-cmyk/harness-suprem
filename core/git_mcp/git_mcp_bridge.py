# Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea
# GitMCP Remote Documentation & Live Code Hub
# Powered by idosal/git-mcp (https://gitmcp.io)

from __future__ import annotations
import json
import logging
import os
import urllib.request
import urllib.parse
from typing import Any, Dict, List, Optional

logger = logging.getLogger("supreme.git_mcp")

class GitMCPBridge:
    """
    Bridge to GitMCP (idosal/git-mcp), allowing AI models (Qwen3.6-35B, DeepSeek, Claude)
    to query real-time documentation and code directly from GitHub repositories without hallucinations.
    """

    BASE_URL = "https://gitmcp.io"

    @classmethod
    def get_repo_mcp_url(cls, owner: str, repo: str) -> str:
        """Returns the specific MCP server URL for a given GitHub repository."""
        return f"{cls.BASE_URL}/{owner}/{repo}"

    @classmethod
    def get_generic_docs_url(cls) -> str:
        """Returns the generic dynamic GitMCP endpoint."""
        return f"{cls.BASE_URL}/docs"

    @classmethod
    def generate_lmstudio_mcp_config(cls, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates the LM Studio MCP server definition snippet using mcp-remote.
        """
        target_url = cls.get_repo_mcp_url(owner, repo) if (owner and repo) else cls.get_generic_docs_url()
        npx_path = "/Users/rarescristea/.local/bin/npx" if os.path.exists("/Users/rarescristea/.local/bin/npx") else "npx"

        return {
            "command": npx_path,
            "args": [
                "-y",
                "mcp-remote",
                target_url
            ],
            "env": {
                "PATH": "/Users/rarescristea/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
            }
        }

    @classmethod
    def fetch_repo_docs(cls, owner: str, repo: str, path: str = "README.md") -> Dict[str, Any]:
        """
        Directly fetches raw documentation from GitHub via GitMCP endpoint or raw fallback.
        """
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Harness-Suprem-GitMCP/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8")
                return {
                    "owner": owner,
                    "repo": repo,
                    "path": path,
                    "content": content,
                    "status": "success",
                    "url": url,
                }
        except Exception as e:
            # Try master branch fallback
            fallback_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{path}"
            try:
                req = urllib.request.Request(
                    fallback_url,
                    headers={"User-Agent": "Harness-Suprem-GitMCP/1.0"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    content = resp.read().decode("utf-8")
                    return {
                        "owner": owner,
                        "repo": repo,
                        "path": path,
                        "content": content,
                        "status": "success",
                        "url": fallback_url,
                    }
            except Exception as e2:
                logger.error(f"Failed to fetch {owner}/{repo}/{path}: {e2}")
                return {
                    "owner": owner,
                    "repo": repo,
                    "path": path,
                    "content": "",
                    "status": "error",
                    "error": str(e2),
                }

    @classmethod
    def get_supported_catalogs(cls) -> List[Dict[str, str]]:
        """Common essential repositories pre-configured for instant zero-hallucination querying."""
        return [
            {"name": "mlx-swift", "owner": "ml-explore", "repo": "mlx-swift", "description": "Apple Silicon Swift machine learning framework"},
            {"name": "llama.cpp", "owner": "ggerganov", "repo": "llama.cpp", "description": "LLM inference in C/C++ with Apple Metal GPU support"},
            {"name": "gitingest", "owner": "coderamp-labs", "repo": "gitingest", "description": "Prompt-friendly codebase digestion for LLMs"},
            {"name": "git-mcp", "owner": "idosal", "repo": "git-mcp", "description": "Model Context Protocol documentation server"},
            {"name": "app-store-compliance", "owner": "mjmirza", "repo": "app-store-compliance", "description": "Apple App Store Review Guidelines compliance rules"},
            {"name": "ECC", "owner": "AFFAAN-M", "repo": "ECC", "description": "Enterprise Codebase Context & Agent Harness Operating System"},
        ]
