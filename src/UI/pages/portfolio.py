from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Rule, Static


async def mount_portfolio(container: ScrollableContainer) -> None:
    await container.mount(Static("PORTFOLIO HOLDINGS", classes="panel-title"))
    await container.mount(
        Horizontal(
            Static("[#5c6370]TOTAL VALUE[/]\n[bold #abb2bf]$12,600.00[/]", classes="stat-card"),
            Static("[#5c6370]24h CHANGE[/]\n[bold #98c379]+$187 +1.5%[/]", classes="stat-card"),
            Static("[#5c6370]ASSETS[/]\n[bold #61afef]4[/]", classes="stat-card"),
            classes="stat-row",
        )
    )

    await container.mount(Rule())
    await container.mount(
        Static(
            "[bold #5c6370]ASSET      QTY            VALUE        ALLOC    24h[/]",
            classes="table-header",
        )
    )
    rows = [
        ("USDT", "--", "$9,525.00", "75.6%", "[#5c6370]0.0%[/]"),
        ("BTC", "0.05", "$2,100.00", "16.7%", "[#98c379]+2.3%[/]"),
        ("SOL", "150.00", "$825.00", "6.5%", "[#e06c75]-0.4%[/]"),
        ("PEPE", "1,000,000", "$150.00", "1.2%", "[#98c379]+8.1%[/]"),
    ]
    for asset, qty, value, alloc, change in rows:
        await container.mount(
            Static(
                f"[bold #abb2bf]{asset:<10}[/] [#abb2bf]{qty:<14} {value:<12} {alloc:<8}[/] {change}",
                classes="table-row",
            )
        )
