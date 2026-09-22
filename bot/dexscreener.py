import logging
from typing import Any

import requests

log = logging.getLogger(__name__)

BASE_URL = "https://api.dexscreener.com"


def get_token_pairs(dexscreener_chain: str, token_address: str) -> list[dict[str, Any]]:
    """Haal alle DexScreener-pairs op voor een tokenadres op een gegeven chain."""
    try:
        resp = requests.get(
            f"{BASE_URL}/tokens/v1/{dexscreener_chain}/{token_address}",
            timeout=15,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []
    except requests.RequestException as exc:
        log.warning("DexScreener request mislukt voor %s: %s", token_address, exc)
        return []


def best_pair(pairs: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Kies het pair met de meeste liquiditeit (meest representatief)."""
    if not pairs:
        return None
    return max(pairs, key=lambda p: (p.get("liquidity") or {}).get("usd") or 0)
