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
        
        print("Response:")
        print(response.decode('utf-8', errors='replace')[:500])
    except Exception as e:
        print(f"Error: {e}")

send_http_request('127.0.0.1', 8001, '/api/health')
