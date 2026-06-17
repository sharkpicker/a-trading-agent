# Modifications Copyright 2026 sharkpicker
# Original work Copyright TauricResearch
# Licensed under the Apache License, Version 2.0.
# See LICENSE for details.

"""Symbol normalization and market-data error types for vendor calls.

Yahoo Finance (the default vendor) uses specific ticker conventions that
differ from the broker / TradingView / MT5 style symbols users often type:

    user types        Yahoo wants       why
    ---------------   ---------------   -----------------------------------
    XAUUSD, XAUUSD+   GC=F              gold has no forex pair on Yahoo;
                                        it is quoted as a COMEX future
    EURUSD            EURUSD=X          spot forex pairs take a ``=X`` suffix
    BTCUSD            BTC-USD           crypto pairs use a ``-`` separator
    SPX500, US500     ^GSPC             index CFDs map to Yahoo index symbols

A-Share (China stock) symbols are also supported:
    user types        Canonical         exchange
    ---------------   ---------------   -----------------------------------
    000001            000001.SZ         Shenzhen
    600000            600000.SS         Shanghai
    688001            688001.SS         Shanghai STAR Market
    300001            300001.SZ         Shenzhen ChiNext

Passing the raw broker symbol to Yahoo returns an empty result, which the
agents previously received as free text and could hallucinate a price
around (see issue #781). Centralizing the mapping here means every yfinance
entry point resolves symbols the same way, and new instruments are added by
appending a table row rather than editing call sites.
"""

from __future__ import annotations

import logging
import re

# NoMarketDataError lives in the vendor-error taxonomy (errors.py); re-exported
# here for the many call sites that import it alongside normalize_symbol.
from .errors import NoMarketDataError as NoMarketDataError

logger = logging.getLogger(__name__)


# ISO-4217 codes common enough to appear in retail forex pairs. A bare
# six-letter symbol whose halves are BOTH in this set is treated as a spot
# forex pair and given Yahoo's ``=X`` suffix.
_FOREX_CURRENCIES = frozenset(
    {
        "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
        "CNY", "CNH", "HKD", "SGD", "SEK", "NOK", "DKK", "PLN",
        "MXN", "ZAR", "TRY", "INR", "KRW", "BRL", "RUB", "THB",
    }
)

# Crypto bases that brokers quote against USD without a separator.
_CRYPTO_BASES = frozenset(
    {"BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "LTC", "BCH", "DOT", "AVAX", "LINK"}
)

# Explicit aliases for instruments whose broker symbol does not map to a
# Yahoo symbol by rule. Metals/energy resolve to their front-month future;
# index CFD names resolve to the underlying Yahoo index symbol. Extend by
# adding rows — no call site changes required.
_ALIASES = {
    # Precious metals (spot names -> COMEX/NYMEX futures)
    "XAUUSD": "GC=F", "XAU": "GC=F", "GOLD": "GC=F",
    "XAGUSD": "SI=F", "XAG": "SI=F", "SILVER": "SI=F",
    "XPTUSD": "PL=F", "XPDUSD": "PA=F",
    # Energy
    "WTICOUSD": "CL=F", "USOIL": "CL=F", "WTI": "CL=F",
    "BCOUSD": "BZ=F", "UKOIL": "BZ=F", "BRENT": "BZ=F",
    "NATGAS": "NG=F", "XNGUSD": "NG=F",
    "COPPER": "HG=F", "XCUUSD": "HG=F",
    # Index CFDs -> Yahoo index symbols
    "SPX500": "^GSPC", "US500": "^GSPC", "SPX": "^GSPC",
    "NAS100": "^NDX", "US100": "^NDX", "USTEC": "^NDX",
    "US30": "^DJI", "DJI30": "^DJI", "WS30": "^DJI",
    "GER40": "^GDAXI", "GER30": "^GDAXI", "DE40": "^GDAXI",
    "UK100": "^FTSE", "JP225": "^N225", "JPN225": "^N225",
    "FRA40": "^FCHI", "EU50": "^STOXX50E", "HK50": "^HSI",
}

# China A-Share exchange suffixes
_CHINA_EXCHANGE_SUFFIXES = (".SS", ".SZ", ".BJ")

# China A-Share code patterns: exchange determined by code prefix
_CHINA_SH_PREFIXES = ("600", "601", "603", "605", "688")
_CHINA_SZ_PREFIXES = ("000", "001", "002", "003", "300")
_CHINA_BJ_PREFIXES = ("4", "8")

# Yahoo symbols may contain letters, digits, and these structural characters.
_YAHOO_SAFE = re.compile(r"^[A-Za-z0-9._\-\^=]+$")


# Crypto quote currencies that all map to Yahoo's USD pair. Yahoo lists only
# ``<BASE>-USD`` (not the USDT/USDC stablecoin pairs), so a broker symbol quoted
# in any of these resolves to ``-USD`` (#982). Longest first so ``USDT``/``USDC``
# match before the ``USD`` substring.
_CRYPTO_QUOTES = ("USDT", "USDC", "USD")


def _normalize_crypto(s: str) -> str | None:
    """Return ``<BASE>-USD`` if ``s`` is a known crypto quoted in USD/USDT/USDC.

    Accepts dashed or undashed forms: ``BTCUSD``, ``BTCUSDT``, ``BTC-USDT``,
    ``BTC-USDC`` all resolve to ``BTC-USD``. Returns None otherwise.
    """
    compact = s.replace("-", "")
    for quote in _CRYPTO_QUOTES:
        if compact.endswith(quote):
            base = compact[: -len(quote)]
            if base in _CRYPTO_BASES:
                return f"{base}-USD"
            break
    return None


def _resolve_china_exchange_by_code(code: str) -> str | None:
    """Return the exchange suffix for a China A-Share numeric code.

    Returns None if the code does not match any known A-Share pattern.
    """
    if not code.isdigit():
        return None
    if len(code) != 6:
        return None
    if code.startswith(_CHINA_SH_PREFIXES):
        return f"{code}.SS"
    if code.startswith(_CHINA_SZ_PREFIXES):
        return f"{code}.SZ"
    if code.startswith(_CHINA_BJ_PREFIXES):
        return f"{code}.BJ"
    return None


def is_china_stock(symbol: str) -> bool:
    """True when ``symbol`` is a China A-Share (has .SS/.SZ/.BJ suffix or
    matches a known 6-digit A-Share code pattern)."""
    if not symbol:
        return False
    s = symbol.strip().upper()
    if s.endswith(_CHINA_EXCHANGE_SUFFIXES):
        return True
    # Check if it's a 6-digit numeric code that matches A-Share patterns
    if len(s) == 6 and s.isdigit():
        return _resolve_china_exchange_by_code(s) is not None
    return False


def normalize_symbol(raw: str) -> str:
    """Map a user/broker symbol to its canonical vendor symbol.

    Resolution order (first match wins):
      1. China A-Share rule: 6-digit numeric code -> ``CODE.SS`` or ``CODE.SZ``.
      2. Explicit alias table (metals, energy, index CFDs).
      3. Crypto rule: a known crypto base quoted in USD/USDT/USDC (dashed or
         not) -> ``BASE-USD``.
      4. Forex rule: six letters that are two ISO currency codes -> ``PAIR=X``.
      5. Otherwise the upper-cased symbol is returned unchanged (plain
         equities, ETFs, Yahoo-native symbols like ``GC=F`` or ``^GSPC``).

    A trailing ``+`` (broker CFD marker, e.g. ``XAUUSD+``) is stripped before
    matching. The function is purely syntactic — it performs no network
    calls — so it is safe to apply on every request.
    """
    if not isinstance(raw, str) or not raw.strip():
        return raw

    s = raw.strip().upper()
    # Broker CFD/qualifier suffixes Yahoo never uses.
    s = s.rstrip("+")

    # 1. China A-Share: already has suffix or 6-digit numeric code
    if s.endswith(_CHINA_EXCHANGE_SUFFIXES):
        canonical = s
    elif len(s) == 6 and s.isdigit():
        china_symbol = _resolve_china_exchange_by_code(s)
        if china_symbol is not None:
            canonical = china_symbol
        else:
            canonical = s
    else:
        crypto = _normalize_crypto(s)
        if s in _ALIASES:
            canonical = _ALIASES[s]
        elif crypto is not None:
            canonical = crypto
        elif len(s) == 6 and s[:3] in _FOREX_CURRENCIES and s[3:] in _FOREX_CURRENCIES:
            canonical = f"{s}=X"
        else:
            canonical = s

    if canonical != raw.strip().upper():
        logger.info("Resolved symbol %r to canonical symbol %r", raw, canonical)
    return canonical


def is_yahoo_safe(symbol: str) -> bool:
    """True when ``symbol`` only contains characters Yahoo symbols use."""
    return bool(symbol) and _YAHOO_SAFE.fullmatch(symbol) is not None


def parse_china_symbol(symbol: str) -> tuple[str, str]:
    """Parse a China A-Share symbol into (code, exchange_suffix).

    Examples:
        "000001.SZ" -> ("000001", ".SZ")
        "600000.SS" -> ("600000", ".SS")
        "000001"    -> ("000001", ".SZ")  # auto-resolved

    Raises ValueError if the symbol cannot be parsed as a China A-Share.
    """
    canonical = normalize_symbol(symbol)
    if not is_china_stock(canonical):
        raise ValueError(f"'{symbol}' is not a recognized China A-Share symbol")

    if canonical.endswith(_CHINA_EXCHANGE_SUFFIXES):
        for suffix in _CHINA_EXCHANGE_SUFFIXES:
            if canonical.endswith(suffix):
                code = canonical[: -len(suffix)]
                return code, suffix
    # Should not reach here if is_china_stock passed
    raise ValueError(f"Cannot parse China A-Share symbol: '{symbol}'")
