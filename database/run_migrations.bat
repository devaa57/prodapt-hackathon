@echo off
REM ════════════════════════════════════════════════════════════════
REM run_migrations.bat — Execute all SQL migrations in order (Windows)
REM ════════════════════════════════════════════════════════════════
REM Usage:
REM   run_migrations.bat                   -- uses defaults
REM   set DB_NAME=mydb && run_migrations.bat
REM   run_migrations.bat --seed            -- include seed data
REM
REM Prerequisites:
REM   - PostgreSQL 15+ running locally
REM   - psql.exe available in PATH
REM   - pgvector extension installed
REM ════════════════════════════════════════════════════════════════

setlocal enabledelayedexpansion

REM ── Load .env if present ──
if exist "%~dp0..\.env" (
    for /f "usebackq tokens=1* delims==" %%i in ("%~dp0..\.env") do (
        set "line=%%i"
        if not "!line:~0,1!"=="#" (
            if not "%%j"=="" set "%%i=%%j"
        )
    )
) else if exist "%~dp0.env" (
    for /f "usebackq tokens=1* delims==" %%i in ("%~dp0.env") do (
        set "line=%%i"
        if not "!line:~0,1!"=="#" (
            if not "%%j"=="" set "%%i=%%j"
        )
    )
)

REM ── Configuration (override via environment variables) ──
if "%DB_HOST%"=="" set DB_HOST=localhost
if "%DB_PORT%"=="" set DB_PORT=5432
if "%DB_NAME%"=="" set DB_NAME=screening_db
if "%DB_USER%"=="" set DB_USER=postgres
if not "%DB_PASSWORD%"=="" (
    if "%PGPASSWORD%"=="" set PGPASSWORD=%DB_PASSWORD%
)

set MIGRATIONS_DIR=%~dp0migrations
set INCLUDE_SEED=false

REM Parse flags
for %%a in (%*) do (
    if "%%a"=="--seed" set INCLUDE_SEED=true
)

echo ══════════════════════════════════════════════════════════
echo   AI Candidate Screening — Database Migration Runner
echo ══════════════════════════════════════════════════════════
echo   Host : %DB_HOST%:%DB_PORT%
echo   DB   : %DB_NAME%
echo   User : %DB_USER%
echo   Seed : %INCLUDE_SEED%
echo ══════════════════════════════════════════════════════════
echo.

REM ── Create database if it doesn't exist ──
echo ^> Ensuring database '%DB_NAME%' exists...
psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -tc "SELECT 1 FROM pg_database WHERE datname = '%DB_NAME%'" | findstr "1" >nul 2>&1
if errorlevel 1 (
    psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -c "CREATE DATABASE %DB_NAME%;"
)
echo   Done.
echo.

REM ── Run migrations in order ──
set MIGRATIONS=001_extensions.sql 002_types.sql 003_core_tables.sql 004_candidate_resume_tables.sql 005_screening_tables.sql 006_verification_tables.sql 007_audit_log.sql 008_indexes.sql 009_rls_policies.sql

if "%INCLUDE_SEED%"=="true" (
    set MIGRATIONS=%MIGRATIONS% 010_seed_data.sql
)

for %%f in (%MIGRATIONS%) do (
    if exist "%MIGRATIONS_DIR%\%%f" (
        echo ^> Running %%f ...
        psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -v ON_ERROR_STOP=1 -f "%MIGRATIONS_DIR%\%%f"
        if errorlevel 1 (
            echo   FAILED on %%f — aborting.
            exit /b 1
        )
        echo   Applied %%f
    ) else (
        echo   %%f NOT FOUND — skipping
    )
)

echo.
echo ══════════════════════════════════════════════════════════
echo   All migrations applied successfully!
echo ══════════════════════════════════════════════════════════

endlocal
