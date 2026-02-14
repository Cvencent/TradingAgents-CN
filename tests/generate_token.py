"""生成测试用的JWT token"""
import jwt
import time

# JWT配置 (使用.env文件中的配置)
JWT_SECRET = "23742378978934787578934798734892"
JWT_ALGORITHM = "HS256"

# 生成一个有效期为1小时的token (使用admin用户)
payload = {
    "sub": "admin",
    "exp": int(time.time()) + 3600  # 1小时有效期
}
token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
print(f"生成的Token (admin用户):\n{token}")
