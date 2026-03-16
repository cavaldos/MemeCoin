from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Button, Input, Rule, Static


async def mount_trade(container: ScrollableContainer) -> None:
    await container.mount(Static("NEW ORDER", classes="panel-title"))
    await container.mount(Input(placeholder="Token (e.g. SOL)", id="trade-token"))
    await container.mount(Input(placeholder="Amount (USD)", id="trade-amount"))
    await container.mount(
        Input(
            placeholder="Limit price (leave empty for market order)",
            id="trade-price",
        )
    )
    await container.mount(
        Horizontal(
            Button("\u25b2  BUY", variant="success", id="btn-buy"),
            Button("\u25bc  SELL", variant="error", id="btn-sell"),
            classes="btn-row",
        )
    )

    await container.mount(Rule())
    await container.mount(Static("OPEN ORDERS", classes="panel-title"))
    await container.mount(
        Static(
            "[bold #5c6370]TOKEN  SIDE   PRICE      AMOUNT     STATUS[/]",
            classes="table-header",
        )
    )
    await container.mount(
        Static(
            "[#abb2bf]SOL[/]    [#98c379]BUY[/]    $5.40      50.0       [#e5c07b]Pending[/]",
            classes="table-row",
        )
    )
    await container.mount(
        Static(
            "[#abb2bf]BTC[/]    [#98c379]BUY[/]    $41,800    0.012      [#e5c07b]Pending[/]",
            classes="table-row",
        )
    )
    await container.mount(
        Static(
            "[#abb2bf]PEPE[/]   [#e06c75]SELL[/]   $0.00110   500,000    [#d19a66]Partial[/]",
            classes="table-row",
        )
    )
