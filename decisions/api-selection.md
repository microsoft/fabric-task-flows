---
id: api-selection
title: API Layer Selection
description: Choose how to expose Fabric data to applications — GraphQL, serverless functions, or direct connections
triggers:
  - "GraphQL vs REST"
  - "how to expose data to apps"
  - "API for Fabric data"
  - "application integration"
  - "frontend access to Fabric"
options:
  - id: graphql-api
    label: GraphQL API
    criteria:
      query_style: declarative (client specifies fields)
      schema_generation: automatic from data sources
      backend_code: none required
      best_for: ["data-driven apps", "mobile/web frontends", "selective field queries"]
      supported_sources: ["Warehouse", "SQL Database", "Lakehouse SQL endpoint", "Mirrored Databases"]
      write_support: mutations (via stored procedures)
  - id: user-data-functions
    label: User Data Functions (REST)
    criteria:
      query_style: imperative (function defines logic)
      schema_generation: manual (Python function signature)
      backend_code: Python functions with @udf.function()
      best_for: ["custom business logic", "data transformation", "writeback", "event-driven actions"]
      supported_sources: ["any — function code accesses data directly"]
      write_support: full (function can write to any source)
  - id: direct-connection
    label: Direct Database Connection
    criteria:
      query_style: SQL queries from application
      schema_generation: N/A
      backend_code: application-side data access layer
      best_for: ["internal tools", "existing SQL applications", "simple CRUD"]
      supported_sources: ["SQL Database", "Warehouse", "Lakehouse SQL endpoint"]
      write_support: full (SQL DML)
quick_decision: |
  Flexible read queries → GraphQL API
  Custom business logic/writes → User Data Functions
  Simple CRUD from internal tools → Direct Connection
  Both reads AND logic → GraphQL API + User Data Functions
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
