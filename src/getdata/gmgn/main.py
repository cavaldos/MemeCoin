import json
import logging
import os
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

SUPPORTED_TREND_INTERVALS = ("5m", "1h", "6h", "24h")
INTERVAL_WEIGHTS = {
    "5m": 4,
    "1h": 3,
    "6h": 2,
    "24h": 1,
}


def _coerce_float(value: object) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class GMGNClient:
    BASE_URL = "https://gmgn.ai"
    API_URL = "https://gmgn.ai/defi/quotation/v1"
    
    CHAINS = {
        "sol": "solana",
        "eth": "ethereum", 
        "bsc": "binance",
        "base": "base",
        "tron": "tron",
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://gmgn.ai/?chain=sol",
        })
    
    def get_trending_tokens(self, chain: str = "sol", time_range: str = "1h", 
                           orderby: str = "volume", limit: int = 100) -> Optional[dict]:
        """Get trending tokens from GMGN"""
        url = f"{self.API_URL}/rank/{chain}/swaps/{time_range}"
        params = {
            "orderby": orderby,
            "direction": "desc",
            "limit": limit,
            "filters[]": "not_honeypot",
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning("Error getting trending tokens: %s", e)
            return None
    
    def get_new_tokens(self, chain: str = "sol", limit: int = 100) -> Optional[dict]:
        """Get newest tokens - try different approaches"""
        url = f"{self.API_URL}/rank/{chain}/swaps/1h"
        params = {
            "orderby": "created_at",
            "direction": "desc", 
            "limit": limit,
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning("Error getting new tokens: %s", e)
            return None
    
    def get_new_pools(self, chain: str = "sol", limit: int = 100) -> Optional[dict]:
        """Get new pools - try with different time range"""
        for time_range in ["5m", "15m", "1h"]:
            url = f"{self.API_URL}/rank/{chain}/swaps/{time_range}"
            params = {
                "orderby": "created_at",
                "direction": "desc",
                "limit": limit,
            }
            
            try:
                resp = self.session.get(url, params=params, timeout=30)
                if resp.status_code == 200:
                    return resp.json()
            except requests.RequestException:
                continue
        
        return None
    
    def get_top_gainers(self, chain: str = "sol", time_range: str = "1h", limit: int = 100) -> Optional[dict]:
        """Get top gainers"""
        url = f"{self.API_URL}/rank/{chain}/swaps/{time_range}"
        params = {
            "orderby": "price_change_percent",
            "direction": "desc",
            "limit": limit,
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning("Error getting top gainers: %s", e)
            return None
    
    def get_tokens_by_volume(self, chain: str = "sol", time_range: str = "1h", 
                            limit: int = 100) -> Optional[dict]:
        """Get tokens sorted by volume"""
        return self.get_trending_tokens(chain, time_range, "volume", limit)

    def get_top_trending_tokens(
        self,
        chain: str = "sol",
        limit: int = 100,
        intervals: tuple[str, ...] = SUPPORTED_TREND_INTERVALS,
    ) -> list[dict]:
        merged_tokens: dict[str, dict] = {}

        for interval in intervals:
            result = self.get_trending_tokens(chain=chain, time_range=interval, limit=limit)
            tokens = extract_tokens(result)
            if not tokens:
                continue

            interval_weight = INTERVAL_WEIGHTS.get(interval, 1)
            total_tokens = len(tokens)
            for rank, token in enumerate(tokens, start=1):
                address = token.get("address")
                if not address:
                    continue

                score = interval_weight * max(total_tokens - rank + 1, 1)
                existing = merged_tokens.get(address)
                if existing is None:
                    token_copy = dict(token)
                    token_copy["trend_intervals"] = [interval]
                    token_copy["signal_score"] = score
                    token_copy["best_rank"] = rank
                    merged_tokens[address] = token_copy
                    continue

                existing["signal_score"] = _coerce_float(existing.get("signal_score")) + score
                existing["best_rank"] = min(int(existing.get("best_rank", rank)), rank)

                trend_intervals = existing.setdefault("trend_intervals", [])
                if isinstance(trend_intervals, list) and interval not in trend_intervals:
                    trend_intervals.append(interval)

                incoming_priority = (
                    _coerce_float(token.get("volume")),
                    _coerce_float(token.get("market_cap")),
                    -rank,
                )
                existing_priority = (
                    _coerce_float(existing.get("volume")),
                    _coerce_float(existing.get("market_cap")),
                    -int(existing.get("best_rank", rank)),
                )
                if incoming_priority > existing_priority:
                    current_score = existing.get("signal_score")
                    current_intervals = existing.get("trend_intervals")
                    current_best_rank = existing.get("best_rank")
                    existing.clear()
                    existing.update(token)
                    existing["signal_score"] = current_score
                    existing["trend_intervals"] = current_intervals
                    existing["best_rank"] = current_best_rank

        sorted_tokens = sorted(
            merged_tokens.values(),
            key=lambda token: (
                -_coerce_float(token.get("signal_score")),
                -_coerce_float(token.get("volume")),
                -_coerce_float(token.get("market_cap")),
                int(token.get("best_rank", 10**6)),
            ),
        )
        return sorted_tokens[:limit]
    
    def get_smart_money_tokens(self, chain: str = "sol", time_range: str = "6h", 
                               limit: int = 100) -> Optional[dict]:
        """Get tokens with smart money activity"""
        url = f"{self.API_URL}/rank/{chain}/swaps/{time_range}"
        params = {
            "orderby": "smart_money",
            "direction": "desc",
            "limit": limit,
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning("Error getting smart money tokens: %s", e)
            return None


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
RES_DATA_DIR = os.path.join(PROJECT_ROOT, "res", "data")
DATA_FILENAME = "gmgn_100_coins.json"


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


def extract_tokens(result: dict | None) -> list[dict]:
    if not result or "data" not in result:
        return []

    data = result.get("data", {})
    if isinstance(data, dict):
        return data.get("rank", data.get("tokens", data.get("data", [])))
    if isinstance(data, list):
        return data
    return []


def enrich_token(token: dict, chain: str = "sol") -> dict:
    token_address = token.get("address", "")
    chain_name = GMGNClient.CHAINS.get(chain, chain)
    pair_info = token.get("pair", {})
    creation_timestamp = token.get("creation_timestamp")
    created_at = (
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(creation_timestamp))
        if creation_timestamp
        else None
    )
    coin_url = f"https://gmgn.ai/{chain}/token/{token_address}" if token_address else None

    return {
        "symbol": token.get("symbol"),
        "name": token.get("name"),
        "address": token_address,
        "price": token.get("price"),
        "price_change_percent": token.get("price_change_percent"),
        "volume": token.get("volume"),
        "liquidity": token.get("liquidity"),
        "market_cap": token.get("market_cap"),
        "chain": chain_name,
        "chain_code": chain,
        "dex": pair_info.get("dex") if pair_info else None,
        "pair_address": pair_info.get("address") if pair_info else None,
        "creation_timestamp": creation_timestamp,
        "creation_date": created_at,
        "created_at": created_at,
        "trend_intervals": token.get("trend_intervals", []),
        "signal_score": token.get("signal_score"),
        "best_rank": token.get("best_rank"),
        "url": coin_url,
        "coin_url": coin_url,
    }


def fetch_enriched_tokens(chain: str = "sol", limit: int = 100, client: GMGNClient | None = None) -> list[dict]:
    active_client = client or GMGNClient()

    tokens = active_client.get_top_trending_tokens(chain=chain, limit=limit)
    if not tokens:
        result = active_client.get_trending_tokens(chain=chain, time_range="1h", limit=limit)
        tokens = extract_tokens(result)
    if not tokens:
        return []
    return [enrich_token(token, chain=chain) for token in tokens]


def save_enriched_tokens(rows: list[dict], output_path: str | None = None) -> str:
    os.makedirs(RES_DATA_DIR, exist_ok=True)
    resolved_output_path = _build_output_path(output_path)
    return _write_json_atomic(rows, resolved_output_path)


def format_token(token: dict, chain: str = "sol") -> str:
    """Format token data for display"""
    symbol = token.get("symbol", "N/A")
    name = token.get("name", "N/A")
    price = token.get("price", "N/A")
    if isinstance(price, (int, float)):
        if price < 0.001:
            price_str = f"${price:.8f}"
        elif price < 1:
            price_str = f"${price:.6f}"
        else:
            price_str = f"${price:.4f}"
    else:
        price_str = str(price)
    
    price_change = token.get("price_change_percent", 0)
    volume = token.get("volume", 0)
    liquidity = token.get("liquidity", 0)
    market_cap = token.get("market_cap", 0)
    token_address = token.get("address", "")
    token_address_short = token_address[:12] + "..." if len(token_address) > 12 else token_address
    
    created_date = token.get("created_at") or token.get("creation_date") or "N/A"
    
    change_str = f"+{price_change:.2f}%" if price_change >= 0 else f"{price_change:.2f}%"
    change_color = "green" if price_change >= 0 else "red"
    
    chain_name = GMGNClient.CHAINS.get(chain, chain)
    pair_info = token.get("pair", {})
    dex = pair_info.get("dex", "N/A") if pair_info else "N/A"
    
    gmgn_url = token.get("coin_url") or token.get("url")
    if not gmgn_url:
        gmgn_url = f"https://gmgn.ai/{chain}/token/{token_address}" if token_address else "N/A"
    
    return (f"{symbol} ({name}) | {price_str} | {change_color}:{change_str} | "
            f"Vol: ${volume:,.0f} | Liq: ${liquidity:,.0f} | "
            f"MC: ${market_cap:,.0f} | Chain: {chain_name} | Dex: {dex} | "
            f"Created: {created_date} | {token_address_short} | {gmgn_url}")

def main():
    chain = "sol"
    
    os.makedirs(RES_DATA_DIR, exist_ok=True)
    
    print(f"Fetching top 100 trending tokens from GMGN.ai (Chain: {chain})...")
    print("=" * 100)

    enriched_tokens = fetch_enriched_tokens(chain=chain, limit=100)
    if enriched_tokens:
        print(f"\nFound {len(enriched_tokens)} tokens:\n")
        for i, token in enumerate(enriched_tokens[:100], 1):
            print(f"{i:3}. {format_token(token, chain)}")

        print("\n" + "=" * 100)
        print(f"Total: {len(enriched_tokens)} tokens")

        output_path = save_enriched_tokens(enriched_tokens)
        print(f"Saved to {output_path}")
    else:
        print("Failed to fetch tokens or no token data found in response")


if __name__ == "__main__":
    main()
