import requests, json, sys

r = requests.post('http://localhost:8000/api/auth/login', json={'username':'admin','password':'admin123'})
token = r.json()['data']['access_token']
r2 = requests.get('http://localhost:8000/api/analysis/tasks/007bc602-771d-4b02-8d57-40d8dace38c2/status', headers={'Authorization':f'Bearer {token}'})

data = r2.json()
err = data.get("data", {}).get("error_message", "")
if err:
    with open('D:/trade/TradingAgents-CN/error_msg.txt', 'w', encoding='utf-8') as f:
        f.write(err)
    print("Error saved to error_msg.txt")
else:
    print("No error message")
