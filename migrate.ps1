# Alembic migration script for Windows PowerShell
# Only runs migration for updated or newly created tables

Write-Host "Running Alembic migrations..."

# Check for new or updated migration scripts
$pending = alembic history --verbose | Select-String "(head)"
if ($pending) {
    alembic upgrade head
    Write-Host "Migrations applied."
} else {
    Write-Host "No new migrations to apply."
}
