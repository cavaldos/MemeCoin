from __future__ import annotations

from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Button, Rule, Static

from core.trending_config import ensure_config_file, get_config_path

from .coin_metrics import format_compact_currency


SAVE_SETTINGS_BUTTON_ID = "settings-save"
RESET_SETTINGS_BUTTON_ID = "settings-reset"


def _as_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return default
    return default


def _currency_label(value: object) -> str:
    if isinstance(value, (int, float, str)) or value is None:
        return format_compact_currency(value)
    return format_compact_currency(None)


def _describe_thresholds(filter_name: str, filter_config: dict[str, object]) -> str:
    parts: list[str] = []

    max_age_minutes = filter_config.get("max_age_minutes")
    if max_age_minutes is not None:
        hours, minutes = divmod(_as_int(max_age_minutes), 60)
        if hours and minutes:
            parts.append(f"Age <= {hours}h {minutes}m")
        elif hours:
            parts.append(f"Age <= {hours}h")
        else:
            parts.append(f"Age <= {minutes}m")

    min_volume = filter_config.get("min_volume")
    if min_volume is not None:
        parts.append(f"Volume >= ${_currency_label(min_volume)}")

    min_market_cap = filter_config.get("min_market_cap")
    if min_market_cap is not None:
        parts.append(f"Market cap >= ${_currency_label(min_market_cap)}")

    baseline_market_cap = filter_config.get("baseline_market_cap")
    if filter_name == "main_trading" and baseline_market_cap is not None:
        parts.append(f"Baseline floor >= ${_currency_label(baseline_market_cap)}")

    if not parts:
        parts.append("No thresholds configured")

    return "\n".join(f"[#5c6370]-[/] [#abb2bf]{part}[/]" for part in parts)


def _render_filter_card(filter_name: str, filter_config: dict[str, object], result_count: int) -> str:
    label = str(filter_config.get("label") or filter_name.replace("_", " ").title())
    description = str(filter_config.get("description") or "")
    thresholds = _describe_thresholds(filter_name, filter_config)
    return (
        f"[bold #61afef]{label}[/]\n"
        f"[#5c6370]{description}[/]\n"
        f"{thresholds}\n"
        f"[#5c6370]Matches:[/] [bold #98c379]{result_count}[/]"
    )


async def mount_settings(container: ScrollableContainer) -> None:
    config = ensure_config_file()
    sources = config.get("sources", {}) if isinstance(config.get("sources"), dict) else {}
    filters = config.get("filters", {}) if isinstance(config.get("filters"), dict) else {}
    history = config.get("history", {}) if isinstance(config.get("history"), dict) else {}
    results = config.get("results", {}) if isinstance(config.get("results"), dict) else {}
    source_counts = results.get("source_counts", {}) if isinstance(results.get("source_counts"), dict) else {}

    dex_settings_obj = sources.get("dexscreener", {})
    dex_settings = dex_settings_obj if isinstance(dex_settings_obj, dict) else {}
    gmgn_settings_obj = sources.get("gmgn", {})
    gmgn_settings = gmgn_settings_obj if isinstance(gmgn_settings_obj, dict) else {}
    history_entries = history.get("entries", []) if isinstance(history.get("entries"), list) else []

    await container.mount(Static("TREND FILTER SETTINGS", classes="panel-title"))
    await container.mount(
        Static(
            f"[#5c6370]Config file:[/] [#abb2bf]{get_config_path()}[/]\n"
            f"[#5c6370]Updated:[/] [#abb2bf]{config.get('updated_at') or 'Not generated yet'}[/]\n"
            f"[#5c6370]DexScreener top:[/] [bold #61afef]{dex_settings.get('target_count', 100)}[/]\n"
            f"[#5c6370]GMGN top:[/] [bold #61afef]{gmgn_settings.get('limit', 100)}[/] [#5c6370]on chain[/] [bold #e5c07b]{str(gmgn_settings.get('chain', 'sol')).upper()}[/]\n"
            f"[#5c6370]History size:[/] [bold #abb2bf]{len(history_entries)}[/] [#5c6370]/[/] [bold #abb2bf]{history.get('max_entries', 200)}[/]",
            classes="panel",
        )
    )

    await container.mount(Rule())
    await container.mount(Static("CURRENT SNAPSHOT", classes="panel-title"))
    await container.mount(
        Static(
            f"[#5c6370]Generated at:[/] [#abb2bf]{results.get('generated_at') or 'Waiting for first refresh'}[/]\n"
            f"[#5c6370]DexScreener rows:[/] [bold #abb2bf]{source_counts.get('dexscreener', 0)}[/]\n"
            f"[#5c6370]GMGN rows:[/] [bold #abb2bf]{source_counts.get('gmgn', 0)}[/]\n"
            f"[#5c6370]Merged candidates:[/] [bold #98c379]{source_counts.get('merged', 0)}[/]",
            classes="panel",
        )
    )

    await container.mount(Rule())
    await container.mount(Static("FILTER PRESETS", classes="panel-title"))

    for filter_name in ("main_trading", "strong_trending", "fast_trend"):
        filter_config_obj = filters.get(filter_name, {})
        filter_config = filter_config_obj if isinstance(filter_config_obj, dict) else {}
        result_rows_obj = results.get(filter_name, [])
        result_rows = result_rows_obj if isinstance(result_rows_obj, list) else []
        await container.mount(
            Static(
                _render_filter_card(filter_name, filter_config, len(result_rows)),
                classes="panel",
            )
        )

    await container.mount(
        Horizontal(
            Button("Save Settings", id=SAVE_SETTINGS_BUTTON_ID, variant="primary"),
            Button("Reset Defaults", id=RESET_SETTINGS_BUTTON_ID, variant="default"),
            classes="btn-row",
        )
    )
