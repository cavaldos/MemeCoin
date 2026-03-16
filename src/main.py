from UI import MemeCoinTUI
from core import MarketDataPoller


if __name__ == "__main__":
    poller = MarketDataPoller(interval_seconds=10)
    poller.start()

    try:
        app = MemeCoinTUI(poller=poller)
        app.run()
    finally:
        poller.stop()
