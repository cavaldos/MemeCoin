from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Rule, Static


async def mount_dashboard(container: ScrollableContainer) -> None:
    await container.mount(
        Horizontal(
            Static("[#5c6370]PORTFOLIO[/]\n[bold #abb2bf]$12,500.00[/]", classes="stat-card"),
            Static("[#5c6370]TODAY P&L[/]\n[bold #98c379]+$234.50 +1.9%[/]", classes="stat-card"),
            classes="stat-row",
        )
    )

    await container.mount(
        Horizontal(
            Static("[#5c6370]TRADES[/]\n[bold #e5c07b]3 Active[/]", classes="stat-card"),
            Static("[#5c6370]SIGNALS[/]\n[bold #61afef]5 Open[/]", classes="stat-card"),
            classes="stat-row",
        )
    )

    await container.mount(Static("RECENT ACTIVITY", classes="panel-title"))
    await container.mount(
        Static(
            "[bold #98c379]\u25b2 BUY[/]  [#abb2bf]SOL  @ $5.50    $275.00    [#5c6370]2 min ago[/]",
            classes="activity-item signal-buy",
        )
    )
    await container.mount(
        Static(
            "[bold #e06c75]\u25bc SELL[/] [#abb2bf]PEPE @ $0.00100  $100.00    [#5c6370]15 min ago[/]",
            classes="activity-item signal-sell",
        )
    )
    await container.mount(
        Static(
            "[bold #98c379]\u25b2 BUY[/]  [#abb2bf]BTC  @ $42,000   $500.00    [#5c6370]1 hour ago[/]",
            classes="activity-item signal-buy",
        )
    )

    await container.mount(Rule())
    await container.mount(Static("MARKET OVERVIEW", classes="panel-title"))
    await container.mount(
        Static(
            "[#abb2bf]BTC[/]  $42,150  [#98c379]+2.3%[/]   \u2502  "
            "[#abb2bf]ETH[/]  $2,280   [#98c379]+1.8%[/]   \u2502  "
            "[#abb2bf]SOL[/]  $5.52    [#e06c75]-0.4%[/]",
            classes="panel",
        )
    )
