"""Generate password hash using bcrypt directly"""
import bcrypt

password = "admin123@Daewi"

# Truncate to 72 bytes for bcrypt compatibility
password_bytes = password.encode('utf-8')
if len(password_bytes) > 72:
    password_bytes = password_bytes[:72]

# Generate hash
hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

print(f"Password: {password}")
print(f"Hash: {hashed.decode('utf-8')}")
