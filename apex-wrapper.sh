#!/bin/bash
# Copyright 2026 Scion Frontiers & Antigravity
# Apex Runtime Wrapper for Supreme Harness + VeRO Engine
# Combines: Git Token Isolation (OpenCode), Keyring Daemons (Antigravity), 
# Port Auto-Exposure (Hermes), Non-Interactive Autonomy (Grok), and VeRO Optimization.

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARNESS_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd 2>/dev/null || echo "${HOME}/.scion/harness")"

# 1. Isolate GITHUB_TOKEN to prevent tool credential confusion (from OpenCode)
if [ -n "${GITHUB_TOKEN:-}" ]; then
    export SCION_GIT_TOKEN="$GITHUB_TOKEN"
    unset GITHUB_TOKEN
fi

# 2. Initialize Headless DBus & Gnome Keyring for safe OAuth handling (from Antigravity)
if [ -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
    if command -v dbus-launch >/dev/null 2>&1; then
        eval $(dbus-launch --sh-syntax 2>/dev/null || true)
        export DBUS_SESSION_BUS_ADDRESS
    fi
fi

if command -v gnome-keyring-daemon >/dev/null 2>&1; then
    if ! pgrep gnome-keyring-daemon >/dev/null; then
        eval $(echo "supreme" | gnome-keyring-daemon --unlock 2>/dev/null || true)
        gnome-keyring-daemon --start --components=secrets,pkcs11,ssh >/dev/null 2>&1 || true
    fi
fi

# 3. Handle Special Subcommands (VeRO Conformance, Optimize, Evaluate, Login)
case "${1:-}" in
    --conformance)
        echo "[supreme-vero] Running Harness Conformance Test Suite..."
        python3 "${SCRIPT_DIR}/vero/conformance.py" 2>/dev/null || python3 "${HARNESS_DIR}/vero/conformance.py"
        exit $?
        ;;
    --optimize)
        echo "[supreme-vero] Triggering VeRO Recursive Hill-Climbing Optimization..."
        shift
        python3 -m vero.optimizer "$@"
        exit $?
        ;;
    --evaluate)
        echo "[supreme-vero] Triggering VeRO Trusted Evaluation..."
        shift
        python3 -m vero.evaluator "$@"
        exit $?
        ;;
    --gate)
        echo "[supreme-loopgate] Running LoopGate Strict Pre-Commit Quality Gates..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import sys
from core.gates.quality_gate import QualityGateRunner
runner = QualityGateRunner('${SCRIPT_DIR}')
test_cmd = ['python3', '-m', 'unittest', 'discover', '-s', 'tests'] if len(sys.argv) <= 1 else sys.argv[1:]
res = runner.run_all_gates(test_cmd)
print(f'Quality Gates Passed: {res.passed} (Mutation Score: {res.mutation_score:.1f}%, Duration: {res.duration_ms:.1f}ms)')
if not res.passed:
    print('Diagnostics:', res.diagnostics)
sys.exit(0 if res.passed else 1)
" "$@"
        exit $?
        ;;
    --skeptic)
        echo "[supreme-skeptic] Running Skeptical Evaluator Audit..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import sys
from core.skeptic.evaluator_session import SkepticalEvaluatorSession
evaluator = SkepticalEvaluatorSession()
verdict = evaluator.audit_task_completion('Task Audit', ['Requirement 1'], 'diff sample', {'passed': True})
print(f'Skeptical Verdict: {verdict.verdict} (Score: {verdict.score:.1f}%)')
sys.exit(0 if verdict.approved else 1)
" "$@"
        exit $?
        ;;
    --audit)
        echo "[better-harness] Running Better Harness 5-Dimension Work Loop Audit..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import sys, os
from core.audit import WorkLoopAuditor, HTMLReporter, TaskEpisode
auditor = WorkLoopAuditor()
episode = TaskEpisode(
    episode_id='EPISODE-LATEST',
    goal='Implement and verify enterprise features',
    prompts=['User request prompt'],
    tool_calls=[{'tool': 'exec', 'args': {'command': 'pytest'}}],
    code_diff='diff --git a/core.py b/core.py\n+ verified code',
    test_results={'passed': True},
    git_commits=['c0ffee1'],
)
report = auditor.evaluate_episode(episode)
out_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), 'better_harness_report.html')
HTMLReporter.render_report(report, out_file)
print(f'Audit Score: {report.overall_score}% across 5 dimensions.')
print(f'Generated Interactive HTML Report: {out_file}')
for dim_id, d in report.dimensions.items():
    print(f' - {d.name}: {d.score}%')
" "$@"
        exit $?
        ;;
    --security)
        echo "[autoharness-security] Running Security Governor (Secret Scrubber & Anti-Injection)..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import sys
from core.security import SecurityGovernor
gov = SecurityGovernor()
sample = sys.argv[1] if len(sys.argv) > 1 else 'echo test with sk-ant-1234567890abcdef12345678'
res = gov.inspect_prompt(sample)
print(f'Allowed: {res[\"allowed\"]}')
print(f'Risk Level: {res[\"risk_level\"]} (Score: {res[\"risk_score\"]})')
print(f'Sanitized text: {res[\"sanitized_prompt\"]}')
" "$@"
        exit $?
        ;;
    --tdd)
        echo "[oh-my-copilot-tdd] Running TDD Discipline Enforcer..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import sys
from core.gates import TDDEnforcer
files = sys.argv[1:] if len(sys.argv) > 1 else ['core/example.py', 'tests/test_example.py']
res = TDDEnforcer.evaluate_changes(files)
print(f'TDD Compliant: {res[\"compliant\"]}')
print(f'Phase: {res[\"phase\"]}')
print(f'Message: {res[\"message\"]}')
" "$@"
        exit $?
        ;;
    --apple-build)
        echo "[apple-builder] Building Swift/Xcode project with Swift 6 Strict Concurrency..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import sys, os
from core.apple import XcodeBuilder
target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
res = XcodeBuilder.run_swift_build(target_dir, strict_concurrency=True)
print(f'Build Succeeded: {res.success} in {res.duration_sec}s')
if res.diagnostics:
    print(f'Total Diagnostics: {len(res.diagnostics)}')
    for d in res.diagnostics[:5]:
        concurrency_tag = ' [SWIFT-6 CONCURRENCY]' if d.is_strict_concurrency else ''
        print(f' - [{d.severity.upper()}]{concurrency_tag} {d.file_path}:{d.line}:{d.column} -> {d.message}')
        if d.suggested_fix:
            print(f'   Suggestion: {d.suggested_fix}')
" "$@"
        exit $?
        ;;
    --apple-sim)
        echo "[apple-simctl] Apple Simulator Automation..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import sys
from core.apple import SimulatorManager
mgr = SimulatorManager()
action = sys.argv[1] if len(sys.argv) > 1 else 'list'
if action == 'list':
    devs = mgr.list_devices('iOS')
    print(f'Available iOS Simulators: {len(devs)}')
    for d in devs[:8]:
        print(f' - {d.name} ({d.state}) [{d.udid}]')
elif action == 'boot':
    udid = sys.argv[2] if len(sys.argv) > 2 else ''
    ok = mgr.boot_device(udid)
    print(f'Booted {udid}: {ok}')
" "$@"
        exit $?
        ;;
    --apple-hig)
        echo "[apple-hig] Running Apple Human Interface Guidelines & Accessibility Audit..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import sys, os
from core.apple import HIGAccessibilityAuditor
target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
report = HIGAccessibilityAuditor.audit_directory(target_dir)
print(f'HIG Compliance Score: {report.score}% across {report.total_files_scanned} files.')
if report.issues:
    print(f'Issues found: {len(report.issues)}')
    for iss in report.issues[:8]:
        print(f' - [{iss.rule_id} {iss.severity}] {iss.file_path}: {iss.message}')
        print(f'   Remediation: {iss.remediation}')
else:
    print('No HIG or VoiceOver accessibility issues detected!')
" "$@"
        exit $?
        ;;
    --apple-concurrency)
        echo "[apple-concurrency] Running Swift 6 Strict Concurrency & Swift Testing Gate..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import sys, os
from core.apple import SwiftConcurrencyGate
target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
res = SwiftConcurrencyGate.audit_directory(target_dir)
print(f'Swift 6 Concurrency Compliant: {res.is_compliant} ({res.total_files_scanned} files scanned)')
print(f'Swift Testing Suites: {res.swift_testing_suites} | XCTest Suites: {res.xctest_suites}')
if res.issues_found:
    print(f'Concurrency issues found: {len(res.issues_found)}')
    for iss in res.issues_found[:5]:
        print(f' - [{iss[\"type\"]}] {iss[\"file\"]}: {iss[\"message\"]}')
        print(f'   Suggestion: {iss[\"suggestion\"]}')
" "$@"
        exit $?
        ;;
    --apple-compliance)
        echo "[apple-compliance] Running Enterprise App Store Pre-Submission Compliance Audit (mjmirza/app-store-compliance)..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import sys, os
from core.apple import AppStoreComplianceAuditor
target_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else os.getcwd()
report = AppStoreComplianceAuditor.audit_project(target_dir)
print(f'App Store Compliance Score: {report.score}% across {report.total_files_scanned} files.')
print(f'Compliant (Release Gate): {report.is_compliant}')
print(f'Critical (Blockers): {report.critical_count} | High: {report.high_count} | Medium: {report.medium_count} | Low: {report.low_count}')
if report.findings:
    print('Identified Rejection Risks:')
    for f in report.findings[:8]:
        print(f' - [{f.severity.upper()}] Guideline {f.guideline} ({f.pattern_id}): {f.title}')
        print(f'   File: {f.file_path}:{f.line_number}')
        print(f'   Fix: {f.fix_recommendation}')
if report.appeal_recommendations:
    print('Review & Appeal Strategy:')
    for a in report.appeal_recommendations:
        print(f' * {a}')
" "$@"
        exit $?
        ;;
    --desktop)
        echo "[supreme-desktop] Launching Harness-Suprem Native Desktop App (Apple MLX Engine)..."
        shift
        APP_PATH="/Users/rarescristea/Desktop/Harness-Suprem.app"
        if [ ! -d "$APP_PATH" ]; then
            echo "[supreme-desktop] App bundle not found, compiling now..."
            "${SCRIPT_DIR}/desktop/build_app.sh"
        fi
        open "$APP_PATH"
        echo "[supreme-desktop] Harness-Suprem.app is now running on your Desktop!"
        exit 0
        ;;
    --memory-status)
        echo "[mempalace] Querying MemPalace live memory palace status..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
from core.memory import MemPalaceBridge
st = MemPalaceBridge.get_status()
print(f'MemPalace Available: {st[\"is_available\"]}')
print(f'Total Drawers Filed: {st[\"total_drawers\"]}')
print(f'Knowledge Graph Entities: {st[\"entities_count\"]} | Triples: {st[\"triples_count\"]}')
print(f'Cognitive Diary Entries: {st[\"diary_entries\"]}')
print(f'Palace Storage Path: {st[\"palace_path\"]}')
" "$@"
        exit $?
        ;;
    --memory-wake)
        echo "[mempalace] Retrieving L0 (Identity) & L1 (Essential Story) Wake-Up Context..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
from core.memory import MemPalaceBridge
print(MemPalaceBridge.get_wake_up_context())
" "$@"
        exit $?
        ;;
    --memory-search)
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import sys
from core.memory import MemPalaceBridge
q = sys.argv[1] if len(sys.argv) > 1 else 'architecture'
print(f'[mempalace] Searching memories for: \"{q}\"...')
results = MemPalaceBridge.search_memory(q)
if results:
    for idx, r in enumerate(results, 1):
        print(f' {idx}. [{r.get(\"source\", \"drawer\")}] {r.get(\"snippet\", r.get(\"name\", \"\"))}')
else:
    print('No direct matches found in current drawers.')
" "$@"
        exit $?
        ;;
    --engine-status)
        echo "[dual-engine] Querying Dual-Engine (MLX + llama.cpp) Status..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import json
from core.engine import DualEngineRouter
router = DualEngineRouter()
print(json.dumps(router.get_status(), indent=2))
" "$@"
        exit $?
        ;;
    --llama-start)
        echo "[llama.cpp] Starting llama-server on Metal GPU (Port 5249)..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
from core.engine import LlamaBridge
bridge = LlamaBridge()
ok = bridge.start()
print(f'llama-server online: {ok}')
" "$@"
        exit $?
        ;;
    --llama-stop)
        echo "[llama.cpp] Stopping llama-server daemon..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
from core.engine import LlamaBridge
bridge = LlamaBridge()
ok = bridge.stop()
print(f'llama-server stopped: {ok}')
" "$@"
        exit $?
        ;;
    --llama-status)
        echo "[llama.cpp] Querying llama-server status..."
        shift
        PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}" python3 -c "
import json
from core.engine import LlamaBridge
bridge = LlamaBridge()
print(json.dumps(bridge.get_status(), indent=2))
" "$@"
        exit $?
        ;;
    --login)
        echo "==========================================================="
        echo "  Supreme Harness Interactive Authentication Shell"
        echo "==========================================================="
        echo "Provide one of the supported credentials:"
        echo "  - export DEEPSEEK_API_KEY='sk-...'"
        echo "  - export ANTHROPIC_API_KEY='sk-ant-...'"
        echo "  - export OPENAI_API_KEY='sk-proj-...'"
        echo "  - export GEMINI_API_KEY='AIza...'"
        echo "  - gcloud auth application-default login"
        echo ""
        echo "After setting credentials, run:"
        echo "  python3 /home/scion/.scion/harness/capture_auth.py"
        echo "==========================================================="
        exec /bin/zsh
        ;;
esac

# 4. Verify Active Plugins & Manifest
SUPREME_HOME="${HOME}/.supreme"
PLUGINS_MANIFEST="${SUPREME_HOME}/plugins/manifest.json"

if [ -f "$PLUGINS_MANIFEST" ]; then
    ACTIVE_COUNT=$(jq -r '.total_plugins // 16' "$PLUGINS_MANIFEST" 2>/dev/null || echo "16")
    echo "[supreme] Initialized runtime with $ACTIVE_COUNT active system plugins."
fi

# 5. Trap Termination Signals for Graceful State Flushes
cleanup() {
    echo "[supreme] Received shutdown signal; performing graceful flush..."
    if [ -f "/home/scion/.scion/harness/notify.sh" ]; then
        /home/scion/.scion/harness/notify.sh blocked "Agent container interrupted" 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM

# 6. Default Fallback or Command Execution
if [ $# -eq 0 ]; then
    exec /bin/zsh
else
    # Execute the requested agent process
    exec "$@"
fi
