# Supreme Coding Harness (Scion Bundle + VeRO Engine)

The **Supreme Harness** (`scion-supreme`) is an all-in-one, enterprise-grade harness bundle for [Scion](https://github.com/GoogleCloudPlatform/scion) that synthesizes the premier features from all 9 canonical harnesses (`claude`, `gemini-cli`, `antigravity`, `codex`, `copilot`, `grok-build`, `hermes`, `muse-code`, `opencode`), introduces native support for **DeepSeek (V3 & R1)**, bundles **16 persistent system plugins**, and integrates the **VeRO** (*Scale AI: Versioned Evaluation & Recursive Optimization*, ICML 2026) recursive self-improvement engine.

---

## 🌟 Key Architectural Features Inherited

1. **Anti-SSRF & Network Sandbox (`init-firewall.sh`)** — *From `claude`*
   * Hardware-level network rules preventing container access to Cloud Metadata (`169.254.169.254`), while whitelisting all verified model API endpoints.
2. **Fine-Grained Token Telemetry & FinOps** — *From `muse-code`*
   * Complete lifecycle extraction of `input_tokens`, `output_tokens`, `cached_tokens`, and DeepSeek `reasoning_tokens` to prevent runaway spending loops.
3. **Full Non-Interactive Autonomy** — *From `grok-build`*
   * `--yolo --dangerously-skip-permissions` execution without user stdin blocking; context compaction events (`PreCompact` / `PostCompact`).
4. **Push-Based Completion Signaling (`notify.sh`)** — *From `codex`*
   * Active callback push to `sciontool status` (`task_completed`, `blocked`, `ask_user`) rather than relying purely on passive stderr polling.
5. **Headless Secret Keyring** — *From `antigravity`*
   * Background `dbus-launch` and `gnome-keyring-daemon` for managing OAuth sessions securely in container memory.
6. **Auto-Expose Ports & Web Previews** — *From `hermes`*
   * Direct forwarding of ports `8080` (app web preview), `9119` (observability/metrics), and `9120` (VeRO Trusted Evaluator Sidecar).
7. **Git Credential Isolation** — *From `opencode`*
   * Renames `GITHUB_TOKEN` to `SCION_GIT_TOKEN` to prevent confusion with LLM provider credentials.
8. **Hybrid Identity & Cloud ADC** — *From `gemini-cli`*
   * Universal provider resolution across API keys, personal OAuth, and Google Cloud Vertex AI ADC.
9. **Reasoning Engine Support (DeepSeek-R1 / V3)** — *DeepSeek Integration*
   * Handles `<think> ... </think>` reasoning blocks and long-thought traces without premature timeout.
10. **Recursive Optimization & Conformance (`vero/`)** — *From Scale AI `VeRO`*
    * Versioned Evaluation & Recursive Optimization: Git worktree candidate branching, Pareto multi-objective evaluation (Accuracy vs Latency vs Cost), and strict FinOps budget metering.

---

## 🧬 VeRO Optimization Architecture

VeRO enables **Agents to Optimize Agents** via a durable, versioned loop:

```
[Baseline Repo] ──> [Git Worktree Candidate] ──> [Execution & Tooling]
                          │                              │
                          ▼                              ▼
                 [Rollback if Regressed]        [Trusted Evaluator Sidecar]
                          ▲                              │
                          └──── [Commit if Pareto+ ] <───┘
```

### VeRO Subcommands
* **Conformance Test**: Verify all providers, tools, and 16 plugins before starting work:
  ```sh
  ./apex-wrapper.sh --conformance
  ```
* **Trusted Evaluation**: Score a target candidate against automated benchmarks:
  ```sh
  ./apex-wrapper.sh --evaluate --test "pytest tests/"
  ```
* **Recursive Hill-Climbing**: Run autonomous optimization loop:
  ```sh
  ./apex-wrapper.sh --optimize --iterations 10
  ```

---

## 🛡️ Advanced Harness Engineering Scaffolding (`core/`)

The harness incorporates the core engineering primitives from leading research repositories:

1. **Harness-Coder 1.3.3 Resilience Engine (`core/resilience/`)**:
   * **Tolerant Action Normalizer**: Unwraps JSON from markdown fences, stripped explanatory comments, and nested wrappers (`next_action`, `tool_calls`).
   * **Capped Exponential Backoff Retry**: Automatic recovery from transient HTTP 429/5xx errors, emitting structured `model_retry` events in telemetry.

2. **LoopGate Quality Guardrails (`core/gates/`)**:
   * **Multi-Stage Pre-Commit Gates**: Enforces syntax checking, 100% test pass rate, and AST-based **mutation verification** (detecting hollow `assert True` tests) before any code lands.
   * Run manually via:
     ```sh
     ./apex-wrapper.sh --gate
     ```

3. **Skeptical QA & Machine-Parseable State (`core/skeptic/`)**:
   * **Independent Auditor Pattern**: Separate evaluation session that audits work against explicit acceptance criteria without generous agent self-bias.
   * **Durable JSON State**: Plans (`.supreme/plans/*.json`) and verdicts (`.supreme/eval_verdicts/*.json`) persist cleanly across context compaction.

4. **Enterprise CI/CD Governance (`core/enterprise/`)**:
   * Synthesizes production CI/CD pipelines, triages failed build logs, and provides real-time cloud resource cost estimates.

5. **Better Harness Work Loop Audit & Feedback Closure (`core/audit/`)**:
   * **5-Dimension Work Loop Evaluation**: Task Understanding, Controlled Execution, Change Validation, Reliable Delivery, and Learning Capture evaluated across 15 discrete criteria.
   * **7 Evidence States**: Replaces ambiguous pass/fail with concrete evidence states (`Present`, `Wired`, `Exercised`, `Outcome-supported`, `Missing`, `Unobserved`, `Not applicable`).
   * **Interactive HTML Report**: Self-contained visual report with collapsible evidence drawer and progress meters.
   * **Learning Capture Feedforward Loop**: Audits synthesize durable rules and append them directly to `.supreme/AGENTS.md`.
   * Run manually via:
     ```sh
     ./apex-wrapper.sh --audit
     ```

6. **AutoHarness Active Security & Governance (`core/security/`)**:
   * **Secret Scrubber**: Dual regex and Shannon entropy scanner detecting leaked credentials (Anthropic, OpenAI, GitHub, AWS, private keys) and high-entropy hashes.
   * **Prompt-Injection Defense**: Pre-flight analyzer neutralizing instruction override, jailbreaks, and delimiter tampering.
   * **Destructive Command Interceptor**: Proactively blocks dangerous shell operations (e.g. `rm -rf /`, `mkfs`, fork bombs).
   * Run manually via:
     ```sh
     ./apex-wrapper.sh --security "<text>"
     ```

7. **oh-my-githubcopilot TDD Discipline & Consensus Planning (`core/gates/`)**:
   * **TDD Enforcer**: Blocks production code modifications unless accompanied or preceded by test suites (Red-Green-Refactor enforcement).
   * **Triumvirate Consensus**: Multi-persona sign-off (Architect, Security Auditor, Test Lead) before accepting high-impact proposals.
   * Run manually via:
     ```sh
     ./apex-wrapper.sh --tdd [files...]
     ```

8. **Brat Crash-Safe Append-Only Journal (`core/storage/`)**:
   * **Gritee Architecture**: Atomic SHA-256 checksummed JSONL event logging with automatic truncation recovery from process crashes or `SIGKILL`.
   * **Multi-Agent Convoy Locking**: Concurrency controls for parallel agents sharing worktrees.

9. **pat-jj/harness-1 Stateful Evidence Graph (`core/evidence/`)**:
   * Directed knowledge network linking claims, source documents, and contradictions, enabling long-horizon research without prompt context flooding.

10. **Harness-R1 / Harness-Evolver Meta-Harness Loop (`core/evolution/`)**:
    * Reflective engineer engine proposing self-healing patches to prompts, gates, and runtime configurations based on failure trajectories, validated through VeRO.

11. **Apple Native Development Suite (`core/apple/`)**:
    * **Xcode & Swift 6 Build Diagnostics**: Parses strict concurrency compiler outputs, data races, `@MainActor` violations, and structured test results from `.xcresult`.
    * **Simulator Automation (`simctl`)**: Full device lifecycle, app deployment, clean status bar overrides (9:41 AM), privacy permission management, and visual QA screenshots.
    * **Codesign & Notarization**: Validates hardened runtime, extracts binary entitlements, and manages Apple Notary Service submissions via `notarytool`.
    * **Swift Concurrency Gate**: Enforces `@MainActor` on ViewModels, `Sendable` boundary conformance, and modern `Swift Testing` (`@Test`, `@Suite`, `#expect`).
    * **Human Interface Guidelines (HIG) & Accessibility Auditor**: Automated SwiftUI linting for VoiceOver `.accessibilityLabel`, Dynamic Type scaling, and 44pt minimum touch targets.
    * Run manually via:
      ```sh
      ./apex-wrapper.sh --apple-build [target]
      ./apex-wrapper.sh --apple-sim list
      ./apex-wrapper.sh --apple-hig [views_dir]
      ./apex-wrapper.sh --apple-concurrency [dir]
      ```

---

## 🧩 The 17 Built-in System Plugins

The harness comes with 17 system plugins pre-registered in `plugins/plugin_manager.py` and exported to `~/.supreme/plugins/manifest.json`:

| # | Plugin Name | Category | Description |
|---|---|---|---|
| 1 | **`anthropic`** | Provider | Claude 3.5 Sonnet / Opus / Haiku connector and runner |
| 2 | **`openai`** | Provider | GPT-4o, o1, and o3 reasoning model connector |
| 3 | **`xai`** | Provider | Grok 3 / 4 reasoning engine with fast inference |
| 4 | **`nvidia`** | Provider | NVIDIA NIM Cloud provider for DeepSeek-V3 and DeepSeek-R1 |
| 5 | **`ollama`** | Provider | Offline and air-gapped local model runner for zero-leakage enterprise workloads |
| 6 | **`apple-developer`**| Platform | Native compiler diagnostics (Xcode/Swift 6), simctl control, notarytool and HIG/a11y auditor |
| 7 | **`codex`** | Execution | Code synthesis, AST inspection, test generation & smart patching |
| 8 | **`linux-node`** | Execution | Container execution supervisor, process sandbox control, sysinfo & metrics |
| 9 | **`cua-computer`**| Execution | Computer-Use Agent (CUA) for desktop automation, GUI interaction, mouse & keyboard |
| 10 | **`browser`** | Interaction | Headless browser automation, web search, DOM tree extraction and screenshots |
| 11 | **`canvas`** | Interaction | Generative UI renderer, live interactive component preview and visual canvas |
| 12 | **`talk-voice`** | Interaction | Bidirectional voice streaming, speech-to-text audio ingestion and voice synthesis |
| 13 | **`bonjour`** | System | mDNS / Zero-conf local service discovery for adjacent agent swarms and sidecars |
| 14 | **`device-pair`**| System | Secure cryptographic device pairing and multi-node worktree coordination |
| 15 | **`file-transfer`**| System | High-speed encrypted file synchronization and artifact staging between host and agent |
| 16 | **`geolocation`**| Context | Contextual localization, timezone normalization and geo-aware environmental presets |
| 17 | **`memory-core`**| Memory | Persistent episodic and semantic memory with vector retrieval (MemPalace integration) |

---

## 🚀 Quickstart & Installation in Scion

Install the bundle directly into your local Scion environment:

```sh
scion harness-config install /Users/rarescristea/Desktop/harness-suprem
```

Or run an agent with the Supreme harness:

```sh
scion agent create my-supreme-agent --harness supreme --model large
```

### Model Aliases
* **`small`**: `deepseek-ai/deepseek-v3` (Ultra-low cost, high throughput)
* **`medium`**: `anthropic/claude-sonnet-4` (Balanced coding powerhouse)
* **`large`**: `deepseek-ai/deepseek-r1` (Deep reasoning & algorithmic problem solving)
* **`extra-large`**: `anthropic/claude-opus-4` (Maximum architectural capability)
