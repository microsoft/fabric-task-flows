---
id: api-selection
title: API Layer Selection
---

# API Layer Selection

> Choose how to expose Microsoft Fabric data to external applications, services, and frontends.

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

The most powerful pattern combines GraphQL for reads and User Data Functions for writes:

```
┌─────────────┐      ┌─────────────┐
│  Frontend   │─────►│ GraphQL API │──► SQL Database (reads)
│  (React,    │      └─────────────┘
│   Mobile)   │
│             │      ┌─────────────┐
│             │─────►│ User Data   │──► SQL Database (writes)
│             │      │ Functions   │──► External APIs
└─────────────┘      └─────────────┘
```

- **GraphQL** handles all read queries with selective field selection and relationship traversal
- **User Data Functions** handle writes, validation, and side effects via REST endpoints
- Both use Microsoft Entra ID for authentication
