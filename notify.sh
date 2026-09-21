#!/bin/bash
# Copyright 2026 Scion Frontiers & Antigravity
# Direct status signaling from agent container to sciontool supervisor

STATUS="${1:-task_completed}"
MESSAGE="${2:-Turn completed}"

if command -v sciontool >/dev/null 2>&1; then
    sciontool status "$STATUS" --message "$MESSAGE" 2>/dev/null || true
else
    echo "[supreme-notify] Status: $STATUS | Message: $MESSAGE"
fi
