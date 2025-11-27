#!/usr/bin/env python3
"""
Complete automation script: migration + testing
"""

import subprocess
import sys
import os

def run_cmd(cmd, description):
    """Execute command and return success status"""
    print(f"\n{'='*60}")
    print(description)
    print('='*60)
    print(f"Running: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd='/Users/segun/Desktop/Protech/alpha_granit_backend')
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    success = result.returncode == 0
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'} (exit code: {result.returncode})")
    
    return success

def main():
    os.chdir('/Users/segun/Desktop/Protech/alpha_granit_backend')
    
    print("\n" + "="*60)
    print("COMPLETE WORKFLOW: MIGRATION + TESTING")
    print("="*60)
    
    # Step 1: Check current migration
    run_cmd(['alembic', 'current'], 'STEP 1: Checking current migration')
    
    # Step 2: Apply migration
    migration_ok = run_cmd(['alembic', 'upgrade', 'head'], 'STEP 2: Applying database migration')
    
    if not migration_ok:
        print("\n❌ Migration failed! Cannot proceed with testing.")
        return 1
    
    # Step 3: Run comprehensive tests
    test_ok = run_cmd(['python', 'verify_and_test.py'], 'STEP 3: Running verification and tests')
    
    if test_ok:
        print("\n" + "="*60)
        print("🎉 ALL STEPS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("✅ Migration applied")
        print("✅ Database schema verified")
        print("✅ Both endpoints tested and working")
        print("\nReady to commit and push to repository.")
        return 0
    else:
        print("\n" + "="*60)
        print("⚠️  TESTS FAILED")
        print("="*60)
        print("Migration was applied, but endpoint tests failed.")
        print("Check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
