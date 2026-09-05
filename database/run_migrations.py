#!/usr/bin/env python3
"""
run_migrations.py — PostgreSQL & pgvector Migration Runner (Python)
===================================================================
Executes all SQL migration files in sequence against PostgreSQL/Neon.
Works on Windows, macOS, and Linux without requiring 'psql' CLI.

Usage:
    python run_migrations.py
    python run_migrations.py --seed
    python run_migrations.py --status
"""

import os
import sys
import argparse
from pathlib import Path

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Error: 'psycopg2' is required to run migrations.")
    print("Run: pip install psycopg2-binary")
    sys.exit(1)


def load_env():
    """Load key-value pairs from .env if present."""
    base_dir = Path(__file__).resolve().parent
    env_paths = [base_dir.parent / ".env", base_dir / ".env"]
    for path in env_paths:
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip()
                        # Do not override existing env vars
                        if k not in os.environ:
                            os.environ[k] = v
            break


def get_connection():
    """Establish connection using DATABASE_URL or individual DB_* params."""
    load_env()
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "screening_db")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    sslmode = os.getenv("PGSSLMODE", "prefer")

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode=sslmode,
    )


def check_status():
    """Check database connection and existing tables."""
    print("Connecting to database...")
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"Connected: {version}\n")

        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]
        print(f"Existing tables ({len(tables)}):")
        for t in tables:
            print(f"  - {t}")

        cur.execute("SELECT 1 FROM pg_available_extensions WHERE name = 'vector';")
        has_vector = bool(cur.fetchone())
        print(f"\npgvector extension available: {has_vector}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error checking status: {e}")
        sys.exit(1)


def run_migrations(include_seed=False):
    """Execute SQL migrations in numerical order."""
    migrations_dir = Path(__file__).resolve().parent / "migrations"
    migration_files = [
        "001_extensions.sql",
        "002_types.sql",
        "003_core_tables.sql",
        "004_candidate_resume_tables.sql",
        "005_screening_tables.sql",
        "006_verification_tables.sql",
        "007_audit_log.sql",
        "008_indexes.sql",
        "009_rls_policies.sql",
    ]

    if include_seed:
        migration_files.append("010_seed_data.sql")

    print("=" * 60)
    print("  AI Candidate Screening — Database Migration Runner")
    print("=" * 60)
    print(f"Targeting: {os.getenv('DB_HOST', 'configured DATABASE_URL')}")
    print(f"Include Seed Data: {include_seed}\n")

    conn = get_connection()
    conn.autocommit = True  # Each migration file manages its own transactions or statement blocks

    for filename in migration_files:
        filepath = migrations_dir / filename
        if not filepath.is_file():
            print(f"Warning: {filename} not found, skipping.")
            continue

        print(f"-> Running {filename}...")
        with open(filepath, "r", encoding="utf-8") as f:
            sql_content = f.read()

        try:
            cur = conn.cursor()
            cur.execute(sql_content)
            cur.close()
            print(f"   [DONE] {filename}")
        except Exception as e:
            print(f"   [FAILED] {filename}: {e}")
            conn.close()
            sys.exit(1)

    conn.close()
    print("\n" + "=" * 60)
    print("  All migrations executed successfully!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Run SQL database migrations.")
    parser.add_argument("--seed", action="store_true", help="Include seed sample data (010_seed_data.sql)")
    parser.add_argument("--status", action="store_true", help="Check database connection and list tables")
    args = parser.parse_args()

    if args.status:
        check_status()
    else:
        run_migrations(include_seed=args.seed)


if __name__ == "__main__":
    main()
