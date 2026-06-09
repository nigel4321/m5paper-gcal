# Copy this file to config.py and fill in your values.
# config.py is gitignored so your secrets are never committed.

# WiFi credentials
WIFI_SSID = ""
WIFI_PASSWORD = ""

# Google OAuth credentials (populated after running tools/get_token.py)
CLIENT_ID = ""
CLIENT_SECRET = ""
REFRESH_TOKEN = ""

# App settings
SLEEP_INTERVAL_MIN = 30         # minutes between refreshes when online
SLEEP_INTERVAL_WIFI_FAIL_MIN = 60  # shorter retry interval when WiFi fails
MAX_EVENTS = 5

# Weather location (Open-Meteo, no API key required)
WEATHER_LAT = 51.5074
WEATHER_LNG = -0.1278
