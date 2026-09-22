import logging
import time

from . import config, dexscreener, discovery, holders, state, telegram

log = logging.getLogger(__name__)


def _fmt_usd(value) -> str:
    if value is None:
        return "n.v.t."
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.2f}"


def _fmt_pct(value) -> str:
    return "n.v.t." if value is None else f"{value:+.1f}%"


def _build_message(chain_cfg, pool: dict, pair: dict | None, holder_count, threshold: config.Threshold) -> str:
    symbol = pool["token_symbol"] or "?"
    name = pool["token_name"] or symbol
    address = pool["token_address"]

    liquidity = pool.get("liquidity_usd")
    volume = pool.get("volume_usd", {})
    price_change = pool.get("price_change_pct", {})
    price = pool.get("price_usd")
    mc = pool.get("market_cap_usd")

    link = (pair or {}).get("url") or pool.get("geckoterminal_url")
    explorer = chain_cfg.explorer_token_url.format(address=address)

    mc_threshold = threshold.market_cap_usd
    header = (
        "🔥 *50K MC BREAKOUT*"
        if mc_threshold >= 50_000
        else f"🚀 *Nieuwe coin > {mc_threshold // 1000}K MC*"
    )
    price_line = f"💵 Prijs: ${price:.8f}" if price else "💵 Prijs: n.v.t."

    lines = [
        header,
        f"*{name}* (`{symbol}`) — {chain_cfg.display_name}",
        f"`{address}`",
        "",
        f"💰 Market cap: *{_fmt_usd(mc)}*  (drempel: {_fmt_usd(mc_threshold)})",
        f"💧 Liquidity: {_fmt_usd(liquidity)}",
        f"📊 Volume 24u: {_fmt_usd(volume.get('h24'))} (min. vereist: {_fmt_usd(threshold.min_volume_24h_usd)}) · 1u: {_fmt_usd(volume.get('h1'))} · 5m: {_fmt_usd(volume.get('m5'))}",
        f"📈 Prijsverandering 24u: {_fmt_pct(price_change.get('h24'))} · 1u: {_fmt_pct(price_change.get('h1'))}",
        price_line,
        f"👥 Holders: {holder_count if holder_count is not None else 'n.v.t.'}",
        "",
        f"[Chart bekijken]({link}) · [Explorer]({explorer})",
    ]
    return "\n".join(lines)


def _scan_chain(chain_key: str, bot_state: dict) -> None:
    chain_cfg = config.CHAINS[chain_key]
    pools = discovery.get_new_pools(chain_cfg.gecko_network)
    log.info("[%s] %d nieuwe pools opgehaald", chain_cfg.display_name, len(pools))

    for pool in pools:
        mc = pool.get("market_cap_usd")
        liquidity = pool.get("liquidity_usd") or 0
        volume_24h = (pool.get("volume_usd") or {}).get("h24") or 0
        if mc is None or liquidity < config.MIN_LIQUIDITY_USD:
            continue

        key = f"{chain_key}:{pool['token_address'].lower()}"
        entry = bot_state.setdefault(key, {"alerted": [], "first_seen": time.time()})

        for threshold in config.THRESHOLDS:
            already_alerted = threshold.market_cap_usd in entry["alerted"]
            if already_alerted or mc < threshold.market_cap_usd or volume_24h < threshold.min_volume_24h_usd:
                continue

            pairs = dexscreener.get_token_pairs(chain_cfg.dexscreener_chain, pool["token_address"])
            pair = dexscreener.best_pair(pairs)
            holder_count = holders.get_holder_count(chain_cfg, pool["token_address"])

            message = _build_message(chain_cfg, pool, pair, holder_count, threshold)
            if telegram.send_message(message):
                entry["alerted"].append(threshold.market_cap_usd)
                log.info(
                    "Alert verstuurd: %s (%s) @ mc>=%s vol24u>=%s",
                    pool["token_symbol"], key, threshold.market_cap_usd, threshold.min_volume_24h_usd,
                )


def run_forever() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log.info(
        "Scanner gestart | chains=%s | thresholds=%s | interval=%ss",
        config.SCAN_CHAINS,
        [(t.market_cap_usd, t.min_volume_24h_usd) for t in config.THRESHOLDS],
        config.POLL_INTERVAL_SECONDS,
    )
    bot_state = state.load()

    while True:
        for chain_key in config.SCAN_CHAINS:
            try:
                _scan_chain(chain_key, bot_state)
            except Exception:
                log.exception("Fout tijdens scannen van %s", chain_key)
        bot_state = state.prune(bot_state)
        state.save(bot_state)
        time.sleep(config.POLL_INTERVAL_SECONDS)
