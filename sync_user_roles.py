"""
Script to synchronize user_roles table with users table
This ensures all users with role_id have corresponding entries in user_roles table
"""
import asyncio
from sqlalchemy import select
from src.app.database.user import User
from src.app.database.role import Role
from src.app.database.department import Department
from src.app.database.user_role import UserRole
from src.app.database.job import JobApplication
from src.app.utils.config import SessionLocal
from datetime import datetime


async def sync_user_roles():
    """Sync user_roles table with users table"""
    
    async with SessionLocal() as db:
        print("=" * 60)
        print("Synchronizing user_roles table")
        print("=" * 60)
        
        # Get all users with role_id
        result = await db.execute(
            select(User).where(User.role_id.isnot(None))
        )
        users_with_roles = result.scalars().all()
        
        print(f"\nFound {len(users_with_roles)} users with role_id assigned")
        
        synced = 0
        already_exists = 0
        skipped = 0
        
        for user in users_with_roles:
            # Skip if role_id is 0 or doesn't exist in roles table
            if user.role_id == 0:
                print(f"⚠ Skipping user {user.username} (ID: {user.id}) - invalid role_id: {user.role_id}")
                skipped += 1
                continue
            
            # Verify role exists
            role_result = await db.execute(select(Role).where(Role.id == user.role_id))
            role = role_result.scalars().first()
            if not role:
                print(f"⚠ Skipping user {user.username} (ID: {user.id}) - role {user.role_id} does not exist")
                skipped += 1
                continue
            
            # Check if UserRole entry already exists
            ur_result = await db.execute(
                select(UserRole).where(
                    UserRole.user_id == user.id,
                    UserRole.role_id == user.role_id
                )
            )
            existing_ur = ur_result.scalars().first()
            
            if existing_ur:
                print(f"✓ User {user.username} (ID: {user.id}) already has UserRole for role {user.role_id}")
                already_exists += 1
            else:
                # Create UserRole entry
                new_user_role = UserRole(
                    user_id=user.id,
                    role_id=user.role_id,
                    created_at=datetime.now()
                )
                db.add(new_user_role)
                print(f"+ Created UserRole for {user.username} (ID: {user.id}) -> role {user.role_id}")
                synced += 1
        
        # Commit all changes
        await db.commit()
        
        print("\n" + "=" * 60)
        print(f"Synchronization Complete!")
        print(f"- Already in sync: {already_exists}")
        print(f"- Newly synced: {synced}")
        print(f"- Skipped (invalid role): {skipped}")
        print("=" * 60)
        
        # Verify the sync by checking user_roles count
        count_result = await db.execute(select(UserRole))
        all_user_roles = count_result.scalars().all()
        print(f"\nTotal entries in user_roles table: {len(all_user_roles)}")
        
        # Show breakdown by role
        print("\nBreakdown by role:")
        role_counts = {}
        for ur in all_user_roles:
            role_counts[ur.role_id] = role_counts.get(ur.role_id, 0) + 1
        
        for role_id, count in sorted(role_counts.items()):
            print(f"  Role {role_id}: {count} member(s)")


if __name__ == "__main__":
    print("\nStarting user_roles synchronization...\n")
    asyncio.run(sync_user_roles())
    print("\nSync completed.\n")
