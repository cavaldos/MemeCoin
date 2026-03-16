from dataclasses import dataclass


@dataclass(frozen=True)
class NavItem:
    id: str
    label: str
    icon: str = ""


NAV_ITEMS = [
    NavItem("dexscreener", "DexScreener", "\u26fd"),
    NavItem("gmgn", "GMGN.ai", "\U0001f4ca"),
    NavItem("history", "History", "\U0001f5c2"),
    NavItem("settings", "Settings", "\u2699"),
]

TAB_TITLES = {
    "dexscreener": ("\u26fd  DexScreener Orders", "Sources \u203a DexScreener"),
    "gmgn": ("\U0001f4ca  GMGN Orders", "Sources \u203a GMGN.ai"),
    "history": ("\U0001f5c2  Filter History", "Config \u203a History"),
    "settings": ("\u2699  Settings", "Config \u203a Preferences"),
}

HELP_TAB_ID = "__help__"
