from UI import MemeCoinTUI
from core import MarketDataPoller
from core.discord import run_bot_async


if __name__ == "__main__":
    poller = MarketDataPoller(interval_seconds=10)
    poller.start()

    # Start Discord bot in background thread (non-blocking)
    run_bot_async()

    try:
        app = MemeCoinTUI(poller=poller)
        app.run()
    finally:
        poller.stop()
