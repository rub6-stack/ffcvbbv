import logging
import os

import requests

log = logging.getLogger(__name__)


def get_holder_count(chain_cfg, token_address: str) -> int | None:
    """Best-effort holder-aantal via een Etherscan-compatibele explorer-API.

    Let op: het tokenholdercount-endpoint vereist bij de meeste explorers
    (Etherscan, hyperevmscan, ...) een betaald Pro-abonnement. Zonder key,
    of zonder toegang, geven we gewoon None terug en laat de bot het
    holders-veld weg i.p.v. te crashen.
    """
    api_key = os.environ.get(chain_cfg.holder_api_key_env, "")
    if not api_key:
        return None

    params = {
        "module": "token",
        "action": "tokenholdercount",
        "contractaddress": token_address,
        "apikey": api_key,
    }
    if chain_cfg.holder_api_chainid is not None:
        params["chainid"] = chain_cfg.holder_api_chainid

    try:
        resp = requests.get(chain_cfg.holder_api_base, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "1":
            return int(data["result"])
        log.debug("Holder-aantal niet beschikbaar voor %s: %s", token_address, data.get("result"))
        return None
    except (requests.RequestException, ValueError, KeyError) as exc:
        log.debug("Holder-aantal opvragen mislukt voor %s: %s", token_address, exc)
        return None
