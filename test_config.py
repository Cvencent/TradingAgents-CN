import urllib.request
import json

try:
    req = urllib.request.Request(
        'http://localhost:8001/api/config/system',
        headers={'Authorization': 'Bearer test'}
    )
    response = urllib.request.urlopen(req, timeout=10)
    data = response.read().decode('utf-8')
    print("Status: 200 OK")
    print("Response preview:")
    print(data[:800])
except Exception as e:
    print(f"Error: {e}")
