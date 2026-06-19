# Copyright 2026 sharkpicker
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Data quality gate for analyst reports.

Two-layer validation:
- Layer 1: Hard checks (empty, too short, failure markers, missing tables/data)
- Layer 2: LLM review (triggered when failure reports < threshold)

This is a derivative work of TradingAgents by TauricResearch.
https://github.com/TauricResearch/TradingAgents
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Minimum report length to be considered valid (characters)
MIN_REPORT_LENGTH = 200
# Minimum number of data references (numbers, percentages, dates) in report
MIN_DATA_REFERENCES = 3


def _count_data_references(text: str) -> int:
    """Count data-like references in report text."""
    if not text:
        return 0
    # Match numbers (with optional %, yuan, etc.), dates, percentages
    patterns = [
        r'\d+\.?\d*%',       # percentages
        r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',  # dates
        r'\d+\.?\d*\s*(亿|万|元|股|手|点)',  # Chinese units
        r'\d+\.?\d*\s*(million|billion|trillion)',  # English units
        r'\b\d{3,}\b',       # standalone numbers >= 100
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text))
    return count


def _has_table(text: str) -> bool:
    """Check if report contains a markdown table."""
    if not text:
        return False
    return bool(re.search(r'\|.+\|.*\n\|[-| ]+\|', text))


def _has_failure_markers(text: str) -> bool:
    """Check if report indicates data fetch failure."""
    if not text:
        return True  # empty = failure
    markers = [
        "NO_DATA_AVAILABLE",
        "ERROR:",
        "failed to retrieve",
        "unable to fetch",
        "data unavailable",
    ]
    text_lower = text.lower()
    return any(m.lower() in text_lower for m in markers)


def grade_report(report: str, report_name: str = "") -> tuple[str, str]:
    """Grade a single analyst report on data quality.

    Returns:
        (grade, reason) where grade is one of A/B/C/D/F
    """
    if not report or not report.strip():
        return "F", "Empty report"

    if len(report.strip()) < 50:
        return "F", "Report too short (< 50 chars)"

    if len(report.strip()) < MIN_REPORT_LENGTH:
        return "D", f"Report below minimum length ({len(report.strip())} < {MIN_REPORT_LENGTH})"

    if _has_failure_markers(report):
        # Check if the ENTIRE report is just error messages
        lines = [l.strip() for l in report.split('\n') if l.strip()]
        error_lines = sum(1 for l in lines if any(m in l for m in ["NO_DATA", "ERROR:", "failed"]))
        if error_lines > len(lines) * 0.5:
            return "D", "Majority of report contains error/failure messages"

    data_refs = _count_data_references(report)
    if data_refs < MIN_DATA_REFERENCES:
        return "C", f"Insufficient data references ({data_refs} < {MIN_DATA_REFERENCES})"

    has_table = _has_table(report)
    if has_table and data_refs >= 8:
        return "A", "Rich data with structured table"
    if has_table or data_refs >= 6:
        return "B", "Good data coverage"

    return "B", "Adequate data references"


def run_quality_gate(reports: dict[str, str]) -> dict[str, Any]:
    """Run Layer 1 quality gate on all analyst reports.

    Args:
        reports: dict mapping report_name -> report_content

    Returns:
        dict with 'grades', 'summary', 'failed_count'
    """
    grades = {}
    summary_parts = []

    for name, content in reports.items():
        g, reason = grade_report(content, name)
        grades[name] = {"grade": g, "reason": reason}
        status = "PASS" if g in ("A", "B") else "WARN" if g == "C" else "FAIL"
        summary_parts.append(f"  [{status}] {name}: Grade {g} - {reason}")

    failed_count = sum(1 for g in grades.values() if g["grade"] in ("D", "F"))

    summary = "Data Quality Assessment:\n" + "\n".join(summary_parts)
    if failed_count > 0:
        summary += f"\n\nWARNING: {failed_count} report(s) failed quality check. "
        summary += "Reduce reliance on low-confidence reports in investment decisions."

    return {
        "grades": grades,
        "summary": summary,
        "failed_count": failed_count,
    }


async def run_quality_gate_llm_review(
    reports: dict[str, str],
    quality_result: dict[str, Any],
    llm: Any,
) -> str:
    """Run Layer 2 LLM review when failure count is below threshold.

    The LLM reviews the quality assessment and provides additional insights
    about data reliability and potential biases.

    Args:
        reports: dict mapping report_name -> report_content
        quality_result: result from run_quality_gate
        llm: language model for review

    Returns:
        Enhanced quality summary string
    """
    if quality_result["failed_count"] >= 4:
        # Too many failures, LLM review won't help
        return quality_result["summary"]

    report_summaries = []
    for name, content in reports.items():
        preview = content[:500] if content else "(empty)"
        report_summaries.append(f"**{name}** (first 500 chars):\n{preview}")

    prompt = f"""You are a Data Quality Reviewer for an investment research system.
Review the following analyst reports and their quality grades. Provide a brief
assessment of overall data reliability and any concerns.

Quality Gate Results:
{quality_result['summary']}

Report Previews:
{chr(10).join(report_summaries)}

Provide a concise assessment (3-5 sentences) of:
1. Overall data reliability for making investment decisions
2. Which reports are most/least reliable and why
3. Any data gaps that could materially affect the analysis

Keep your response factual and specific."""

    try:
        response = await llm.ainvoke(prompt)
        return quality_result["summary"] + "\n\nLLM Quality Review:\n" + response.content
    except Exception as e:
        logger.warning("LLM quality review failed: %s", e)
        return quality_result["summary"]


__all__ = [
    "grade_report",
    "run_quality_gate",
    "run_quality_gate_llm_review",
]
