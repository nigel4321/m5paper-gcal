import sys
from unittest.mock import MagicMock

# Stub out MicroPython/M5Stack device modules so tests run on host Python
for mod in ["M5", "machine", "network", "urequests", "utility"]:
    sys.modules[mod] = MagicMock()
