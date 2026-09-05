-- Migration 001: Enable Required Extensions
-- ============================================
-- All extensions used are free and open-source.
--
-- pgvector  : Vector similarity search (embeddings)
-- pgcrypto  : UUID generation via gen_random_uuid()
--             (Built into PostgreSQL 13+, but pgcrypto is a safe fallback)

BEGIN;

CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

COMMIT;
