from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Button, Rule, Static


async def mount_settings(container: ScrollableContainer) -> None:
    await container.mount(Static("EXCHANGE CONFIGURATION", classes="panel-title"))
    await container.mount(
        Static(
            "[#5c6370]API Key:[/]      [#abb2bf]****************************3f7a[/]\n"
            "[#5c6370]Secret Key:[/]   [#abb2bf]****************************9b2e[/]\n"
            "[#5c6370]Exchange:[/]     [bold #61afef]Binance[/]\n"
            "[#5c6370]Testnet:[/]      [#98c379][\u2713] Enabled[/]",
            classes="panel",
        )
    )

    await container.mount(Rule())
    await container.mount(Static("TRADING SETTINGS", classes="panel-title"))
    await container.mount(
        Static(
            "[#5c6370]Auto-Trade:[/]      [#e06c75][ ] Disabled[/]\n"
            "[#5c6370]Max Position:[/]    [#abb2bf]$1,000.00[/]\n"
            "[#5c6370]Stop Loss:[/]       [#e5c07b]5%[/]\n"
            "[#5c6370]Take Profit:[/]     [#98c379]15%[/]\n"
            "[#5c6370]Slippage Limit:[/]  [#d19a66]1.5%[/]",
            classes="panel",
        )
    )

    await container.mount(Rule())
    await container.mount(Static("NOTIFICATIONS", classes="panel-title"))
    await container.mount(
        Static(
            "[#5c6370]Telegram:[/]   [#e06c75][ ] Disabled[/]\n"
            "[#5c6370]Discord:[/]    [#e06c75][ ] Disabled[/]\n"
            "[#5c6370]Email:[/]      [#e06c75][ ] Disabled[/]",
            classes="panel",
        )
    )

    await container.mount(
        Horizontal(
            Button("Save Settings", variant="primary"),
            Button("Reset Defaults", variant="default"),
            classes="btn-row",
        )
    )
