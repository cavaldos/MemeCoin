from rich.markup import escape
from rich.text import Text
from textual.containers import ScrollableContainer, VerticalGroup
from textual.widgets import Button, Collapsible, Input, Rule, Static

from core.trending_config import annotate_source_rows_with_volume_change

from .coin_metrics import format_age, format_compact_currency, format_created_at, format_full_currency, matches_query
from .data_loader import load_data_file


SEARCH_INPUT_ID = "dexscreener-search"
RESULTS_ID = "dexscreener-results"
POLL_STATUS_ID = "dexscreener-poll-status"

PAIR_STYLE = "bold #56b6c2"
NAME_STYLE = "bold #7fbbb3"
CHAIN_STYLE = "bold #e5c07b"
DEX_STYLE = "bold #c678dd"
PRICE_STYLE = "bold #61afef"
VOLUME_STYLE = "bold #98c379"
MCAP_STYLE = "bold #d19a66"
AGE_STYLE = "bold #e06c75"
VALUE_STYLE = "#abb2bf"


def _as_float(value: float | int | str | None) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _format_price(value: float) -> str:
    if value >= 1:
        return f"${value:.4f}"
    if value >= 0.001:
        return f"${value:.6f}"
    return f"${value:.8f}"


def _format_created_at(value: object) -> str:
    return format_created_at(value)


def _format_volume_change(value: object) -> str:
    change = _as_float(value)
    return f"{change:+.1f}%"


def _volume_change_style(value: object) -> str:
    change = _as_float(value)
    if change > 0:
        return VOLUME_STYLE
    if change < 0:
        return AGE_STYLE
    return VALUE_STYLE


def _display_url(value: object) -> str:
    url = str(value or "").strip()
    if not url:
        return "-"
    if url.startswith("https://"):
        return url[8:]
    if url.startswith("http://"):
        return url[7:]
    return url


def _append_cell(buffer: Text, value: object, width: int, style: str, *, align: str = "left") -> None:
    content = ("" if value is None else str(value))[:width]
    padded = content.rjust(width) if align == "right" else content.ljust(width)
    buffer.append(padded, style=style)


def _build_header() -> Text:
    header = Text()
    _append_cell(header, "PAIR", 18, PAIR_STYLE)
    header.append("  ")
    _append_cell(header, "NAME", 18, NAME_STYLE)
    header.append("  ")
    _append_cell(header, "CHAIN", 6, CHAIN_STYLE)
    header.append("  ")
    _append_cell(header, "DEX", 10, DEX_STYLE)
    header.append("  ")
    _append_cell(header, "PRICE USD", 11, PRICE_STYLE, align="right")
    header.append("  ")
    _append_cell(header, "VOL 24H", 8, VOLUME_STYLE, align="right")
    header.append("  ")
    _append_cell(header, "VOL 24H %", 10, VOLUME_STYLE, align="right")
    header.append("  ")
    _append_cell(header, "MCAP", 8, MCAP_STYLE, align="right")
    header.append("  ")
    _append_cell(header, "AGE", 8, AGE_STYLE)
    return header


def _markup_cell(value: object, width: int, style: str, *, align: str = "left") -> str:
    content = ("" if value is None else str(value))[:width]
    padded = content.rjust(width) if align == "right" else content.ljust(width)
    return f"[{style}]{escape(padded)}[/]"


def _build_title(row: dict) -> str:
    base = str(row.get("symbol", "?") or "?")
    quote = str(row.get("quote_token_symbol", "?") or "?")
    name = str(row.get("name", "-") or "-")
    return "  ".join(
        [
            _markup_cell(f"{base}/{quote}", 18, PAIR_STYLE),
            _markup_cell(name, 18, NAME_STYLE),
            _markup_cell(str(row.get("chain", "-")).upper(), 6, CHAIN_STYLE),
            _markup_cell(row.get("dex_id", "-") or "-", 10, DEX_STYLE),
            _markup_cell(_format_price(_as_float(row.get("price_usd", 0))), 11, PRICE_STYLE, align="right"),
            _markup_cell(format_compact_currency(row.get("volume_24h")), 8, VOLUME_STYLE, align="right"),
            _markup_cell(_format_volume_change(row.get("volume_change_percent_24h")), 10, _volume_change_style(row.get("volume_change_percent_24h")), align="right"),
            _markup_cell(format_compact_currency(row.get("market_cap") or row.get("fdv")), 8, MCAP_STYLE, align="right"),
            _markup_cell(format_age(row.get("created_at") or row.get("pair_created_at")), 8, AGE_STYLE),
        ]
    )


def _build_details(row: dict) -> Text:
    created_value = row.get("created_at") or row.get("pair_created_at")
    age = format_age(created_value)
    created_at = _format_created_at(created_value)
    volume = format_full_currency(row.get("volume_24h"))
    market_cap = format_full_currency(row.get("market_cap") or row.get("fdv"))
    name = str(row.get("name", "-") or "-")
    trend_signals = ", ".join(row.get("trend_signals", [])) if isinstance(row.get("trend_signals"), list) else "-"
    signal_score = str(int(_as_float(row.get("signal_score", 0)))) if _as_float(row.get("signal_score", 0)) else "-"
    volume_change = _format_volume_change(row.get("volume_change_percent_24h"))
    details = Text()
    details.append("Name: ", style=NAME_STYLE)
    details.append(name, style=VALUE_STYLE)
    details.append(" | ")
    details.append("Age: ", style=AGE_STYLE)
    details.append(age, style=VALUE_STYLE)
    details.append(" | Created: ", style=AGE_STYLE)
    details.append(created_at, style=VALUE_STYLE)
    details.append(" | Vol 24h: ", style=VOLUME_STYLE)
    details.append(volume, style=VALUE_STYLE)
    details.append(" | Vol 24h %: ", style=VOLUME_STYLE)
    details.append(volume_change, style=_volume_change_style(row.get("volume_change_percent_24h")))
    details.append(" | Market cap: ", style=MCAP_STYLE)
    details.append(market_cap, style=VALUE_STYLE)
    details.append(" | Trend score: ", style=CHAIN_STYLE)
    details.append(signal_score, style=VALUE_STYLE)
    details.append(" | Signals: ", style=DEX_STYLE)
    details.append(trend_signals, style=VALUE_STYLE)
    return details


def _filter_rows(rows: list[dict], search_query: str) -> list[dict]:
    return [
        row
        for row in rows
        if matches_query(
            search_query,
            row.get("symbol"),
            row.get("quote_token_symbol"),
            row.get("name"),
            row.get("address"),
            row.get("chain"),
            row.get("dex_id"),
            row.get("pair_address"),
            row.get("coin_url") or row.get("url"),
        )
    ]


def _load_rows(search_query: str = "") -> tuple[list[dict], int]:
    data = annotate_source_rows_with_volume_change("dexscreener", load_data_file("dexscreener_100_coins.json"))
    rows = sorted(
        data,
        key=lambda row: (
            _as_float(row.get("signal_score")),
            _as_float(row.get("volume_24h")),
            _as_float(row.get("market_cap") or row.get("fdv")),
            str(row.get("created_at") or row.get("pair_created_at") or ""),
        ),
        reverse=True,
    )
    return _filter_rows(rows, search_query), len(rows)


def _build_status_line(count: int, total_rows: int, search_query: str) -> Text:
    status = Text(style="#5c6370")
    status.append("Showing ")
    status.append(str(count), style="bold #abb2bf")
    status.append(" of ")
    status.append(str(total_rows), style="bold #abb2bf")
    if search_query.strip():
        status.append(" pairs for ")
        status.append(search_query, style=PAIR_STYLE)
        status.append(".")
    else:
        status.append(" top trending pairs from DexScreener.")
    return status


async def refresh_dexscreener_results(container: VerticalGroup, search_query: str = "") -> None:
    rows, total_rows = _load_rows(search_query)

    async with container.batch():
        await container.remove_children()
        await container.mount(Static(_build_status_line(len(rows), total_rows, search_query), classes="text-muted"))
        await container.mount(Rule())

        if total_rows == 0:
            await container.mount(
                Static(
                    "[#e5c07b]No DexScreener data found. Run the fetcher first to load orders.[/]",
                    classes="panel",
                )
            )
            return

        if not rows:
            await container.mount(
                Static(
                    "[#e5c07b]No pairs match your search yet. Try symbol, chain, dex, address, or URL.[/]",
                    classes="panel",
                )
            )
            return

        await container.mount(Static(_build_header(), classes="table-header"))

        for index, row in enumerate(rows[:40]):
            url = str(row.get("coin_url") or row.get("url") or "").strip()
            display_url = _display_url(url)
            await container.mount(
                Collapsible(
                    VerticalGroup(
                        Static(_build_details(row), classes="panel"),
                        Static(display_url, classes="coin-url", markup=False),
                        Button(
                            "Copy",
                            id=f"copy_dexscreener_{index}",
                            name=url,
                            variant="primary",
                            compact=True,
                            classes="copy-url-button",
                            disabled=not bool(url),
                        ),
                        classes="coin-details",
                    ),
                    title=_build_title(row),
                    classes="coin-toggle",
                )
            )


async def mount_dexscreener(container: ScrollableContainer, search_query: str = "") -> None:
    data = load_data_file("dexscreener_100_coins.json")

    await container.mount(Static("DEXSCREENER TRENDING PAIRS", classes="panel-title"))
    await container.mount(
        Static(
            f"[#5c6370]Loaded [bold #abb2bf]{len(data)}[/] trending pairs from DexScreener. Search by symbol, name, chain, dex, address, or URL.[/]",
            classes="text-muted",
        )
    )
    await container.mount(Static("[#5c6370]Preparing auto refresh...[/]", id=POLL_STATUS_ID, classes="text-muted"))
    await container.mount(
        Input(
            value=search_query,
            placeholder="Search pair, symbol, chain, dex, address...",
            id=SEARCH_INPUT_ID,
        )
    )
    await container.mount(Rule())
    results = VerticalGroup(id=RESULTS_ID)
    await container.mount(results)
    await refresh_dexscreener_results(results, search_query)
