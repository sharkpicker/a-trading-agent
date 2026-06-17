"""China A-Share macro data via akshare."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

logger = logging.getLogger(__name__)


def get_macro_indicators(
    indicators: Annotated[list[str], "list of macro indicators to fetch"] = None
):
    """Get China macroeconomic indicators via akshare.

    Returns Label: Value text with header, matching FRED format.
    """
    if indicators is None:
        indicators = [
            "cpi",
            "ppi",
            "pmi",
            "m2",
            "interest_rate",
            "unemployment",
        ]

    lines = []

    for ind in indicators:
        try:
            import akshare as ak

            if ind == "cpi":
                df = ak.macro_china_cpi()
                if not df.empty:
                    latest = df.iloc[-1]
                    val = latest.get("今值", "N/A")
                    lines.append(f"China CPI YoY: {val}%")

            elif ind == "ppi":
                df = ak.macro_china_ppi()
                if not df.empty:
                    latest = df.iloc[-1]
                    val = latest.get("今值", "N/A")
                    lines.append(f"China PPI YoY: {val}%")

            elif ind == "pmi":
                df = ak.macro_china_pmi()
                if not df.empty:
                    latest = df.iloc[-1]
                    val = latest.get("今值", "N/A")
                    lines.append(f"China Manufacturing PMI: {val}")

            elif ind == "m2":
                df = ak.macro_china_m2()
                if not df.empty:
                    latest = df.iloc[-1]
                    val = latest.get("今值", "N/A")
                    lines.append(f"China M2 Money Supply YoY: {val}%")

            elif ind == "interest_rate":
                df = ak.macro_china_lpr()
                if not df.empty:
                    latest = df.iloc[-1]
                    lpr_1y = latest.get("1年期LPR", "N/A")
                    lpr_5y = latest.get("5年期LPR", "N/A")
                    lines.append(f"China 1-Year LPR: {lpr_1y}%")
                    lines.append(f"China 5-Year LPR: {lpr_5y}%")

            elif ind == "unemployment":
                df = ak.macro_china_urban_unemployment()
                if not df.empty:
                    latest = df.iloc[-1]
                    val = latest.get("今值", "N/A")
                    lines.append(f"China Urban Unemployment Rate: {val}%")

        except Exception as e:
            logger.warning("akshare macro indicator %s failed: %s", ind, e)
            lines.append(f"{ind}: Error fetching data - {str(e)}")

    if not lines:
        return "No macro indicators available."

    header = "# China Macro Indicators\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    return header + "\n".join(lines)
