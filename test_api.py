import requests

r = requests.get('http://localhost:8001/api/config/system', headers={'Authorization': 'Bearer test'})
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:1000]}")
