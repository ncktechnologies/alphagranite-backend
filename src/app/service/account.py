from datetime import datetime
from sqlalchemy.orm import Session
from src.app.database.user import User
from src.app.utils.constants import MAX_LOGIN_ATTEMPTS

class AccountService:
    @staticmethod
    def increment_failed_login(db: Session, user: User) -> User:
        """
        Increment failed login attempts and lock account if threshold reached
        """
        # Increment the counter
        user.failed_login_attempts += 1
        
        # Check if account needs to be locked
        if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.is_locked = True
            user.locked_at = datetime.utcnow()
        
        # Persist changes
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def reset_failed_login(db: Session, user: User) -> User:
        """
        Reset failed login attempts counter on successful login
        """
        user.failed_login_attempts = 0
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def unlock_account(db: Session, user: User) -> User:
        """
        Unlock a locked account
        """
        user.is_locked = False
        user.failed_login_attempts = 0
        user.locked_at = None
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user