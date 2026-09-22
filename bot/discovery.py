import logging
import time
from typing import Any

import requests

log = logging.getLogger(__name__)

BASE_URL = "https://api.geckoterminal.com/api/v2"


def _get(url: str, params: dict | None = None) -> dict | None:
    try:
        resp = requests.get(url, params=params, timeout=15, headers={"Accept": "application/json"})
        if resp.status_code == 429:
            log.warning("GeckoTerminal rate limit bereikt, wacht even")
            time.sleep(5)
            return None
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        log.warning("GeckoTerminal request mislukt: %s", exc)
        return None


def get_new_pools(gecko_network: str) -> list[dict[str, Any]]:
    """Haal de nieuwste pools op voor een netwerk, genormaliseerd naar simpele dicts."""
    data = _get(
        f"{BASE_URL}/networks/{gecko_network}/new_pools",
        params={"include": "base_token,quote_token", "page": 1},
    )
    if not data:
        return []

    tokens_by_id = {
        item["id"]: item.get("attributes", {})
        for item in data.get("included", [])
        if item.get("type") == "token"
    }

    pools = []
    for entry in data.get("data", []):
        pool = _normalize_pool(entry, tokens_by_id, gecko_network)
        if pool:
            pools.append(pool)
    return pools


def _to_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _normalize_pool(entry: dict, tokens_by_id: dict, gecko_network: str) -> dict[str, Any] | None:
    attrs = entry.get("attributes", {})
    rel = entry.get("relationships", {})
    base_token_ref = rel.get("base_token", {}).get("data", {})
    base_token = tokens_by_id.get(base_token_ref.get("id"))
    if not base_token:
        return None

    token_address = base_token.get("address")
    if not token_address:
        return None

    market_cap = _to_float(attrs.get("market_cap_usd"))
    if market_cap is None:
        market_cap = _to_float(attrs.get("fdv_usd"))

    volume = attrs.get("volume_usd", {}) or {}
    price_change = attrs.get("price_change_percentage", {}) or {}

    return {
        "chain": gecko_network,
        "token_address": token_address,
        "token_name": base_token.get("name"),
        "token_symbol": base_token.get("symbol"),
        "pool_address": attrs.get("address"),
        "pool_name": attrs.get("name"),
        "price_usd": _to_float(attrs.get("base_token_price_usd")),
        "market_cap_usd": market_cap,
        "liquidity_usd": _to_float(attrs.get("reserve_in_usd")),
        "volume_usd": {k: _to_float(v) for k, v in volume.items()},
        "price_change_pct": {k: _to_float(v) for k, v in price_change.items()},
        "txns": attrs.get("transactions", {}) or {},
        "pool_created_at": attrs.get("pool_created_at"),
        "geckoterminal_url": f"https://www.geckoterminal.com/{gecko_network}/pools/{attrs.get('address')}",
    }
