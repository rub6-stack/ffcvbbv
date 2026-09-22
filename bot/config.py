import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ChainConfig:
    key: str
    display_name: str
    gecko_network: str
    dexscreener_chain: str
    explorer_token_url: str
    # Etherscan-compatible "holder count" API for this chain (best-effort,
    # usually needs a paid plan - see bot/holders.py).
    holder_api_base: str
    holder_api_key_env: str
    # Etherscan's unified v2 API takes a numeric chainid; classic
    # Etherscan-fork explorers (e.g. hyperevmscan.io) don't use this param.
    holder_api_chainid: int | None = None


CHAINS: dict[str, ChainConfig] = {
    "eth": ChainConfig(
        key="eth",
        display_name="Ethereum",
        gecko_network="eth",
        dexscreener_chain="ethereum",
        explorer_token_url="https://etherscan.io/token/{address}",
        holder_api_base="https://api.etherscan.io/v2/api",
        holder_api_key_env="ETHERSCAN_API_KEY",
        holder_api_chainid=1,
    ),
    "bsc": ChainConfig(
        key="bsc",
        display_name="BNB Chain",
        gecko_network="bsc",
        dexscreener_chain="bsc",
        explorer_token_url="https://bscscan.com/token/{address}",
        holder_api_base="https://api.etherscan.io/v2/api",
        holder_api_key_env="ETHERSCAN_API_KEY",
        holder_api_chainid=56,
    ),
    "hyperevm": ChainConfig(
        key="hyperevm",
        display_name="HyperEVM",
        gecko_network="hyperevm",
        dexscreener_chain="hyperevm",
        explorer_token_url="https://hyperevmscan.io/token/{address}",
        holder_api_base="https://api.hyperevmscan.io/api",
        holder_api_key_env="HYPEREVMSCAN_API_KEY",
        holder_api_chainid=None,
    ),
}


def _parse_chains(raw: str) -> list[str]:
    keys = [c.strip().lower() for c in raw.split(",") if c.strip()]
    unknown = [k for k in keys if k not in CHAINS]
    if unknown:
        raise ValueError(
            f"Onbekende chain(s) in SCAN_CHAINS: {unknown}. Beschikbaar: {list(CHAINS)}"
        )
    return keys or list(CHAINS)


def _parse_thresholds(raw: str) -> list[int]:
    values = {int(t.strip()) for t in raw.split(",") if t.strip()}
    return sorted(values) or [10_000, 50_000]


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

SCAN_CHAINS = _parse_chains(os.environ.get("SCAN_CHAINS", "hyperevm"))
MC_THRESHOLDS = _parse_thresholds(os.environ.get("MC_THRESHOLDS", "10000,50000"))
MIN_LIQUIDITY_USD = float(os.environ.get("MIN_LIQUIDITY_USD", "1000"))
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
STATE_FILE = os.environ.get("STATE_FILE", "state.json")
STATE_MAX_AGE_DAYS = int(os.environ.get("STATE_MAX_AGE_DAYS", "14"))
