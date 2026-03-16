from __future__ import annotations

from rich.text import Text
from textual.containers import ScrollableContainer, VerticalGroup
from textual.widget import Widget
from textual.widgets import Button, Collapsible, Rule, Static

from core.trending_config import ensure_config_file, get_config_path

from .coin_metrics import format_compact_currency, format_created_at


HISTORY_ENTRY_LIMIT = 50

FILTER_LABELS = {
    "main_trading": "Main Trading",
    "strong_trending": "Strong Trending",
    "fast_trend": "Fast Trend",
}

TOKEN_STYLE = "bold #56b6c2"
CHAIN_STYLE = "bold #e5c07b"
VOLUME_STYLE = "bold #98c379"
MCAP_STYLE = "bold #d19a66"
VALUE_STYLE = "#abb2bf"
STATUS_SENT_STYLE = "bold #98c379"
STATUS_PENDING_STYLE = "bold #e5c07b"


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_entries(value: object) -> list[dict[str, object]]:
    return [entry for entry in value if isinstance(entry, dict)] if isinstance(value, list) else []


def _currency_text(value: object) -> str:
    if isinstance(value, (int, float, str)) or value is None:
        return format_compact_currency(value)
    return format_compact_currency(None)


def _display_url(value: object) -> str:
    url = str(value or "").strip()
    if not url:
        return "-"
    if url.startswith("https://"):
        return url[8:]
    if url.startswith("http://"):
        return url[7:]
    return url


def _source_label(row: dict[str, object]) -> str:
    source_sites = row.get("source_sites")
    if isinstance(source_sites, list) and source_sites:
        return ", ".join(str(source).upper() for source in source_sites if str(source).strip())
    return "-"


def _status_label(row: dict[str, object]) -> tuple[str, str]:
    sent = bool(row.get("sent_to_discord", False))
    return ("SENT", STATUS_SENT_STYLE) if sent else ("PENDING", STATUS_PENDING_STYLE)


def _build_entry_text(row: dict[str, object]) -> Text:
    status_text, status_style = _status_label(row)
    details = Text()
    details.append("Token: ", style=TOKEN_STYLE)
    details.append(f"{row.get('symbol') or '?'} - {row.get('name') or '-'}", style=VALUE_STYLE)
    details.append(" | Chain: ", style=CHAIN_STYLE)
    details.append(str(row.get("chain") or "-").upper(), style=VALUE_STYLE)
    details.append(" | Website: ", style=CHAIN_STYLE)
    details.append(_source_label(row), style=VALUE_STYLE)
    details.append(" | Discord: ", style=CHAIN_STYLE)
    details.append(status_text, style=status_style)
    details.append("\nVolume: ", style=VOLUME_STYLE)
    details.append(f"${_currency_text(row.get('volume'))}", style=VALUE_STYLE)
    details.append(" | MC: ", style=MCAP_STYLE)
    details.append(f"${_currency_text(row.get('market_cap'))}", style=VALUE_STYLE)
    details.append(" | Created: ", style=CHAIN_STYLE)
    details.append(format_created_at(row.get("created_at")), style=VALUE_STYLE)
    return details


def _build_filter_group(filter_name: str, entries: list[dict[str, object]]) -> Collapsible:
    filter_label = FILTER_LABELS.get(filter_name, filter_name)
    widgets: list[Widget] = []

    if not entries:
        widgets.append(
            Static(
                f"[#5c6370]No coins stored for {filter_label} yet.[/]",
                classes="panel",
            )
        )
    else:
        display_entries = entries[:HISTORY_ENTRY_LIMIT]
        if len(entries) > HISTORY_ENTRY_LIMIT:
            widgets.append(
                Static(
                    f"[#5c6370]Showing [bold #abb2bf]{len(display_entries)}[/] of [bold #abb2bf]{len(entries)}[/] stored coins.[/]",
                    classes="text-muted",
                )
            )

        for index, entry in enumerate(display_entries):
            url = str(entry.get("url") or "").strip()
            widgets.extend(
                [
                    Static(_build_entry_text(entry), classes="panel"),
                    Static(_display_url(url), classes="coin-url", markup=False),
                    Button(
                        "Copy",
                        id=f"copy_history_{filter_name}_{index}",
                        name=url,
                        variant="primary",
                        compact=True,
                        classes="copy-url-button",
                        disabled=not bool(url),
                    ),
                ]
            )

    return Collapsible(
        VerticalGroup(*widgets, classes="coin-details"),
        title=f"{filter_label} ({len(entries)})",
        classes="coin-toggle",
    )


async def mount_history(container: ScrollableContainer) -> None:
    config = ensure_config_file()
    history = _as_dict(config.get("history"))
    entries = _as_entries(history.get("entries"))
    max_entries = history.get("max_entries", 200)

    grouped_entries = {
        filter_name: [entry for entry in entries if str(entry.get("filter_key") or "") == filter_name]
        for filter_name in ("main_trading", "strong_trending", "fast_trend")
    }

    await container.mount(Static("FILTER HISTORY", classes="panel-title"))
    await container.mount(
        Static(
            f"[#5c6370]Config file:[/] [#abb2bf]{get_config_path()}[/]\n"
            f"[#5c6370]Stored coins:[/] [bold #abb2bf]{len(entries)}[/] [#5c6370]/[/] [bold #abb2bf]{max_entries}[/]\n"
            f"[#5c6370]History only stores coin info, source website, filter type, and whether Discord already received it.[/]",
            classes="panel",
        )
    )
    await container.mount(Rule())

    if not entries:
        await container.mount(
            Static(
                "[#e5c07b]No history yet. Wait for the filter to find new coins.[/]",
                classes="panel",
            )
        )
        return

    for filter_name in ("main_trading", "strong_trending", "fast_trend"):
        await container.mount(_build_filter_group(filter_name, grouped_entries[filter_name]))
