#!/usr/bin/env python3
"""Run migration and test endpoints"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a shell command and print output"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:", result.stderr)
    
    print(f"Exit code: {result.returncode}")
    
    return result.returncode == 0

def main():
    os.chdir('/Users/segun/Desktop/Protech/alpha_granit_backend')
    
    # Step 1: Check current migration
    print("\n" + "="*60)
    print("STEP 1: Check current Alembic migration")
    print("="*60)
    run_command(['alembic', 'current'], 'Current migration state')
    
    # Step 2: Show pending migrations
    print("\n" + "="*60)
    print("STEP 2: Check pending migrations")
    print("="*60)
    run_command(['alembic', 'heads'], 'Available migration heads')
    
    # Step 3: Apply migration
    success = run_command(['alembic', 'upgrade', 'head'], 'STEP 3: Applying database migration')
    
    if not success:
        print("\n❌ Migration failed! Check the errors above.")
        return 1
    
    print("\n✅ Migration applied successfully!")
    
    # Step 4: Run tests
    print("\n" + "="*60)
    print("STEP 4: Running endpoint tests")
    print("="*60)
    
    test_result = subprocess.run([sys.executable, 'test_both_endpoints.py'])
    
    return test_result.returncode

if __name__ == "__main__":
    sys.exit(main())
