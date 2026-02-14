import urllib.request
import json

try:
    req = urllib.request.Request(
        'http://localhost:8001/api/config/system',
        headers={'Authorization': 'Bearer test'}
    )
    response = urllib.request.urlopen(req, timeout=10)
    data = response.read().decode('utf-8')
    print("Status:", response.status)
    print("Response preview (first 500 chars):")
    print(data[:500])
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(f"Response: {e.read().decode('utf-8')[:500]}")
except Exception as e:
    print(f"Error: {e}")
