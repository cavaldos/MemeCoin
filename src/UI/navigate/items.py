from dataclasses import dataclass


@dataclass(frozen=True)
class NavItem:
    id: str
    label: str
    icon: str = ""


NAV_ITEMS = [
    NavItem("dashboard", "Dashboard", "\u2302"),
    NavItem("analyze", "Analyze", "\u2261"),
    NavItem("trade", "Trade", "\u21c4"),
    NavItem("signals", "Signals", "\u2691"),
    NavItem("portfolio", "Portfolio", "\u25ce"),
    NavItem("settings", "Settings", "\u2699"),
]

TAB_TITLES = {
    "dashboard": ("\u2302  Dashboard", "Overview \u203a Home"),
    "analyze": ("\u2261  Market Analysis", "Tools \u203a Analysis"),
    "trade": ("\u21c4  Trading", "Execute \u203a New Order"),
    "signals": ("\u2691  Trading Signals", "AI \u203a Signals"),
    "portfolio": ("\u25ce  Portfolio", "Holdings \u203a Assets"),
    "settings": ("\u2699  Settings", "Config \u203a Preferences"),
}

HELP_TAB_ID = "__help__"
