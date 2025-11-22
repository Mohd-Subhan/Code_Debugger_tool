import requests
url = 'http://127.0.0.1:5500/static/index.html'
try:
    r = requests.get(url, timeout=5)
    print('STATUS', r.status_code)
    print('LENGTH', len(r.content))
    print('SNIPPET:', r.text[:200])
except Exception as e:
    print('ERROR', e)
