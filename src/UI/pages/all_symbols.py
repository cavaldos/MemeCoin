from __future__ import annotations

from rich.text import Text
from textual.containers import ScrollableContainer, VerticalGroup
from textual.widgets import Button, Input, Rule, Static

from core.database import load_all_coins

from .coin_metrics import format_compact_currency, format_created_at

VOLUME_FILTER_ID = "all_symbols-min-volume"
RESULTS_ID = "all_symbols-results"

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
CHANGE_UP_STYLE = "bold #98c379"
CHANGE_DOWN_STYLE = "bold #e06c75"


def _parse_min_volume(raw: str) -> float:
    """Parse user input like '50000', '50k', '1.5m' into a float."""
    text = raw.strip().lower().replace(",", "").replace("$", "")
    if not text:
        return 0.0
    multiplier = 1.0
    if text.endswith("k"):
        multiplier = 1_000
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith("b"):
        multiplier = 1_000_000_000
        text = text[:-1]
    try:
        return float(text) * multiplier
    except ValueError:
        return 0.0


def _coin_volume(coin: dict[str, object]) -> float:
    val = coin.get("volume")
    if val is None:
        return 0.0
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _volume_change_label(row: dict[str, object]) -> tuple[str, str]:
    change = float(row.get("volume_change_percent_24h") or 0)
    if change >= 0:
        return (f"+{change:.2f}%", CHANGE_UP_STYLE)
    return (f"{change:.2f}%", CHANGE_DOWN_STYLE)


def _build_row_text(row: dict[str, object]) -> Text:
    change_text, change_style = _volume_change_label(row)
    details = Text()
    details.append("Token: ", style=TOKEN_STYLE)
    details.append(f"{row.get('symbol') or '?'} - {row.get('name') or '-'}", style=VALUE_STYLE)
    details.append(" | Chain: ", style=CHAIN_STYLE)
    details.append(str(row.get("chain") or "-").upper(), style=VALUE_STYLE)
    details.append(" | Volume: ", style=VOLUME_STYLE)
    details.append(f"${format_compact_currency(row.get('volume'))}", style=VALUE_STYLE)
    details.append(" | Vol 24h %: ", style=VOLUME_STYLE)
    details.append(change_text, style=change_style)
    details.append(" | MC: ", style=MCAP_STYLE)
    details.append(f"${format_compact_currency(row.get('market_cap'))}", style=VALUE_STYLE)
    details.append(" | Added: ", style=CHAIN_STYLE)
    details.append(format_created_at(row.get("added_at")), style=VALUE_STYLE)
    return details


def _filter_by_volume(coins: list[dict[str, object]], min_volume: float) -> list[dict[str, object]]:
    if min_volume <= 0:
        return coins
    return [c for c in coins if _coin_volume(c) >= min_volume]


async def refresh_all_symbols_results(container: VerticalGroup, raw_input: str = "") -> None:
    """Refresh only the results area."""
    min_volume = _parse_min_volume(raw_input)
    all_coins = load_all_coins()
    total_count = sum(len(coins) for coins in all_coins.values())

    async with container.batch():
        await container.remove_children()

        info_parts = [f"[#5c6370]Total symbols stored:[/] [bold #abb2bf]{total_count}[/]"]
        if min_volume > 0:
            info_parts.append(
                f"[#5c6370]  |  Filtering volume ≥[/] [bold #98c379]${format_compact_currency(min_volume)}[/]"
            )
        await container.mount(Static("".join(info_parts), classes="panel"))
        await container.mount(Rule())

        if total_count == 0:
            await container.mount(
                Static("[#e5c07b]No symbols in database yet.[/]", classes="panel")
            )
            return

        total_shown = 0
        for filter_key, coins in all_coins.items():
            filter_label = FILTER_LABELS.get(filter_key, filter_key)
            filtered = _filter_by_volume(coins, min_volume)

            if not coins:
                continue

            if min_volume > 0:
                await container.mount(
                    Static(
                        f"[bold #61afef]{filter_label}[/] ([bold #abb2bf]{len(filtered)}[/] / {len(coins)})",
                        classes="panel-subtitle",
                    )
                )
            else:
                await container.mount(
                    Static(f"[bold #61afef]{filter_label}[/] ({len(coins)})", classes="panel-subtitle")
                )

            if not filtered:
                await container.mount(
                    Static(f"[#5c6370]No symbols with volume ≥ ${format_compact_currency(min_volume)}[/]", classes="panel")
                )
                continue

            total_shown += len(filtered)
            for idx, coin in enumerate(filtered):
                url = str(coin.get("url") or "").strip()
                await container.mount(Static(_build_row_text(coin), classes="panel"))
                if url:
                    display_url = url[8:] if url.startswith("https://") else url[7:] if url.startswith("http://") else url
                    await container.mount(Static(display_url, classes="coin-url", markup=False))
                    await container.mount(
                        Button(
                            "Copy",
                            id=f"copy_symbol_{filter_key}_{idx}",
                            name=url,
                            variant="primary",
                            compact=True,
                            classes="copy-url-button",
                        )
                    )


async def mount_all_symbols(container: ScrollableContainer, raw_input: str = "") -> None:
    """Mount the full page (title + volume filter + results group)."""
    await container.mount(Static("ALL SYMBOLS", classes="panel-title"))
    await container.mount(
        Input(
            placeholder="Min volume (e.g. 50000, 50k, 1.5m) ...",
            id=VOLUME_FILTER_ID,
            value=raw_input,
        )
    )
    results = VerticalGroup(id=RESULTS_ID)
    await container.mount(results)
    await refresh_all_symbols_results(results, raw_input)
