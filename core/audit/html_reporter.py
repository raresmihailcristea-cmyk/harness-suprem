#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Better Harness (QoderAI) Self-Contained Interactive HTML Reporter

from __future__ import annotations
import json
import os
import time
from typing import Optional

from .models import AuditReport, DimensionId, EvidenceState

class HTMLReporter:
    """Renders a self-contained interactive HTML audit report with Evidence Drawer and timeline."""

    @staticmethod
    def render_report(report: AuditReport, output_path: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # Dimension color codes
        def get_score_color(score: float) -> str:
            if score >= 80:
                return "#10b981"  # green
            elif score >= 60:
                return "#f59e0b"  # amber
            return "#ef4444"      # red

        # Generate Dimension Cards HTML
        dim_cards_html = ""
        for dim_id, dim in report.dimensions.items():
            color = get_score_color(dim.score)
            checks_html = ""
            for c in dim.checks:
                badge_bg = {
                    EvidenceState.OUTCOME_SUPPORTED: "#059669",
                    EvidenceState.EXERCISED: "#10b981",
                    EvidenceState.WIRED: "#3b82f6",
                    EvidenceState.PRESENT: "#6b7280",
                    EvidenceState.UNOBSERVED: "#9ca3af",
                    EvidenceState.MISSING: "#ef4444",
                    EvidenceState.NOT_APPLICABLE: "#4b5563",
                }.get(c.state, "#6b7280")

                ev_str = " | ".join(c.evidence) if c.evidence else "No direct trace"
                checks_html += f"""
                <div class="check-item">
                    <div class="check-header">
                        <span class="check-name">{c.name}</span>
                        <span class="state-badge" style="background-color: {badge_bg};">{c.state.value}</span>
                    </div>
                    <div class="check-summary">{c.summary}</div>
                    <div class="evidence-trace"><strong>Trace:</strong> {ev_str}</div>
                </div>
                """

            dim_cards_html += f"""
            <div class="dimension-card">
                <div class="dimension-header">
                    <h3>{dim.name}</h3>
                    <span class="dimension-score" style="color: {color};">{dim.score}%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {dim.score}%; background-color: {color};"></div>
                </div>
                <p class="dimension-question">{dim.question}</p>
                <details class="evidence-drawer">
                    <summary>View Evidence Drawer ({len(dim.checks)} Checks)</summary>
                    <div class="drawer-content">
                        {checks_html}
                    </div>
                </details>
            </div>
            """

        # Generate Findings HTML
        findings_html = ""
        if not report.findings:
            findings_html = "<div class='no-findings'>✅ No blocking workflow defects detected. Agent loop executed within parameters.</div>"
        else:
            for f in report.findings:
                acc_checks = "".join(f"<li>{chk}</li>" for chk in f.acceptance_checks)
                findings_html += f"""
                <div class="finding-card severity-{f.severity.lower()}">
                    <div class="finding-header">
                        <span class="finding-id">{f.finding_id}</span>
                        <h4>{f.title}</h4>
                        <span class="severity-badge">{f.severity}</span>
                    </div>
                    <div class="finding-body">
                        <p><strong>Impact:</strong> {f.impact}</p>
                        <p><strong>Expected:</strong> {f.expected_output}</p>
                        <div class="ai-fix">
                            <strong>Scoped AI Fix:</strong>
                            <code>{f.scoped_ai_fix}</code>
                        </div>
                        <div class="acceptance-checks">
                            <strong>Acceptance Checks:</strong>
                            <ul>{acc_checks}</ul>
                        </div>
                    </div>
                </div>
                """

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Better Harness Audit Report - {report.report_id}</title>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #38bdf8;
            --border: #334155;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            margin: 0;
            padding: 2rem;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        .overall-score {{
            font-size: 2.5rem;
            font-weight: 800;
            color: {get_score_color(report.overall_score)};
            background: rgba(255,255,255,0.05);
            padding: 0.5rem 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border);
        }}
        .dimensions-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}
        .dimension-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
        }}
        .dimension-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .dimension-score {{
            font-size: 1.4rem;
            font-weight: 700;
        }}
        .progress-bar-bg {{
            background: rgba(255,255,255,0.1);
            height: 8px;
            border-radius: 4px;
            margin: 1rem 0;
            overflow: hidden;
        }}
        .progress-bar-fill {{
            height: 100%;
            border-radius: 4px;
        }}
        .dimension-question {{
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }}
        details.evidence-drawer summary {{
            cursor: pointer;
            color: var(--accent);
            font-weight: 600;
            font-size: 0.85rem;
            user-select: none;
        }}
        .drawer-content {{
            margin-top: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}
        .check-item {{
            background: rgba(0,0,0,0.2);
            padding: 0.75rem;
            border-radius: 8px;
            border-left: 3px solid var(--accent);
        }}
        .check-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.25rem;
        }}
        .state-badge {{
            font-size: 0.75rem;
            padding: 0.2rem 0.6rem;
            border-radius: 9999px;
            color: #fff;
            font-weight: 600;
        }}
        .check-summary {{
            font-size: 0.85rem;
            color: var(--text-primary);
        }}
        .evidence-trace {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }}
        .findings-section h2 {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 0.75rem;
            margin-bottom: 1.5rem;
        }}
        .finding-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border-left: 6px solid #f59e0b;
        }}
        .severity-high {{ border-left-color: #ef4444; }}
        .severity-medium {{ border-left-color: #f59e0b; }}
        .finding-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        .finding-id {{
            background: rgba(255,255,255,0.1);
            padding: 0.2rem 0.5rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 700;
        }}
        .ai-fix code {{
            display: block;
            background: rgba(0,0,0,0.3);
            padding: 0.75rem;
            border-radius: 6px;
            margin-top: 0.5rem;
            color: #38bdf8;
        }}
        .no-findings {{
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid #10b981;
            padding: 1.5rem;
            border-radius: 12px;
            color: #10b981;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="brand">
                <div>
                    <h1>Better Harness Work Loop Audit</h1>
                    <p style="color: var(--text-secondary); margin: 0;">Task Episode: <strong>{report.episode_id}</strong> | Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}</p>
                </div>
            </div>
            <div class="overall-score">
                {report.overall_score}%
            </div>
        </header>

        <section>
            <h2>The Five Agent Work Loop Dimensions</h2>
            <div class="dimensions-grid">
                {dim_cards_html}
            </div>
        </section>

        <section class="findings-section">
            <h2>Prioritized Findings & Scoped AI Repairs ({len(report.findings)})</h2>
            <div class="findings-container">
                {findings_html}
            </div>
        </section>
    </div>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)

        return output_path
