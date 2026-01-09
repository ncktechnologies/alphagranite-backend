#!/bin/bash

# Navigate to project directory
cd /root/alphagranite/alpha-granit

echo "============================================================"
echo "STEP 1: Checking current Alembic migration status"
echo "============================================================"
alembic current

echo ""
echo "============================================================"
echo "STEP 2: Applying database migration"
echo "============================================================"
alembic upgrade head

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration applied successfully!"
    echo ""
    echo "============================================================"
    echo "STEP 3: Running comprehensive verification and tests"
    echo "============================================================"
    /opt/homebrew/bin/python3 verify_and_test.py
else
    echo ""
    echo "❌ Migration failed! Please check the errors above."
    exit 1
fi
