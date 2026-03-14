---
id: api-selection
title: API Layer Selection
---

# API Layer Selection

> Match API approach to read/write patterns and custom logic needs.

## Comparison Table

| Criteria | GraphQL API | User Data Functions | Direct Connection |
|----------|------------|-------------------|-------------------|
| **Query Style** | Declarative — client specifies fields | Imperative — function defines logic | SQL from application |
| **Backend Code** | None — auto-generated | Python functions | Application-side DAL |
| **Schema** | Auto-generated from data sources | Manual (function signatures) | N/A (raw SQL) |
| **Read Pattern** | ✅ Selective field queries, nested relationships | ✅ Custom queries in function code | ✅ Full SQL |
| **Write Pattern** | Via mutations + stored procedures | ✅ Full — function writes to any source | ✅ Full SQL DML |
| **Custom Logic** | ❌ No — schema reflects data as-is | ✅ Full Python — validation, transformation, side effects | ❌ Application-side only |
| **Authentication** | Microsoft Entra ID | Microsoft Entra ID | SQL auth or Entra ID |
| **Supported Sources** | Warehouse, SQL Database, Lakehouse SQL, Mirrored DBs | Any (code accesses data directly) | SQL Database, Warehouse |
| **Schema Evolution** | Additive — new fields don't break clients | Function signature changes may break | Schema changes break queries |
| **Monitoring** | Built-in dashboard + request logging | Logs via Python logging module | Application-level |
| **Maturity** | GA | Preview | GA |

## Combining Approaches

| Pattern | Read Layer | Write Layer | Auth |
|---------|-----------|-------------|------|
| **GraphQL + UDF** | GraphQL API (selective reads) | User Data Functions (validation, side effects) | Entra ID |
| **GraphQL only** | GraphQL API | GraphQL mutations + stored procs | Entra ID |
| **Direct** | Application SQL | Application SQL DML | SQL / Entra ID |
