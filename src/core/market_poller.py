from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta

from getdata.dexscreener.main import fetch_enriched_pairs, save_enriched_pairs
from getdata.gmgn.main import fetch_enriched_tokens, save_enriched_tokens

from .trending_config import ensure_config_file, refresh_config_results

logger = logging.getLogger(__name__)


class MarketDataPoller:
    def __init__(
        self,
        *,
        interval_seconds: int = 10,
        dexscreener_target_count: int = 100,
        gmgn_chain: str = "sol",
        gmgn_limit: int = 100,
        run_immediately: bool = True,
    ) -> None:
        self.interval_seconds = interval_seconds
        self.dexscreener_target_count = dexscreener_target_count
        self.gmgn_chain = gmgn_chain
        self.gmgn_limit = gmgn_limit
        self.run_immediately = run_immediately

        ensure_config_file()
        self.reload_settings()

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._cycle_in_progress = False

        self.last_started_at: datetime | None = None
        self.last_completed_at: datetime | None = None
        self.next_run_at: datetime | None = None
        self.last_success_at: dict[str, datetime | None] = {
            "dexscreener": None,
            "gmgn": None,
        }
        self.last_error: dict[str, str | None] = {
            "dexscreener": None,
            "gmgn": None,
        }

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        with self._lock:
            if self.is_running:
                return

            self._stop_event.clear()
            self.next_run_at = None
            self._thread = threading.Thread(
                target=self._run_loop,
                name="market-data-poller",
                daemon=True,
            )
            self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        with self._lock:
            thread = self._thread
            self._stop_event.set()

        if thread is not None:
            thread.join(timeout=timeout)

        with self._lock:
            self.next_run_at = None
            self._cycle_in_progress = False
            if self._thread is thread:
                self._thread = None

    def get_status(self) -> dict[str, object]:
        with self._lock:
            return {
                "interval_seconds": self.interval_seconds,
                "is_running": self.is_running,
                "cycle_in_progress": self._cycle_in_progress,
                "last_started_at": self.last_started_at,
                "last_completed_at": self.last_completed_at,
                "next_run_at": self.next_run_at,
                "last_success_at": dict(self.last_success_at),
                "last_error": dict(self.last_error),
            }

    def reload_settings(self) -> None:
        config = ensure_config_file()
        sources = config.get("sources", {})
        if not isinstance(sources, dict):
            return

        dex_settings = sources.get("dexscreener", {})
        if isinstance(dex_settings, dict):
            self.dexscreener_target_count = int(dex_settings.get("target_count", self.dexscreener_target_count))

        gmgn_settings = sources.get("gmgn", {})
        if isinstance(gmgn_settings, dict):
            self.gmgn_chain = str(gmgn_settings.get("chain", self.gmgn_chain))
            self.gmgn_limit = int(gmgn_settings.get("limit", self.gmgn_limit))

    def _run_loop(self) -> None:
        if self.run_immediately:
            self.run_once()

        while not self._stop_event.is_set():
            with self._lock:
                self.next_run_at = datetime.now() + timedelta(seconds=self.interval_seconds)

            if self._stop_event.wait(self.interval_seconds):
                break

            self.run_once()

        with self._lock:
            self.next_run_at = None
            self._cycle_in_progress = False

    def run_once(self) -> None:
        started_at = datetime.now()
        with self._lock:
            self.last_started_at = started_at
            self._cycle_in_progress = True
            self.next_run_at = None

        try:
            self._poll_dexscreener()
            if not self._stop_event.is_set():
                self._poll_gmgn()
            self._refresh_trending_config()
        finally:
            with self._lock:
                self.last_completed_at = datetime.now()
                self._cycle_in_progress = False

    def _refresh_trending_config(self) -> None:
        try:
            refresh_config_results()
        except Exception:
            logger.exception("Failed to refresh trending config")

    def _poll_dexscreener(self) -> None:
        source_name = "dexscreener"
        try:
            rows = fetch_enriched_pairs(target_count=self.dexscreener_target_count)
            if not rows:
                logger.warning("No %s data fetched; keeping previous snapshot.", source_name)
                return

            output_path = save_enriched_pairs(rows)
            with self._lock:
                self.last_success_at[source_name] = datetime.now()
                self.last_error[source_name] = None
            logger.debug("Updated %s snapshot with %s rows at %s", source_name, len(rows), output_path)
        except Exception as exc:
            with self._lock:
                self.last_error[source_name] = str(exc)
            logger.exception("Failed to refresh %s snapshot", source_name)

    def _poll_gmgn(self) -> None:
        source_name = "gmgn"
        try:
            rows = fetch_enriched_tokens(chain=self.gmgn_chain, limit=self.gmgn_limit)
            if not rows:
                logger.warning("No %s data fetched; keeping previous snapshot.", source_name)
                return

            output_path = save_enriched_tokens(rows)
            with self._lock:
                self.last_success_at[source_name] = datetime.now()
                self.last_error[source_name] = None
            logger.debug("Updated %s snapshot with %s rows at %s", source_name, len(rows), output_path)
        except Exception as exc:
            with self._lock:
                self.last_error[source_name] = str(exc)
            logger.exception("Failed to refresh %s snapshot", source_name)
