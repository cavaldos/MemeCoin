from .analyze import mount_analyze
from .dashboard import mount_dashboard
from .help import mount_help
from .portfolio import mount_portfolio
from .settings import mount_settings
from .signals import mount_signals
from .trade import mount_trade

__all__ = [
    "mount_dashboard",
    "mount_analyze",
    "mount_trade",
    "mount_signals",
    "mount_portfolio",
    "mount_settings",
    "mount_help",
]
