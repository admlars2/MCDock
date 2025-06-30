import sys, getpass, bcrypt

pwd = sys.argv[1] if len(sys.argv) > 1 else getpass.getpass("Password: ")
print(bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode())