#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Container-side provisioner for Supreme Harness

import os
import sys
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scion_harness
from plugins.plugin_manager import export_plugins_manifest, ALL_16_PLUGINS

assert scion_harness.INTERFACE_VERSION >= 2

logger = logging.getLogger("supreme.provision")

AUTH = scion_harness.AuthSpec(
    "supreme",
    [
        scion_harness.env_method(
            "api-key",
            any_of=[
                "DEEPSEEK_API_KEY",
                "ANTHROPIC_API_KEY",
                "OPENAI_API_KEY",
                "GEMINI_API_KEY",
                "GOOGLE_API_KEY",
                "XAI_API_KEY",
                "NVIDIA_API_KEY",
            ],
            hint="Set one of DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, XAI_API_KEY, or NVIDIA_API_KEY",
            env_fallback=True,
        ),
        scion_harness.file_method(
            "oauth-token",
            path="~/.supreme/oauth_token.json",
            hint="Stage OAuth credentials at ~/.supreme/oauth_token.json",
        ),
        scion_harness.file_method(
            "auth-file",
            path="~/.supreme/auth.json",
            hint="Stage custom auth JSON at ~/.supreme/auth.json",
        ),
        scion_harness.env_method(
            "vertex-ai",
            any_of=["VERTEX_PROJECT_ID", "GOOGLE_CLOUD_PROJECT"],
            hint="Set GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CLOUD_PROJECT for Vertex AI execution",
            env_fallback=True,
        ),
    ],
    fallback_to_none_on_error=True,
)

def provision(ctx: scion_harness.ProvisionContext) -> None:
    auth = ctx.select_auth(AUTH)

    home = os.path.expanduser("~")
    supreme_dir = os.path.join(home, ".supreme")
    plugins_dir = os.path.join(supreme_dir, "plugins")
    skills_dir = os.path.join(supreme_dir, "skills")
    os.makedirs(plugins_dir, exist_ok=True)
    os.makedirs(skills_dir, exist_ok=True)

    # 1. Export manifest for the 16 system plugins
    manifest_path = os.path.join(plugins_dir, "manifest.json")
    export_plugins_manifest(manifest_path)
    logger.info("Exported 16 built-in plugins manifest to %s", manifest_path)

    # 2. Project system prompt and agent instructions
    instructions_file = os.path.join(supreme_dir, "AGENTS.md")
    scion_harness.project_instructions(
        instructions_file,
        header="<!-- SUPREME HARNESS MANAGED BLOCK -->\n",
        footer="<!-- END SUPREME HARNESS BLOCK -->\n",
    )

    # 3. Setup MCP configuration
    mcp_config_file = os.path.join(supreme_dir, "mcp_config.json")
    scion_harness.apply_mcp_servers_simple(
        ctx,
        config_path=mcp_config_file,
        root_key="mcpServers",
        transport_field="type",
    )

    # 4. Resolve model overlay environment
    out_env = {
        "SUPREME_HOME": supreme_dir,
        "SUPREME_PLUGINS_MANIFEST": manifest_path,
        "SUPREME_ACTIVE_PLUGINS_COUNT": str(len(ALL_16_PLUGINS)),
    }

    # Pass through active API keys if present
    for k in [
        "DEEPSEEK_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "XAI_API_KEY",
        "NVIDIA_API_KEY",
    ]:
        val = os.environ.get(k)
        if val:
            out_env[k] = val

    ctx.write_outputs(auth, env=out_env)
    logger.info("Supreme Harness provisioning completed successfully.")

if __name__ == "__main__":
    scion_harness.run("supreme", provision)
