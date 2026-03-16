from textual.containers import ScrollableContainer
from textual.widgets import Rule, Static


async def mount_signals(container: ScrollableContainer) -> None:
    await container.mount(Static("ACTIVE SIGNALS", classes="panel-title"))
    await container.mount(
        Static(
            "[#5c6370]AI-generated trading signals based on technical analysis, "
            "sentiment, and on-chain data.[/]",
            classes="text-muted",
        )
    )
    await container.mount(Rule())

    signals = [
        ("SOL", "BUY", "85%", "Strong uptrend \u2014 RSI crossover + whale accumulation", True),
        ("PEPE", "BUY", "91%", "Social volume spike \u2014 potential breakout above resistance", True),
        ("BTC", "SELL", "72%", "Overbought on 4h \u2014 take profit near $43k resistance", False),
        ("DOGE", "BUY", "68%", "Cup & handle forming \u2014 moderate confidence entry", True),
        ("WIF", "SELL", "60%", "Declining volume \u2014 weak momentum after pump", False),
    ]

    for token, side, confidence, reason, is_buy in signals:
        color = "#98c379" if is_buy else "#e06c75"
        arrow = "\u25b2" if is_buy else "\u25bc"
        css_cls = "activity-item signal-buy" if is_buy else "activity-item signal-sell"
        await container.mount(
            Static(
                f"[bold {color}]{arrow} {side}[/]  [bold #abb2bf]{token}[/]  "
                f"\u2502  Confidence: [bold #e5c07b]{confidence}[/]  "
                f"\u2502  [#5c6370]{reason}[/]",
                classes=css_cls,
            )
        )
