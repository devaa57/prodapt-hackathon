#!/bin/bash
# ════════════════════════════════════════════════════════════════
# run_migrations.sh — Execute all SQL migrations in order
# ════════════════════════════════════════════════════════════════
# Usage:
#   ./run_migrations.sh                    # uses defaults
#   DB_NAME=mydb DB_USER=myuser ./run_migrations.sh
#   ./run_migrations.sh --seed             # include seed data
#
# Prerequisites:
#   - PostgreSQL 15+ running locally
#   - psql CLI available in PATH
#   - pgvector extension installed
# ════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Load .env if present ──
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$ROOT_DIR/.env"
    set +a
elif [ -f "$(dirname "$0")/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$(dirname "$0")/.env"
    set +a
fi

# ── Configuration (override via environment variables) ──
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-screening_db}"
DB_USER="${DB_USER:-postgres}"
if [ -n "${DB_PASSWORD:-}" ] && [ -z "${PGPASSWORD:-}" ]; then
    export PGPASSWORD="$DB_PASSWORD"
fi

MIGRATIONS_DIR="$(cd "$(dirname "$0")" && pwd)/migrations"
INCLUDE_SEED=false

# Parse flags
for arg in "$@"; do
    case $arg in
        --seed) INCLUDE_SEED=true ;;
        *)      echo "Unknown option: $arg"; exit 1 ;;
    esac
done

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  AI Candidate Screening — Database Migration Runner     ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Host : $DB_HOST:$DB_PORT"
echo "║  DB   : $DB_NAME"
echo "║  User : $DB_USER"
echo "║  Seed : $INCLUDE_SEED"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Create database if it doesn't exist ──
echo "→ Ensuring database '$DB_NAME' exists..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tc \
    "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 \
    || psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"

echo "  ✓ Database ready"
echo ""

# ── Run migrations in order ──
MIGRATION_FILES=(
    "001_extensions.sql"
    "002_types.sql"
    "003_core_tables.sql"
    "004_candidate_resume_tables.sql"
    "005_screening_tables.sql"
    "006_verification_tables.sql"
    "007_audit_log.sql"
    "008_indexes.sql"
    "009_rls_policies.sql"
)

# Optionally include seed data
if [ "$INCLUDE_SEED" = true ]; then
    MIGRATION_FILES+=("010_seed_data.sql")
fi

for file in "${MIGRATION_FILES[@]}"; do
    filepath="$MIGRATIONS_DIR/$file"
    if [ -f "$filepath" ]; then
        echo "→ Running $file ..."
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            -v ON_ERROR_STOP=1 -f "$filepath"
        echo "  ✓ $file applied"
    else
        echo "  ✗ $file NOT FOUND — skipping"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  All migrations applied successfully!"
echo "════════════════════════════════════════════════════════════"
