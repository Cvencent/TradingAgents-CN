
import socket
import psutil

def check_port(port):
    """检查端口占用情况"""
    print(f"检查端口 {port} 占用情况:")
    
    # 方法1: 使用socket尝试连接
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        result = s.connect_ex(('127.0.0.1', port))
        if result == 0:
            print(f"端口 {port} 被占用 (socket检查)")
        else:
            print(f"端口 {port} 可用 (socket检查)")
    except Exception as e:
        print(f"socket检查异常: {e}")
    s.close()
    
    # 方法2: 使用psutil检查进程
    print("\n使用psutil检查:")
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            print(f"端口 {port} 被进程 {conn.pid} 占用")
            try:
                process = psutil.Process(conn.pid)
                print(f"  进程名: {process.name()}")
                print(f"  命令行: {process.cmdline()}")
            except Exception as e:
                print(f"  无法获取进程信息: {e}")

check_port(8000)
check_port(8001)
