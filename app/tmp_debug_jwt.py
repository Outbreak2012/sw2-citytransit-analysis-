import os, base64, sys
from jose import jwt

# Token generated from backend login
token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbkBjaXR5dHJhbnNpdC5jb20iLCJpYXQiOjE3NjI4MTE5NDIsImV4cCI6MTc2Mjg5ODM0Mn0.ENJOSQXnHFQez1JjVShVHYvDoxUwlCimPzDDsNA9b28"
secret = os.environ.get('JWT_SECRET', '')

# Try base64 decode, otherwise use as-is
try:
    s = base64.b64decode(secret).decode('utf-8')
except Exception:
    s = secret

print('JWT_SECRET_env_len=', len(secret))
print('using_secret_len=', len(s))

try:
    payload = jwt.decode(token, s, algorithms=['HS256'])
    print('OK', payload)
except Exception as e:
    print('ERR', type(e), str(e))
    sys.exit(1)
