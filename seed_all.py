"""
Script to run database migration and all seed scripts
This ensures the database is properly set up with all reference data
"""
import sys
import subprocess
from pathlib import Path


def run_command(command: str, description: str, step: int, total_steps: int) -> bool:
    """
    Run a command and handle errors
    
    Args:
        command: Command to run
        description: Description of what the command does
        step: Current step number
        total_steps: Total number of steps
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"📋 Step {step}/{total_steps}: {description}")
    print(f"{'='*60}")
    print(f"Running: {command}")
    print()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=False
        )
        print(f"\n✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error in step {step}: {description}")
        print(f"Command failed with exit code: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error in step {step}: {str(e)}")
        return False


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("  Alpha Granite Database Migration & Seeding")
    print("="*60)
    print()
    
    # Define all steps
    steps = [
        ("alembic upgrade head", "Running database migration", 1, 11),
        ("python scripts/create_missing_tables.py", "Creating missing tables", 2, 11),
        ("python scripts/load_default_status.py", "Loading default status values", 3, 11),
        ("python scripts/load_default_action_menu.py", "Loading default action menu", 4, 11),
        ("python scripts/load_default_departments.py", "Loading default departments", 5, 11),
        ("python scripts/load_default_roles.py", "Loading default roles", 6, 11),
        ("python scripts/seed_accounts.py", "Seeding accounts", 7, 11),
        ("python scripts/seed_stone_colors.py", "Seeding stone colors", 8, 11),
        ("python scripts/seed_stone_types.py", "Seeding stone types", 9, 11),
        ("python scripts/seed_stone_thickness.py", "Seeding stone thickness", 10, 11),
        ("python scripts/seed_edges.py", "Seeding edges", 11, 11),
    ]
    
    # Run all steps
    for command, description, step, total in steps:
        success = run_command(command, description, step, total)
        if not success:
            print(f"\n❌ Seeding process stopped at step {step}")
            print("Please fix the error and try again.")
            sys.exit(1)
    
    # Final success message
    print("\n" + "="*60)
    print("  ✅ ALL OPERATIONS COMPLETED SUCCESSFULLY!")
    print("="*60)
    print()
    print("Database is now fully migrated and seeded with:")
    print("  • Status values")
    print("  • Action menu items")
    print("  • Default departments")
    print("  • Default roles")
    print("  • Accounts (~237 records)")
    print("  • Stone colors (~1600 records)")
    print("  • Stone types")
    print("  • Stone thickness options")
    print("  • Edge profiles")
    print()
    print("You can now start the application!")
    print()


if __name__ == "__main__":
    main()
