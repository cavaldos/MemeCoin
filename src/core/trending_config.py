from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RES_DATA_DIR = PROJECT_ROOT / "res" / "data"
CONFIG_PATH = RES_DATA_DIR / "config.json"

DEXSCREENER_DATA_FILENAME = "dexscreener_100_coins.json"
GMGN_DATA_FILENAME = "gmgn_100_coins.json"


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


def _coerce_int(value: object, default: int = 0) -> int:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default
    return default


def _parse_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 1_000_000_000_000:
            timestamp /= 1000
        try:
            return datetime.fromtimestamp(timestamp)
        except (OSError, OverflowError, ValueError):
            return None

    text = str(value or "").strip()
    if not text:
        return None

    normalized = text.replace("Z", "+00:00").replace("T", " ")
    for candidate in (normalized, text):
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue

    return None


def _format_datetime(value: object) -> str | None:
    parsed = _parse_datetime(value)
    if parsed is None:
        return None
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _empty_results() -> dict[str, object]:
    return {
        "generated_at": None,
        "candidate_count": 0,
        "source_counts": {
            "dexscreener": 0,
            "gmgn": 0,
            "merged": 0,
        },
        "main_trading": [],
        "strong_trending": [],
        "fast_trend": [],
    }


def _empty_history() -> dict[str, object]:
    return {
        "max_entries": 200,
        "entries": [],
    }


def get_default_config() -> dict[str, object]:
    return {
        "updated_at": None,
        "sources": {
            "dexscreener": {
                "label": "DexScreener",
                "mode": "trending",
                "target_count": 100,
                "signal_sources": [
                    "token-boosts/top/v1",
                    "token-boosts/latest/v1",
                    "community-takeovers/latest/v1",
                    "token-profiles/latest/v1",
                ],
            },
            "gmgn": {
                "label": "GMGN.ai",
                "mode": "trending",
                "chain": "sol",
                "limit": 100,
                "intervals": ["5m", "1h", "6h", "24h"],
            },
        },
        "filters": {
            "main_trading": {
                "label": "Main Trading",
                "description": "Coin age <= 5 hours, market cap >= 2,000,000, with 200,000 as the baseline floor.",
                "max_age_minutes": 300,
                "min_market_cap": 2_000_000,
                "baseline_market_cap": 200_000,
            },
            "strong_trending": {
                "label": "Strong Trending",
                "description": "Coin age <= 200 minutes, volume >= 1,000,000, market cap >= 100,000.",
                "max_age_minutes": 200,
                "min_volume": 1_000_000,
                "min_market_cap": 100_000,
            },
            "fast_trend": {
                "label": "Fast Trend",
                "description": "Volume >= 60,000 with no market cap requirement.",
                "min_volume": 60_000,
            },
        },
        "history": _empty_history(),
        "results": _empty_results(),
    }


def _deep_merge(defaults: dict[str, object], incoming: dict[str, object]) -> dict[str, object]:
    merged = deepcopy(defaults)
    for key, value in incoming.items():
        default_value = merged.get(key)
        if isinstance(default_value, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(default_value, value)
        else:
            merged[key] = value
    return merged


def _extract_source_sites(row: dict[str, object]) -> list[str]:
    candidates: list[str] = []
    source_sites = row.get("source_sites")
    if isinstance(source_sites, list):
        candidates.extend(str(source).strip().lower() for source in source_sites if str(source).strip())

    sources = row.get("sources")
    if isinstance(sources, list):
        candidates.extend(str(source).strip().lower() for source in sources if str(source).strip())

    source = row.get("source")
    if isinstance(source, str) and source.strip():
        candidates.append(source.strip().lower())

    deduped: list[str] = []
    seen: set[str] = set()
    for source_name in candidates:
        if source_name in seen:
            continue
        seen.add(source_name)
        deduped.append(source_name)
    return deduped


def _build_history_key(filter_name: str, row: dict[str, object]) -> str | None:
    candidate_key = _build_candidate_key(row)
    if candidate_key is None:
        return None
    return f"{filter_name}:{candidate_key}"


def _build_history_entry(
    filter_name: str,
    filter_label: str,
    row: dict[str, object],
    *,
    sent_to_discord: bool,
) -> dict[str, object] | None:
    history_key = _build_history_key(filter_name, row)
    if history_key is None:
        return None

    return {
        "history_key": history_key,
        "filter_key": filter_name,
        "filter_label": filter_label,
        "symbol": row.get("symbol"),
        "name": row.get("name"),
        "address": row.get("address"),
        "chain": row.get("chain"),
        "volume": _coerce_float(row.get("volume")),
        "market_cap": _coerce_float(row.get("market_cap")),
        "created_at": row.get("created_at"),
        "age_minutes": row.get("age_minutes"),
        "url": row.get("url"),
        "source_sites": _extract_source_sites(row),
        "sent_to_discord": sent_to_discord,
    }


def _normalize_history_entry(raw_entry: dict[str, object]) -> dict[str, object] | None:
    filter_key = str(raw_entry.get("filter_key") or "").strip()
    filter_label = str(raw_entry.get("filter_label") or filter_key).strip()
    source_sites = _extract_source_sites(raw_entry)

    normalized = {
        "history_key": str(raw_entry.get("history_key") or "").strip(),
        "filter_key": filter_key,
        "filter_label": filter_label,
        "symbol": raw_entry.get("symbol"),
        "name": raw_entry.get("name"),
        "address": raw_entry.get("address"),
        "chain": raw_entry.get("chain"),
        "volume": _coerce_float(raw_entry.get("volume")),
        "market_cap": _coerce_float(raw_entry.get("market_cap")),
        "created_at": raw_entry.get("created_at"),
        "age_minutes": raw_entry.get("age_minutes"),
        "url": raw_entry.get("url"),
        "source_sites": source_sites,
        "sent_to_discord": bool(raw_entry.get("sent_to_discord", False)),
    }

    if not normalized["history_key"] and filter_key:
        history_key = _build_history_key(filter_key, normalized)
        normalized["history_key"] = history_key or ""

    return normalized if normalized["history_key"] else None


def _migrate_snapshot_history(raw_history: dict[str, object]) -> list[dict[str, object]]:
    snapshots = raw_history.get("snapshots")
    if not isinstance(snapshots, list):
        return []

    default_filters = get_default_config().get("filters", {})
    filter_map = default_filters if isinstance(default_filters, dict) else {}
    migrated_entries: list[dict[str, object]] = []
    seen_keys: set[str] = set()

    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        results = snapshot.get("results")
        if not isinstance(results, dict):
            continue

        for filter_name in ("main_trading", "strong_trending", "fast_trend"):
            filter_config = filter_map.get(filter_name, {}) if isinstance(filter_map.get(filter_name, {}), dict) else {}
            filter_label = str(filter_config.get("label") or filter_name)
            rows = results.get(filter_name, [])
            if not isinstance(rows, list):
                continue

            for row in rows:
                if not isinstance(row, dict):
                    continue
                entry = _build_history_entry(filter_name, filter_label, row, sent_to_discord=True)
                if entry is None:
                    continue
                history_key = str(entry.get("history_key") or "")
                if not history_key or history_key in seen_keys:
                    continue
                seen_keys.add(history_key)
                migrated_entries.append(entry)

    return migrated_entries


def _normalize_history(raw_history: object) -> dict[str, object]:
    defaults = _empty_history()
    default_max_entries = _coerce_int(defaults.get("max_entries", 200), 200)
    if not isinstance(raw_history, dict):
        return defaults

    max_entries = _coerce_int(raw_history.get("max_entries", default_max_entries), default_max_entries)
    if max_entries < 1:
        max_entries = 1

    entries_obj = raw_history.get("entries")
    if isinstance(entries_obj, list):
        raw_entries = [entry for entry in entries_obj if isinstance(entry, dict)]
    else:
        raw_entries = _migrate_snapshot_history(raw_history)

    normalized_entries: list[dict[str, object]] = []
    seen_keys: set[str] = set()
    for raw_entry in raw_entries:
        entry = _normalize_history_entry(raw_entry)
        if entry is None:
            continue
        history_key = str(entry.get("history_key") or "")
        if not history_key or history_key in seen_keys:
            continue
        seen_keys.add(history_key)
        normalized_entries.append(entry)

    return {
        "max_entries": max_entries,
        "entries": normalized_entries[:max_entries],
    }


def _normalize_config(raw_config: object) -> dict[str, object]:
    defaults = get_default_config()
    if not isinstance(raw_config, dict):
        return defaults

    raw_history = raw_config.get("history")
    normalized = _deep_merge(defaults, raw_config)
    if not isinstance(normalized.get("results"), dict):
        normalized["results"] = _empty_results()
    normalized["history"] = _normalize_history(raw_history)
    return normalized


def get_config_path() -> str:
    return str(CONFIG_PATH)


def load_snapshot(filename: str) -> list[dict]:
    filepath = RES_DATA_DIR / filename
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def load_config() -> dict[str, object]:
    if not CONFIG_PATH.exists():
        return get_default_config()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file_handle:
            raw_config = json.load(file_handle)
    except (OSError, json.JSONDecodeError):
        return get_default_config()
    return _normalize_config(raw_config)


def load_history_entries() -> list[dict[str, object]]:
    config = load_config()
    history = config.get("history", {})
    if not isinstance(history, dict):
        return []
    entries = history.get("entries", [])
    return [entry for entry in entries if isinstance(entry, dict)] if isinstance(entries, list) else []


def save_config(config: dict[str, object]) -> str:
    normalized = _normalize_config(config)
    RES_DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = CONFIG_PATH.with_suffix(".json.tmp")
    with open(temp_path, "w", encoding="utf-8") as file_handle:
        json.dump(normalized, file_handle, indent=2, ensure_ascii=False)
        file_handle.flush()
        os.fsync(file_handle.fileno())
    os.replace(temp_path, CONFIG_PATH)
    return str(CONFIG_PATH)


def ensure_config_file() -> dict[str, object]:
    config = load_config()
    if not CONFIG_PATH.exists():
        save_config(config)
    return config


def reset_config() -> dict[str, object]:
    config = get_default_config()
    save_config(config)
    return config


def _age_minutes(created_at: object) -> int | None:
    parsed = _parse_datetime(created_at)
    if parsed is None:
        return None
    now = datetime.now(parsed.tzinfo) if parsed.tzinfo is not None else datetime.now()
    elapsed_seconds = max((now - parsed).total_seconds(), 0)
    return int(elapsed_seconds // 60)


def _build_candidate_key(row: dict[str, object]) -> str | None:
    chain = str(row.get("chain") or "").strip().lower()
    address = str(row.get("address") or "").strip().lower()
    if chain and address:
        return f"{chain}:{address}"
    url = str(row.get("url") or "").strip().lower()
    if url:
        return url
    return None


def _normalize_source_row(source_name: str, row: dict[str, object], rank: int) -> dict[str, object]:
    created_value = (
        row.get("created_at")
        or row.get("pair_created_at")
        or row.get("creation_date")
        or row.get("creation_timestamp")
    )
    market_cap = row.get("market_cap") or row.get("fdv")
    volume = row.get("volume_24h") if source_name == "dexscreener" else row.get("volume")

    return {
        "symbol": row.get("symbol"),
        "name": row.get("name"),
        "address": row.get("address"),
        "chain": row.get("chain"),
        "volume": _coerce_float(volume),
        "market_cap": _coerce_float(market_cap),
        "created_at": _format_datetime(created_value),
        "url": row.get("coin_url") or row.get("url"),
        "pair_address": row.get("pair_address"),
        "source": source_name,
        "source_rank": rank,
        "signal_score": _coerce_float(row.get("signal_score")),
    }


def _candidate_priority(row: dict[str, object]) -> tuple[float, float, float]:
    return (
        _coerce_float(row.get("signal_score")),
        _coerce_float(row.get("market_cap")),
        _coerce_float(row.get("volume")),
    )


def _merge_candidate(existing: dict[str, object], incoming: dict[str, object]) -> dict[str, object]:
    existing_created = _parse_datetime(existing.get("created_at"))
    incoming_created = _parse_datetime(incoming.get("created_at"))

    if existing_created is None:
        chosen_created = incoming_created
    elif incoming_created is None:
        chosen_created = existing_created
    else:
        chosen_created = min(existing_created, incoming_created)

    existing["volume"] = max(_coerce_float(existing.get("volume")), _coerce_float(incoming.get("volume")))
    existing["market_cap"] = max(
        _coerce_float(existing.get("market_cap")),
        _coerce_float(incoming.get("market_cap")),
    )
    existing["signal_score"] = max(
        _coerce_float(existing.get("signal_score")),
        _coerce_float(incoming.get("signal_score")),
    )
    existing["created_at"] = _format_datetime(chosen_created)

    if _candidate_priority(incoming) > _candidate_priority(existing):
        for field in ("symbol", "name", "url", "pair_address"):
            if incoming.get(field):
                existing[field] = incoming.get(field)

    current_sources = existing.get("sources", [])
    sources = set(str(item) for item in current_sources) if isinstance(current_sources, list) else set()
    sources.add(str(incoming.get("source") or ""))
    existing["sources"] = sorted(source for source in sources if source)

    source_details = existing.setdefault("source_details", {})
    if isinstance(source_details, dict):
        source_details[str(incoming.get("source") or "unknown")] = {
            "rank": incoming.get("source_rank"),
            "volume": _coerce_float(incoming.get("volume")),
            "market_cap": _coerce_float(incoming.get("market_cap")),
            "created_at": incoming.get("created_at"),
            "url": incoming.get("url"),
            "signal_score": _coerce_float(incoming.get("signal_score")),
        }

    return existing


def _build_candidates(
    dexscreener_rows: list[dict],
    gmgn_rows: list[dict],
    config: dict[str, object],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    source_settings = config.get("sources", {})
    if not isinstance(source_settings, dict):
        source_settings = {}

    dex_limit = int(source_settings.get("dexscreener", {}).get("target_count", 100)) if isinstance(source_settings.get("dexscreener"), dict) else 100
    gmgn_limit = int(source_settings.get("gmgn", {}).get("limit", 100)) if isinstance(source_settings.get("gmgn"), dict) else 100

    merged: dict[str, dict[str, object]] = {}
    trimmed_dex_rows = dexscreener_rows[:dex_limit]
    trimmed_gmgn_rows = gmgn_rows[:gmgn_limit]

    for source_name, rows in (("dexscreener", trimmed_dex_rows), ("gmgn", trimmed_gmgn_rows)):
        for rank, row in enumerate(rows, start=1):
            normalized = _normalize_source_row(source_name, row, rank)
            key = _build_candidate_key(normalized)
            if key is None:
                continue

            if key not in merged:
                merged[key] = {
                    "symbol": normalized.get("symbol"),
                    "name": normalized.get("name"),
                    "address": normalized.get("address"),
                    "chain": normalized.get("chain"),
                    "volume": _coerce_float(normalized.get("volume")),
                    "market_cap": _coerce_float(normalized.get("market_cap")),
                    "created_at": normalized.get("created_at"),
                    "url": normalized.get("url"),
                    "pair_address": normalized.get("pair_address"),
                    "signal_score": _coerce_float(normalized.get("signal_score")),
                    "sources": [source_name],
                    "source_details": {
                        source_name: {
                            "rank": normalized.get("source_rank"),
                            "volume": _coerce_float(normalized.get("volume")),
                            "market_cap": _coerce_float(normalized.get("market_cap")),
                            "created_at": normalized.get("created_at"),
                            "url": normalized.get("url"),
                            "signal_score": _coerce_float(normalized.get("signal_score")),
                        }
                    },
                }
                continue

            merged[key] = _merge_candidate(merged[key], normalized)

    candidates = list(merged.values())
    for candidate in candidates:
        candidate["age_minutes"] = _age_minutes(candidate.get("created_at"))

    source_counts = {
        "dexscreener": len(trimmed_dex_rows),
        "gmgn": len(trimmed_gmgn_rows),
        "merged": len(candidates),
    }
    return candidates, source_counts


def _matches_filter(candidate: dict[str, object], filter_config: dict[str, object]) -> bool:
    age_minutes = candidate.get("age_minutes")
    volume = _coerce_float(candidate.get("volume"))
    market_cap = _coerce_float(candidate.get("market_cap"))

    max_age_minutes = filter_config.get("max_age_minutes")
    if max_age_minutes is not None:
        if age_minutes is None or _coerce_int(age_minutes, 0) > _coerce_int(max_age_minutes, 0):
            return False

    min_volume = filter_config.get("min_volume")
    if min_volume is not None and volume < _coerce_float(min_volume):
        return False

    min_market_cap = filter_config.get("min_market_cap")
    if min_market_cap is not None and market_cap < _coerce_float(min_market_cap):
        return False

    baseline_market_cap = filter_config.get("baseline_market_cap")
    if baseline_market_cap is not None and market_cap < _coerce_float(baseline_market_cap):
        return False

    return True


def _sort_result_items(filter_name: str, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    def sort_key(row: dict[str, object]) -> tuple[float, float, int, str]:
        age_minutes = row.get("age_minutes")
        age_key = _coerce_int(age_minutes, 10**9) if age_minutes is not None else 10**9
        if filter_name == "main_trading":
            return (
                -_coerce_float(row.get("market_cap")),
                -_coerce_float(row.get("volume")),
                age_key,
                str(row.get("symbol") or ""),
            )
        return (
            -_coerce_float(row.get("volume")),
            -_coerce_float(row.get("market_cap")),
            age_key,
            str(row.get("symbol") or ""),
        )

    return sorted(rows, key=sort_key)


def _collect_new_history_entries(
    config: dict[str, object],
    results: dict[str, object],
) -> list[dict[str, object]]:
    history = config.get("history", {})
    history_entries = history.get("entries", []) if isinstance(history, dict) else []
    existing_keys = {
        str(entry.get("history_key") or "")
        for entry in history_entries
        if isinstance(entry, dict)
    }

    filters_obj = config.get("filters", {})
    filters = filters_obj if isinstance(filters_obj, dict) else {}
    new_entries: list[dict[str, object]] = []

    for filter_name in ("main_trading", "strong_trending", "fast_trend"):
        filter_config_obj = filters.get(filter_name, {})
        filter_config = filter_config_obj if isinstance(filter_config_obj, dict) else {}
        filter_label = str(filter_config.get("label") or filter_name)

        current_rows_obj = results.get(filter_name, [])
        current_rows = [row for row in current_rows_obj if isinstance(row, dict)] if isinstance(current_rows_obj, list) else []
        for row in current_rows:
            entry = _build_history_entry(filter_name, filter_label, row, sent_to_discord=False)
            if entry is None:
                continue
            history_key = str(entry.get("history_key") or "")
            if not history_key or history_key in existing_keys:
                continue
            existing_keys.add(history_key)
            new_entries.append(entry)

    return new_entries


def _append_history_entries(config: dict[str, object], new_entries: list[dict[str, object]]) -> None:
    if not new_entries:
        return

    history = config.get("history", {})
    if not isinstance(history, dict):
        history = _empty_history()
        config["history"] = history

    existing_entries = history.get("entries")
    history_entries = [entry for entry in existing_entries if isinstance(entry, dict)] if isinstance(existing_entries, list) else []
    history["entries"] = list(new_entries) + history_entries

    max_entries = _coerce_int(history.get("max_entries", 200), 200)
    if max_entries < 1:
        max_entries = 1
    history["entries"] = history["entries"][:max_entries]


def _mark_history_entries_sent(config: dict[str, object], sent_keys: set[str]) -> None:
    if not sent_keys:
        return

    history = config.get("history", {})
    if not isinstance(history, dict):
        return

    entries = history.get("entries")
    if not isinstance(entries, list):
        return

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        history_key = str(entry.get("history_key") or "")
        if history_key in sent_keys:
            entry["sent_to_discord"] = True


def _get_pending_history_entries(config: dict[str, object]) -> list[dict[str, object]]:
    history = config.get("history", {})
    if not isinstance(history, dict):
        return []

    entries = history.get("entries")
    if not isinstance(entries, list):
        return []

    return [
        entry
        for entry in entries
        if isinstance(entry, dict) and not bool(entry.get("sent_to_discord", False))
    ]


def _send_new_entry_alerts(
    new_entries: list[dict[str, object]],
    detected_at: str,
) -> set[str]:
    if not new_entries:
        return set()

    from .discord import send_filtered_alert

    sent_keys: set[str] = set()
    for entry in new_entries:
        filter_key = str(entry.get("filter_key") or "")
        filter_label = str(entry.get("filter_label") or filter_key)
        if not filter_key:
            continue
        if send_filtered_alert(filter_key, filter_label, entry, detected_at):
            history_key = str(entry.get("history_key") or "")
            if history_key:
                sent_keys.add(history_key)
    return sent_keys


def refresh_config_results(
    *,
    config: dict[str, object] | None = None,
    dexscreener_rows: list[dict] | None = None,
    gmgn_rows: list[dict] | None = None,
    send_alerts: bool = True,
) -> dict[str, object]:
    active_config = _normalize_config(config if config is not None else load_config())
    dex_rows = dexscreener_rows if dexscreener_rows is not None else load_snapshot(DEXSCREENER_DATA_FILENAME)
    gmgn_rows = gmgn_rows if gmgn_rows is not None else load_snapshot(GMGN_DATA_FILENAME)

    candidates, source_counts = _build_candidates(dex_rows, gmgn_rows, active_config)

    filters = active_config.get("filters", {})
    if not isinstance(filters, dict):
        filters = {}

    results = _empty_results()
    results["generated_at"] = _now_string()
    results["candidate_count"] = len(candidates)
    results["source_counts"] = source_counts

    for filter_name in ("main_trading", "strong_trending", "fast_trend"):
        filter_config = filters.get(filter_name, {})
        if not isinstance(filter_config, dict):
            filter_config = {}
        matched = [candidate for candidate in candidates if _matches_filter(candidate, filter_config)]
        results[filter_name] = _sort_result_items(filter_name, matched)

    new_entries = _collect_new_history_entries(active_config, results)
    active_config["updated_at"] = results["generated_at"]
    active_config["results"] = results
    _append_history_entries(active_config, new_entries)
    save_config(active_config)
    if send_alerts:
        pending_entries = _get_pending_history_entries(active_config)
        sent_keys = _send_new_entry_alerts(pending_entries, str(results["generated_at"]))
        if sent_keys:
            _mark_history_entries_sent(active_config, sent_keys)
            save_config(active_config)
    return active_config
