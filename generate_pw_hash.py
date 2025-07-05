import sys, getpass, bcrypt, secrets, base64

pwd = sys.argv[1] if len(sys.argv) > 1 else getpass.getpass("Password: ")
pwd_hash = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

secret = secrets.token_bytes(32)
jwt_secret = base64.urlsafe_b64encode(secret).decode().rstrip("=")

print(f"PASSWORD_HASH: {pwd_hash}")
print(f"JWT_SECRET: {jwt_secret}")