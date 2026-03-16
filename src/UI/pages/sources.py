from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Button, Static

from .data_loader import load_data_file


async def mount_sources(container: ScrollableContainer) -> None:
    await container.mount(Static("DATA SOURCES", classes="panel-title"))
    await container.mount(
        Static(
            "[#5c6370]Available data sources for tracking cryptocurrency pairs and tokens.[/]",
            classes="text-muted",
        )
    )

    sources = [
        ("dexscreener", "DexScreener", "\u26fd", "Real-time DEX pair tracking", "#f39c12"),
        ("gmgn", "GMGN.ai", "\U0001f4ca", "Smart money & Solana signals", "#9b59b6"),
        ("pump_fun", "Pump.fun", "\U0001f4a5", "Token launcher & trading", "#1abc9c"),
        ("trade_padre", "Trade Padre", "\U0001f3af", "Trading signals & analytics", "#3498db"),
        ("four_meme", "4Meme", "\U0001f3b0", "Meme coin aggregator", "#e74c3c"),
    ]

    for source_id, name, icon, desc, color in sources:
        data_file = f"{source_id}_100_coins.json"
        data = load_data_file(data_file)
        count = len(data)
        
        await container.mount(
            Static(
                f"[bold {color}]{icon} {name}[/]\n"
                f"[#5c6370]{desc}[/]\n"
                f"[#abb2bf]{count} tokens loaded[/]",
                classes="source-card",
            )
        )

    await container.mount(Static("\nRECENT DATA", classes="panel-title"))

    dexscreener_data = load_data_file("dexscreener_100_coins.json")
    gmgn_data = load_data_file("gmgn_100_coins.json")

    if dexscreener_data:
        await container.mount(
            Static(
                f"[bold #f39c12]\u26fd DexScreener[/] - [bold #abb2bf]{len(dexscreener_data)}[/] pairs loaded",
                classes="data-item",
            )
        )

    if gmgn_data:
        await container.mount(
            Static(
                f"[bold #9b59b6]\U0001f4ca GMGN.ai[/] - [bold #abb2bf]{len(gmgn_data)}[/] tokens loaded",
                classes="data-item",
            )
        )

    await container.mount(
        Horizontal(
            Button("Refresh DexScreener", variant="primary", id="btn_refresh_dexscreener"),
            Button("Refresh GMGN", variant="primary", id="btn_refresh_gmgn"),
            classes="btn-row",
        )
    )
