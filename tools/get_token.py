"""One-time desktop OAuth helper for the M5Paper calendar display.

Runs Google's OAuth 2.0 device flow (for "TV and Limited Input" clients) and
prints a refresh token. Copy that token into src/config.py on the device.

Prerequisites:
  1. Create a Google Cloud project and enable the Calendar API.
  2. Create OAuth credentials of type "TVs and Limited Input devices".
  3. Run this script and follow the on-screen instructions.

Usage:
  CLIENT_ID=... CLIENT_SECRET=... python3 tools/get_token.py

Uses only the Python standard library — no pip install required.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"


def _post(url, params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    if not client_id or not client_secret:
        sys.exit("Set CLIENT_ID and CLIENT_SECRET environment variables first.")

    status, dc = _post(DEVICE_CODE_URL, {"client_id": client_id, "scope": SCOPE})
    if status != 200:
        sys.exit("Failed to start device flow: {}".format(dc))

    print("\n1. Visit: {}".format(dc["verification_url"]))
    print("2. Enter code: {}\n".format(dc["user_code"]))
    print("Waiting for authorisation...")

    interval = dc.get("interval", 5)
    while True:
        time.sleep(interval)
        status, tok = _post(
            TOKEN_URL,
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "device_code": dc["device_code"],
                "grant_type": GRANT_TYPE,
            },
        )
        if status == 200:
            print("\nSuccess. Add this to src/config.py:\n")
            print('REFRESH_TOKEN = "{}"'.format(tok["refresh_token"]))
            return
        error = tok.get("error")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval += 5
            continue
        sys.exit("Authorisation failed: {}".format(tok))


if __name__ == "__main__":
    main()
