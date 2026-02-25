import socket

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex(('127.0.0.1', 8001))
    if result == 0:
        print("✅ Port 8001 is OPEN and accepting connections")
    else:
        print(f"❌ Port 8001 is CLOSED (error code: {result})")
    sock.close()
except Exception as e:
    print(f"❌ Error: {e}")
