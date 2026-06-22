"""Constants for La Meteo Agricole."""

from datetime import timedelta

DOMAIN = "lameteoagricole"

CONF_URL = "url"

DEFAULT_NAME = "La Meteo Agricole"
DEFAULT_SCAN_INTERVAL = timedelta(minutes=60)

BASE_URL = "https://www.lameteoagricole.net/index.php?communehome={commune}"
USER_AGENT = (
    "Mozilla/5.0 (compatible; HomeAssistant-LaMeteoAgricole/0.1; "
    "+https://www.home-assistant.io/)"
)
