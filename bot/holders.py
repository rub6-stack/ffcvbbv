import logging

import requests

from . import config

log = logging.getLogger(__name__)

BASE_URL = "https://api.etherscan.io/v2/api"


def get_holder_count(etherscan_chainid: int, token_address: str) -> int | None:
    """Best-effort holder-aantal via Etherscan's unified multichain API.

    Let op: het tokenholdercount-endpoint vereist doorgaans een betaald
    Etherscan/BscScan Pro-abonnement. Zonder key, of zonder toegang, geven we
    gewoon None terug en laat de bot het holders-veld weg i.p.v. te crashen.
    """
    if not config.ETHERSCAN_API_KEY:
        return None
    try:
        resp = requests.get(
            BASE_URL,
            params={
                "chainid": etherscan_chainid,
                "module": "token",
                "action": "tokenholdercount",
                "contractaddress": token_address,
                "apikey": config.ETHERSCAN_API_KEY,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "1":
            return int(data["result"])
        log.debug("Holder-aantal niet beschikbaar voor %s: %s", token_address, data.get("result"))
        return None
    except (requests.RequestException, ValueError, KeyError) as exc:
        log.debug("Holder-aantal opvragen mislukt voor %s: %s", token_address, exc)
        return None
