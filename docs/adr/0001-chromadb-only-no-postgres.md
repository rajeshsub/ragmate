# ADR 0001: ChromaDB as sole data store (no PostgreSQL)

**Status:** Accepted
**Date:** 2025-06-07

## Context

The original design considered PostgreSQL for document metadata (title, filename, upload date, chunk count) alongside ChromaDB for vectors. This would require Docker Compose, SQLAlchemy, Alembic, and ongoing schema migrations.

## Decision

Use ChromaDB exclusively: both for chunk vectors and for document metadata stored in a separate `document_meta` collection. No PostgreSQL, no SQLAlchemy, no Alembic, no Docker.

## Consequences

**Good:**
- Zero infrastructure. `pip install` and run. No Docker required to develop or demo.
- Single dependency for persistence simplifies the mental model.
- Trivially portable: the entire data store is a directory on disk.

**Bad:**
- No relational queries or joins across documents.
- ChromaDB metadata filtering is less expressive than SQL WHERE clauses.
- Migrating to PostgreSQL later requires an explicit data migration step.

**Neutral:**
- ChromaDB's metadata store is not designed for arbitrary structured queries; acceptable because ragmate's query surface is narrow (list all, get by ID, delete by ID).
