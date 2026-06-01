import sys
from unittest.mock import MagicMock

# Stub out MicroPython/M5Stack device modules so tests run on host Python
for mod in ["M5", "machine", "network", "requests", "utility"]:
    sys.modules[mod] = MagicMock()
