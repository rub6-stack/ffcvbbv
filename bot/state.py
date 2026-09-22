import json
import logging
import time
from pathlib import Path

from . import config

log = logging.getLogger(__name__)


def load() -> dict:
    path = Path(config.STATE_FILE)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("Kon state-bestand niet lezen (%s), start met lege state", exc)
        return {}


def save(bot_state: dict) -> None:
    Path(config.STATE_FILE).write_text(json.dumps(bot_state, indent=2))


def prune(bot_state: dict) -> dict:
    cutoff = time.time() - config.STATE_MAX_AGE_DAYS * 86400
    return {k: v for k, v in bot_state.items() if v.get("first_seen", time.time()) >= cutoff}
