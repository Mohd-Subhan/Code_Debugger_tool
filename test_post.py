import requests
import json
import sys

BASE = "http://127.0.0.1:5000"

def health():
    try:
        r = requests.get(f"{BASE}/health", timeout=5)
        print('HEALTH STATUS:', r.status_code, r.text)
    except Exception as e:
        print('HEALTH ERROR:', str(e))

def debug_post():
    url = f"{BASE}/debug"
    payload = {
        "code": "print('hello from test')",
        "language": "python",
        "user_input": ""
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        print('STATUS:', r.status_code)
        try:
            print('JSON:', r.json())
        except Exception:
            print('TEXT:', r.text)
    except Exception as e:
        print('ERROR:', str(e))

if __name__ == '__main__':
    health()
    debug_post()
    sys.exit(0)
