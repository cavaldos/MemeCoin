import requests
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
DISCORD_MAIN_TREND = os.environ.get('DISCORD_MAIN_TREND')
DISCORD_FAST_TREND = os.environ.get('DISCORD_FAST_TREND')
DISCORD_STRONG_TREND = os.environ.get('DISCORD_STRONG_TREND')

_FILTER_WEBHOOK_MAP = {
    "main_trading": DISCORD_MAIN_TREND,
    "strong_trending": DISCORD_STRONG_TREND,
    "fast_trend": DISCORD_FAST_TREND,
}


def _coerce_float(value: object) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float, str)):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def _format_amount(value: object) -> str:
    amount = _coerce_float(value)
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.2f}K"
    return f"${amount:,.2f}"


def _format_percent(value: object) -> str:
    amount = _coerce_float(value)
    return f"{amount:+.2f}%"


def send_message(message: str, webhook_url: str | None = None) -> bool:
    """Send message to Discord webhook."""
    url = webhook_url or DISCORD_WEBHOOK_URL
    if not url:
        return False
    payload = {"content": message}
    try:
        requests.post(url, json=payload, timeout=5)
        return True
    except Exception:
        return False


def send_filtered_alert(filter_key: str, filter_label: str, row: dict[str, object], detected_at: str) -> bool:
    symbol = str(row.get("symbol") or "?")
    name = str(row.get("name") or "-")
    chain = str(row.get("chain") or "-").upper()
    source_sites = row.get("source_sites", [])
    if isinstance(source_sites, list) and source_sites:
        source_label = ", ".join(str(source).upper() for source in source_sites)
    else:
        sources = row.get("sources", [])
        if isinstance(sources, list) and sources:
            source_label = ", ".join(str(source).upper() for source in sources)
        else:
            source_label = str(row.get("source") or "-").upper()

    filter_tag_map = {
        "main_trading": "MAIN",
        "strong_trending": "STRONG",
        "fast_trend": "FAST",
    }
    filter_tag = filter_tag_map.get(filter_key, filter_key.upper())

    webhook_url = _FILTER_WEBHOOK_MAP.get(filter_key)

    age_minutes = row.get("age_minutes")
    age_label = f"{age_minutes}m" if isinstance(age_minutes, int) else "-"
    url = str(row.get("url") or row.get("coin_url") or "-")

    message = "\n".join(
        [
            "**NEW FILTER HIT**",
            f"Filter: `{filter_tag}` ({filter_label})",
            f"Token: `{symbol}` - {name}",
            f"Chain: `{chain}`",
            f"Source: `{source_label}`",
            f"Volume: `{_format_amount(row.get('volume'))}`",
            f"Vol 24h Change: `{_format_percent(row.get('volume_change_percent_24h'))}`",
            f"Market Cap: `{_format_amount(row.get('market_cap'))}`",
            f"Age: `{age_label}`",
            f"Detected: `{detected_at}`",
            f"URL: <{url}>",
        ]
    )
    return send_message(message, webhook_url)
