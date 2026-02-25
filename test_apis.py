import socket

def send_http_request(host, port, path):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        sock.sendall(request.encode())
        
        response = b""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data
        
        sock.close()
        
        print(f"\n{'='*60}")
        print(f"GET {path}")
        print('='*60)
        
        header, body = response.decode('utf-8', errors='replace').split('\r\n\r\n', 1)
        print(f"Status: {header.split()[1]}")
        print(f"Response: {body[:500]}")
    except Exception as e:
        print(f"Error: {e}")

# Test health
send_http_request('127.0.0.1', 8001, '/api/health')

# Test role model configs (正确的路径)
send_http_request('127.0.0.1', 8001, '/api/config/role-models')

# Test model presets (正确的路径)
send_http_request('127.0.0.1', 8001, '/api/config/model-presets')

# Test analysis models
send_http_request('127.0.0.1', 8001, '/api/config/model-selection/analysis-models')

# Test active model selection
send_http_request('127.0.0.1', 8001, '/api/config/model-selection/active')
