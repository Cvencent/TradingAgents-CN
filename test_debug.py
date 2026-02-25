import socket

def send_http_request(host, port, path):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        
        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        sock.sendall(request.encode())
        
        response = b""
        while True:
            data = sock.recv(8192)
            if not data:
                break
            response += data
        
        sock.close()
        
        print(f"\n{'='*60}")
        print(f"GET {path}")
        print('='*60)
        
        header, body = response.decode('utf-8', errors='replace').split('\r\n\r\n', 1)
        print(f"Status: {header.split()[1]}")
        print(f"Full Response:")
        print(body)
    except Exception as e:
        print(f"Error: {e}")

# Test active model selection with more detail
send_http_request('127.0.0.1', 8001, '/api/config/model-selection/active')
