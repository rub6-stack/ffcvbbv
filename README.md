# EVM Coin Scanner → Telegram

Bot die nieuwe EVM-tokens (standaard alleen **HyperEVM**, optioneel ook
Ethereum/BNB Chain) scant en een
Telegram-alert stuurt zodra de marketcap boven de ingestelde drempels komt
(standaard **$10K** en **$50K**). Elke alert bevat marketcap, liquidity,
volume, prijsverandering, holders (optioneel) en links naar de chart en de
block explorer.

## Hoe het werkt

1. **Ontdekking** — [GeckoTerminal](https://www.geckoterminal.com/) se
   `new_pools`-endpoint levert per chain de nieuwst aangemaakte liquidity
   pools (gratis, geen API key nodig).
2. **Verrijking** — voor elke coin die een drempel passeert wordt extra data
   opgehaald bij [DexScreener](https://dexscreener.com/) (chart-link,
   actuele volumes/prijzen).
3. **Holders** — optioneel via een Etherscan-compatibele explorer-API per
   chain (`HYPEREVMSCAN_API_KEY` voor HyperEVM, `ETHERSCAN_API_KEY` voor
   Ethereum/BNB Chain). Let op: het `tokenholdercount`-endpoint vereist bij
   deze explorers meestal een **betaald Pro-abonnement**. Zonder (werkende)
   key laat de bot het holders-veld gewoon leeg i.p.v. te crashen.
4. **State** — welke coin al op welke drempel is gealarmeerd wordt lokaal
   bijgehouden in `state.json`, zodat je niet dubbel wordt gespamd.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Vul in `.env` minimaal in:

- `TELEGRAM_BOT_TOKEN` — jouw bot-token van @BotFather
- `TELEGRAM_CHAT_ID` — chat/group ID waar de alerts naartoe moeten

Optioneel:

- `ETHERSCAN_API_KEY` — voor holder-aantallen (zie hierboven)
- `SCAN_CHAINS` — comma-separated uit `hyperevm`, `eth`, `bsc` (standaard alleen `hyperevm`)
- `MC_THRESHOLDS` — comma-separated marketcap-drempels in USD (standaard `10000,50000`)
- `MIN_LIQUIDITY_USD` — negeer pools met minder liquidity (ruis/scam-filter)
- `POLL_INTERVAL_SECONDS` — scan-interval (standaard 60s)

## Draaien

```bash
python3 main.py
```

Dit draait een oneindige loop (scan → sleep → scan → ...) en logt naar
stdout. Voor 24/7 gebruik op een server/VPS, houd hem in leven met bv.:

**systemd** (`/etc/systemd/system/coin-scanner.service`):

```ini
[Unit]
Description=EVM Coin Scanner
After=network.target

[Service]
WorkingDirectory=/pad/naar/ffcvbbv
ExecStart=/pad/naar/ffcvbbv/venv/bin/python main.py
Restart=always
EnvironmentFile=/pad/naar/ffcvbbv/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now coin-scanner
```

**of pm2**:

```bash
pm2 start main.py --interpreter venv/bin/python --name coin-scanner
```

**of Railway** (aanbevolen als je niet zelf een server wilt beheren):

1. Ga naar [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → kies `rub6-stack/ffcvbbv`.
2. Railway herkent automatisch dat het een Python-project is (via `railway.json`/`Procfile` in deze repo) en start `python3 main.py` als worker-service. Je hoeft geen webserver/poort te configureren — dit is een achtergrondproces, geen website.
3. Ga naar het project → tabblad **Variables** en voeg toe:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - eventueel `ETHERSCAN_API_KEY`, `SCAN_CHAINS`, `MC_THRESHOLDS`, etc. (zie `.env.example`)
4. Railway deployt automatisch en houdt het proces 24/7 draaiend (met auto-restart bij een crash, zie `railway.json`).
5. Bij elke nieuwe push naar deze branch/main redeployt Railway automatisch.

Let op: `state.json` wordt lokaal op de container opgeslagen. Bij een redeploy op Railway kan dit bestand resetten, waardoor je mogelijk opnieuw een alert krijgt voor coins die eerder al gealarmeerd waren. Voor puur eigen gebruik is dat prima; wil je dit robuuster (bv. state in een database), laat het weten.

## Beperkingen om te weten

- **Marketcap van gloednieuwe tokens** is vaak (nog) niet bekend als "echte"
  marketcap; in dat geval valt de bot terug op de FDV (fully diluted
  valuation), wat de gangbare aanpak is bij DexScreener/GeckoTerminal voor
  net gelanceerde coins.
- **Holders** vereist een betaalde explorer-API; zonder key wordt dit veld
  overgeslagen. Wil je dit gratis benaderen, dan moet je zelf on-chain
  `Transfer`-events indexeren (aanzienlijk meer werk) — laat het weten als
  je dat wilt laten bouwen.
- **Nieuwe pools ≠ garantie op kwaliteit.** Dit is puur een data-scanner,
  geen koop-/verkoopadvies en geen bescherming tegen honeypots/rugpulls.
  `MIN_LIQUIDITY_USD` filtert wel de grofste ruis eruit.
- Publieke API's van GeckoTerminal/DexScreener hebben rate limits; zet
  `POLL_INTERVAL_SECONDS` niet te laag als je veel chains/tokens volgt.
