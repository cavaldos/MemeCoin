import json
import logging
import os
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger(__name__)

TREND_SIGNAL_SOURCES = (
    ("token-boosts/top/v1", "top_boosts", 4),
    ("token-boosts/latest/v1", "latest_boosts", 3),
    ("community-takeovers/latest/v1", "community_takeovers", 2),
    ("token-profiles/latest/v1", "token_profiles", 1),
)


def _coerce_float(value: object) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class DexScreenerClient:
    BASE_URL = "https://api.dexscreener.com"
    
    CHAINS = [
        "solana", "ethereum", "bsc", "base", "arbitrum", "optimism", 
        "polygon", "avalanche", "tron", "fantom", "cronos", "aptos",
        "sui", "near", "sei", "osmosis", "injective", "linea",
        "mantle", "scroll", "blast", "mode", "zora", "sonic"
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
        })

    def _get_json_list(self, path: str, limit: int = 100) -> Optional[list]:
        url = f"{self.BASE_URL}/{path}"
        params: dict = {}
        if limit:
            params["limit"] = str(min(limit, 100))

        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else None
        except requests.RequestException as e:
            logger.warning("Error getting %s: %s", path, e)
            return None

    def get_token_profiles(self, limit: int = 100) -> Optional[list]:
        return self._get_json_list("token-profiles/latest/v1", limit)

    def get_boosts_latest(self, limit: int = 100) -> Optional[list]:
        return self._get_json_list("token-boosts/latest/v1", limit)

    def get_boosts_top(self, limit: int = 100) -> Optional[list]:
        return self._get_json_list("token-boosts/top/v1", limit)

    def get_community_takeovers(self, limit: int = 100) -> Optional[list]:
        return self._get_json_list("community-takeovers/latest/v1", limit)

    def get_tokens(self, chain_id: str, token_addresses: list[str]) -> Optional[list]:
        if not token_addresses:
            return None

        joined_addresses = ",".join(token_addresses[:30])
        url = f"{self.BASE_URL}/tokens/v1/{chain_id}/{joined_addresses}"
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list):
                return data
            return None
        except requests.RequestException as e:
            logger.warning("Error getting token details for %s: %s", chain_id, e)
            return None

    @staticmethod
    def _pair_priority(pair: dict) -> tuple[float, float, float, float]:
        volume_data = pair.get("volume", {})
        liquidity_data = pair.get("liquidity", {})
        return (
            _coerce_float(pair.get("marketCap") or pair.get("fdv")),
            _coerce_float(volume_data.get("h24") if isinstance(volume_data, dict) else 0),
            _coerce_float(liquidity_data.get("usd") if isinstance(liquidity_data, dict) else 0),
            _coerce_float(pair.get("pairCreatedAt")),
        )

    def get_top_trending_pairs(self, target_count: int = 100) -> list[dict]:
        candidate_map: dict[tuple[str, str], dict] = {}

        for endpoint, signal_name, weight in TREND_SIGNAL_SOURCES:
            rows = self._get_json_list(endpoint, limit=100)
            if not rows:
                continue

            total_rows = len(rows)
            for rank, row in enumerate(rows, start=1):
                chain_id = row.get("chainId")
                token_address = row.get("tokenAddress")
                if not chain_id or not token_address:
                    continue

                key = (str(chain_id), str(token_address))
                score = weight * max(total_rows - rank + 1, 1)
                existing = candidate_map.get(key)
                if existing is None:
                    candidate_map[key] = {
                        "chain_id": chain_id,
                        "token_address": token_address,
                        "signals": [signal_name],
                        "signal_score": score,
                        "best_rank": rank,
                    }
                    continue

                existing["signal_score"] = _coerce_float(existing.get("signal_score")) + score
                existing["best_rank"] = min(int(existing.get("best_rank", rank)), rank)
                signals = existing.setdefault("signals", [])
                if isinstance(signals, list) and signal_name not in signals:
                    signals.append(signal_name)

        grouped_addresses: dict[str, list[str]] = {}
        for chain_id, token_address in candidate_map:
            grouped_addresses.setdefault(chain_id, []).append(token_address)

        selected_pairs: dict[tuple[str, str], dict] = {}
        for chain_id, addresses in grouped_addresses.items():
            for index in range(0, len(addresses), 30):
                batch = addresses[index:index + 30]
                pairs = self.get_tokens(chain_id, batch)
                if not pairs:
                    continue

                for pair in pairs:
                    base_token = pair.get("baseToken", {})
                    token_address = base_token.get("address") if isinstance(base_token, dict) else None
                    if not token_address:
                        continue

                    key = (str(pair.get("chainId") or chain_id), str(token_address))
                    existing_pair = selected_pairs.get(key)
                    if existing_pair is None or self._pair_priority(pair) > self._pair_priority(existing_pair):
                        selected_pairs[key] = pair

        enriched_pairs = []
        for key, metadata in candidate_map.items():
            pair = selected_pairs.get(key)
            if pair is None:
                continue
            enriched_pair = enrich_pair(pair)
            enriched_pair["trend_signals"] = metadata.get("signals", [])
            enriched_pair["signal_score"] = metadata.get("signal_score")
            enriched_pair["best_rank"] = metadata.get("best_rank")
            enriched_pairs.append(enriched_pair)

        enriched_pairs.sort(
            key=lambda pair: (
                -_coerce_float(pair.get("signal_score")),
                -_coerce_float(pair.get("volume_24h")),
                -_coerce_float(pair.get("market_cap") or pair.get("fdv")),
                -_coerce_float(pair.get("liquidity_usd")),
            )
        )
        return enriched_pairs[:target_count]


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RES_DATA_DIR = os.path.join(PROJECT_ROOT, "res", "data")
DATA_FILENAME = "dexscreener_100_coins.json"


def _build_output_path(output_path: str | None = None) -> str:
    return output_path or os.path.join(RES_DATA_DIR, DATA_FILENAME)


def _write_json_atomic(rows: list[dict], output_path: str) -> str:
    temp_path = f"{output_path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, output_path)
    return output_path


def enrich_pair(pair: dict) -> dict:
    base_token = pair.get("baseToken", {})
    quote_token = pair.get("quoteToken", {})
    liquidity_data = pair.get("liquidity", {})
    volume_data = pair.get("volume", {})
    price_change_data = pair.get("priceChange", {})
    pair_created_ts = pair.get("pairCreatedAt", 0)
    created_at = (
        datetime.fromtimestamp(pair_created_ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
        if pair_created_ts
        else None
    )
    coin_url = pair.get("url")

    return {
        "symbol": base_token.get("symbol"),
        "name": base_token.get("name"),
        "address": base_token.get("address"),
        "price_usd": pair.get("priceUsd"),
        "price_change_24h": price_change_data.get("h24") if isinstance(price_change_data, dict) else None,
        "liquidity_usd": liquidity_data.get("usd") if isinstance(liquidity_data, dict) else None,
        "volume_24h": volume_data.get("h24") if isinstance(volume_data, dict) else None,
        "market_cap": pair.get("marketCap") or pair.get("fdv"),
        "fdv": pair.get("fdv"),
        "chain": pair.get("chainId"),
        "dex_id": pair.get("dexId"),
        "pair_address": pair.get("pairAddress"),
        "pair_created_at": created_at,
        "created_at": created_at,
        "quote_token_symbol": quote_token.get("symbol"),
        "trend_signals": pair.get("trend_signals", []),
        "signal_score": pair.get("signal_score"),
        "best_rank": pair.get("best_rank"),
        "url": coin_url,
        "coin_url": coin_url,
    }


def fetch_enriched_pairs(target_count: int = 100, client: DexScreenerClient | None = None) -> list[dict]:
    active_client = client or DexScreenerClient()
    pairs = active_client.get_top_trending_pairs(target_count=target_count)
    if not pairs:
        return []
    return [pair if "symbol" in pair else enrich_pair(pair) for pair in pairs]


def save_enriched_pairs(rows: list[dict], output_path: str | None = None) -> str:
    os.makedirs(RES_DATA_DIR, exist_ok=True)
    resolved_output_path = _build_output_path(output_path)
    return _write_json_atomic(rows, resolved_output_path)


def format_pair(pair: dict) -> str:
    """Format enriched pair data for display"""
    symbol = pair.get("symbol", "N/A")
    name = pair.get("name", "N/A")
    price = pair.get("price_usd", "N/A")
    liquidity_usd = pair.get("liquidity_usd", 0) or 0
    volume = pair.get("volume_24h", 0) or 0
    market_cap = pair.get("market_cap") or pair.get("fdv") or 0
    chain = pair.get("chain", "N/A")
    dex_id = pair.get("dex_id", "N/A")
    token_address = pair.get("address", "")
    url = pair.get("coin_url") or pair.get("url", "")

    created_at = pair.get("created_at") or pair.get("pair_created_at") or "N/A"
    
    token_short = token_address[:10] + "..." if len(token_address) > 10 else token_address
    
    return (f"{symbol} ({name}) | ${price} | Liq: ${liquidity_usd:,.0f} | "
            f"Vol: ${volume:,.0f} | MC: ${market_cap:,.0f} | Chain: {chain} | Dex: {dex_id} | "
            f"Created: {created_at} | Token: {token_short} | {url}")

def main():
    os.makedirs(RES_DATA_DIR, exist_ok=True)

    print("Fetching top 100 trending coin pairs from DexScreener...")
    print("=" * 80)
    
    enriched_pairs = fetch_enriched_pairs(target_count=100)

    if not enriched_pairs:
        print("No trending pairs found from DexScreener public signals.")
    else:
        print(f"\nFound {len(enriched_pairs)} pairs:\n")
        for i, pair in enumerate(enriched_pairs, 1):
            print(f"{i:3}. {format_pair(pair)}")
        
        print("\n" + "=" * 80)
        print(f"Total: {len(enriched_pairs)} pairs")
        
        output_path = save_enriched_pairs(enriched_pairs)
        print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
