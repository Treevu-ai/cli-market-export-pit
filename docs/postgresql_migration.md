# PostgreSQL Migration Guide

## Overview
This document describes the migration path from SQLite (current) to PostgreSQL for production deployments.

## Rationale
- Better concurrency for multi-worker deployments
- Native JSONB support for normalized payloads
- Stronger referential integrity
- Better performance for large evidence sets

## Schema Mapping
| SQLite | PostgreSQL |
|---|---|
| `TEXT PRIMARY KEY` | `TEXT PRIMARY KEY` |
| `TEXT NOT NULL` | `TEXT NOT NULL` |
| `INTEGER` | `INTEGER` |
| `REAL` | `REAL` |
| `JSON` (stored as text) | `JSONB` |
| `DATETIME` (ISO string) | `TIMESTAMPTZ` |

## Migration Steps
1. Export data from SQLite using `sqlite3 .dump`
2. Transform schema to PostgreSQL dialect
3. Create tables with `IF NOT EXISTS`
4. Load data with `COPY` or `INSERT`
5. Update connection string in `ResearchStore`

## Connection String
```
postgresql://user:pass@host:5432/pit
```

## Rollback
- Keep SQLite backup until PostgreSQL is validated
- Maintain `ResearchStore` abstraction for easy swap-back
