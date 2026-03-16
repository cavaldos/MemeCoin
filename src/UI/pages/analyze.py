from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Button, Input, Rule, Static


async def mount_analyze(container: ScrollableContainer) -> None:
    await container.mount(Static("TOKEN ANALYSIS", classes="panel-title"))
    await container.mount(
        Static(
            "[#5c6370]Enter a token symbol below to run technical and sentiment analysis.[/]",
            classes="text-muted",
        )
    )
    await container.mount(
        Input(
            placeholder="Token symbol (e.g. SOL, BTC, PEPE)",
            id="analyze-input",
        )
    )
    await container.mount(
        Horizontal(
            Button("Analyze", variant="primary"),
            Button("Compare", variant="default"),
            classes="btn-row",
        )
    )

    await container.mount(Rule())
    await container.mount(Static("MARKET STATS", classes="panel-title"))
    await container.mount(
        Horizontal(
            Static("[#5c6370]24h VOLUME[/]\n[bold #abb2bf]$2.5B[/]", classes="stat-card"),
            Static("[#5c6370]FEAR & GREED[/]\n[bold #e5c07b]65 \u2014 Greed[/]", classes="stat-card"),
            Static("[#5c6370]BTC DOMINANCE[/]\n[bold #61afef]48.2%[/]", classes="stat-card"),
            classes="stat-row",
        )
    )

    await container.mount(Rule())
    await container.mount(Static("TOP MOVERS (24h)", classes="panel-title"))
    await container.mount(
        Static(
            "[#98c379]\u25b2[/] [bold #abb2bf]BONK[/]   [#98c379]+42.1%[/]    [#5c6370]$0.0000135[/]\n"
            "[#98c379]\u25b2[/] [bold #abb2bf]WIF[/]    [#98c379]+28.7%[/]    [#5c6370]$0.482[/]\n"
            "[#e06c75]\u25bc[/] [bold #abb2bf]SHIB[/]   [#e06c75]-5.2%[/]     [#5c6370]$0.0000089[/]\n"
            "[#98c379]\u25b2[/] [bold #abb2bf]FLOKI[/]  [#98c379]+15.3%[/]    [#5c6370]$0.000167[/]",
            classes="panel",
        )
    )
