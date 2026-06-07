# ADR 0003: Static API key authentication

**Status:** Accepted
**Date:** 2025-06-07

## Context

The API must be protected to prevent unauthorized use of the Gemini quota and to control who can upload/delete documents. Options considered:

- **Per-user API keys in database**: requires a user table, key hashing, management endpoints. Adds significant complexity.
- **OAuth2 / JWT**: appropriate for multi-tenant SaaS, significant implementation overhead.
- **Static API key from environment**: one shared secret, validated on every request via `X-API-Key` header. No database required.

## Decision

A single static API key loaded from the `API_KEY` environment variable. All protected endpoints require a matching `X-API-Key` header. No user concept, no key rotation mechanism in-app.

## Consequences

**Good:**
- Zero auth infrastructure. Key rotation is done by updating the environment variable and redeploying.
- Simple to explain and demonstrate to employers.
- Impossible to misconfigure (no JWT signing keys, no OAuth redirect URIs).

**Bad:**
- All callers share one key; revoking access means changing the key for everyone.
- No per-caller rate limiting or audit log by identity.
- Not suitable for a public multi-tenant product without replacing this mechanism.

**Neutral:**
- Upgrading to per-user keys later requires adding a `keys` table and a key-management router; the auth middleware `require_api_key` would be the only touchpoint.
