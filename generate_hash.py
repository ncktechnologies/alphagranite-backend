"""Generate password hash using the AuthService"""
from src.app.service.auth import AuthService

auth_service = AuthService()
password = "admin123@Daewi"

hashed = auth_service.get_password_hash(password)
print(f"Password: {password}")
print(f"Hash: {hashed}")
