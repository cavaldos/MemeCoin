"""
Coin database – stores matched coins in separate JSON files per trend type.

Files:
    res/data/db/main_trend.json
    res/data/db/strong_trend.json
    res/data/db/fast_trend.json

Each file is a JSON array of coin entries. Deduplication is based on
chain:address key so the same coin won't be stored twice in the same trend.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from copy import deepcopy
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_DIR = PROJECT_ROOT / "res" / "data" / "db"

FILTER_TO_FILENAME: dict[str, str] = {
    "main_trading": "main_trend.json",
    "strong_trending": "strong_trend.json",
    "fast_trend": "fast_trend.json",
}

_lock = threading.Lock()


def _now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _coerce_float(value: object) -> float:
    if value in (None, ""):
        return 0.0
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def _build_coin_key(row: dict[str, object]) -> str | None:
    """Build a unique key from chain:address."""
    chain = str(row.get("chain") or "").strip().lower()
    address = str(row.get("address") or "").strip().lower()
    if chain and address:
        return f"{chain}:{address}"
    return None


def _db_path(filter_key: str) -> Path:
    filename = FILTER_TO_FILENAME.get(filter_key)
    if filename is None:
        raise ValueError(f"Unknown filter_key: {filter_key}")
    return DB_DIR / filename


def _ensure_db_dir() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)


def _load_db(filter_key: str) -> list[dict[str, object]]:
    """Load coin list from a trend database file."""
    path = _db_path(filter_key)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        logger.warning("Failed to load %s, returning empty list", path)
        return []
    return data if isinstance(data, list) else []


def _save_db(filter_key: str, coins: list[dict[str, object]]) -> str:
    """Save coin list to a trend database file (atomic write)."""
    _ensure_db_dir()
    path = _db_path(filter_key)
    temp_path = path.with_suffix(".json.tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(coins, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, path)
    return str(path)


def _build_coin_entry(filter_key: str, row: dict[str, object]) -> dict[str, object]:
    """Build a normalized coin entry for the database."""
    now = _now_string()

    source_sites: list[str] = []
    for field in ("source_sites", "sources"):
        val = row.get(field)
        if isinstance(val, list):
            source_sites.extend(str(s).strip().lower() for s in val if str(s).strip())
    source_val = row.get("source")
    if isinstance(source_val, str) and source_val.strip():
        source_sites.append(source_val.strip().lower())
    source_sites = list(dict.fromkeys(source_sites))  # dedupe preserving order

    return {
        "coin_key": _build_coin_key(row),
        "filter_key": filter_key,
        "symbol": row.get("symbol"),
        "name": row.get("name"),
        "address": row.get("address"),
        "chain": row.get("chain"),
        "volume": _coerce_float(row.get("volume")),
        "volume_at_added": _coerce_float(row.get("volume")),
        "market_cap": _coerce_float(row.get("market_cap")),
        "created_at": row.get("created_at"),
        "age_minutes": row.get("age_minutes"),
        "url": row.get("url"),
        "source_sites": source_sites,
        "added_at": now,
        "updated_at": now,
        "volume_change_percent_24h": _coerce_float(row.get("volume_change_percent_24h")),
        "sent_to_discord": False,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_coins(filter_key: str) -> list[dict[str, object]]:
    """Load all coins for a given trend type. Thread-safe."""
    with _lock:
        return _load_db(filter_key)


def load_all_coins() -> dict[str, list[dict[str, object]]]:
    """Load coins from all 3 trend databases."""
    result: dict[str, list[dict[str, object]]] = {}
    with _lock:
        for fk in FILTER_TO_FILENAME:
            result[fk] = _load_db(fk)
    return result


def add_coins(filter_key: str, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """
    Add new coins to a trend database with deduplication.
    Returns only the newly added entries.
    """
    if not rows:
        return []

    with _lock:
        coins = _load_db(filter_key)
        existing_keys: set[str] = set()
        for coin in coins:
            key = str(coin.get("coin_key") or "")
            if key:
                existing_keys.add(key)

        new_entries: list[dict[str, object]] = []
        for row in rows:
            coin_key = _build_coin_key(row)
            if coin_key is None or coin_key in existing_keys:
                continue
            entry = _build_coin_entry(filter_key, row)
            coins.append(entry)
            new_entries.append(entry)
            existing_keys.add(coin_key)

        if new_entries:
            _save_db(filter_key, coins)
            logger.info("Added %d new coins to %s", len(new_entries), filter_key)

        return new_entries


def update_coins(filter_key: str, rows: list[dict[str, object]]) -> int:
    """
    Update existing coins in a trend database with fresh market data.
    Returns the number of coins updated.
    """
    if not rows:
        return 0

    row_lookup: dict[str, dict[str, object]] = {}
    for row in rows:
        key = _build_coin_key(row)
        if key:
            row_lookup[key] = row

    if not row_lookup:
        return 0

    with _lock:
        coins = _load_db(filter_key)
        updated_count = 0
        now = _now_string()

        for coin in coins:
            coin_key = str(coin.get("coin_key") or "")
            fresh = row_lookup.get(coin_key)
            if fresh is None:
                continue

            coin["volume"] = _coerce_float(fresh.get("volume"))
            coin["market_cap"] = _coerce_float(fresh.get("market_cap"))
            coin["age_minutes"] = fresh.get("age_minutes")
            coin["url"] = fresh.get("url") or coin.get("url")
            coin["volume_change_percent_24h"] = _coerce_float(fresh.get("volume_change_percent_24h"))
            coin["updated_at"] = now
            updated_count += 1

        if updated_count:
            _save_db(filter_key, coins)

        return updated_count


def delete_coin(filter_key: str, symbol: str) -> bool:
    """Delete a coin by symbol from a trend database. Returns True if found and deleted."""
    symbol_lower = symbol.strip().lower()
    with _lock:
        coins = _load_db(filter_key)
        original_len = len(coins)
        coins = [c for c in coins if str(c.get("symbol") or "").strip().lower() != symbol_lower]
        if len(coins) == original_len:
            return False
        _save_db(filter_key, coins)
        return True


def delete_coin_all_trends(symbol: str) -> list[str]:
    """Delete a coin by symbol from ALL trend databases. Returns list of filter_keys where it was found."""
    deleted_from: list[str] = []
    for fk in FILTER_TO_FILENAME:
        if delete_coin(fk, symbol):
            deleted_from.append(fk)
    return deleted_from


def clear_coins(filter_key: str) -> int:
    """Clear all coins from a trend database. Returns the count of removed coins."""
    with _lock:
        coins = _load_db(filter_key)
        count = len(coins)
        if count > 0:
            _save_db(filter_key, [])
        return count


def find_coin(symbol: str) -> list[dict[str, object]]:
    """Find a coin by symbol across all trend databases. Returns list of matches with filter_key."""
    symbol_lower = symbol.strip().lower()
    results: list[dict[str, object]] = []
    with _lock:
        for fk in FILTER_TO_FILENAME:
            coins = _load_db(fk)
            for coin in coins:
                if str(coin.get("symbol") or "").strip().lower() == symbol_lower:
                    entry = deepcopy(coin)
                    entry["filter_key"] = fk
                    results.append(entry)
    return results


def get_stats() -> dict[str, object]:
    """Get statistics across all trend databases."""
    stats: dict[str, object] = {}
    total = 0
    with _lock:
        for fk in FILTER_TO_FILENAME:
            coins = _load_db(fk)
            stats[fk] = len(coins)
            total += len(coins)
    stats["total"] = total
    return stats


def get_unsent_coins(filter_key: str) -> list[dict[str, object]]:
    """Return coins that have not yet been sent to Discord."""
    with _lock:
        coins = _load_db(filter_key)
        return [c for c in coins if not bool(c.get("sent_to_discord", False))]


def mark_coins_sent(filter_key: str, coin_keys: set[str]) -> int:
    """Mark coins as sent to Discord by their coin_key. Returns count marked."""
    if not coin_keys:
        return 0

    with _lock:
        coins = _load_db(filter_key)
        marked = 0
        for coin in coins:
            key = str(coin.get("coin_key") or "")
            if key in coin_keys and not bool(coin.get("sent_to_discord", False)):
                coin["sent_to_discord"] = True
                marked += 1

        if marked:
            _save_db(filter_key, coins)
        return marked
