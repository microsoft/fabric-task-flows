# Validation Report Template

Use this template when producing the Validation Report in Mode 2, Step 6.

```
## Validation Report

**Project:** [name]
**Task flow:** [name]
**Date:** [timestamp]
**Status:** ✅ PASSED | ⚠️ PARTIAL | ❌ FAILED

### Phase Results

| Phase | Status | Notes |
|-------|--------|-------|
| Foundation | ✅/⚠️/❌ | [details] |
| Environment | ✅/⚠️/❌ | [details] |
| Ingestion | ✅/⚠️/❌ | [details] |
| Transformation | ✅/⚠️/❌ | [details] |
| Visualization | ✅/⚠️/❌ | [details] |
| CI/CD Readiness | ✅/⚠️/❌/N/A | [parameterization, capacity pools, connections] |

### Items Validated

- [x] Item 1 - verified
- [x] Item 2 - verified
- [ ] Item 3 - ISSUE: [description]

### Manual Steps Verification

- [x] Step 1 - confirmed
- [ ] Step 2 - NOT COMPLETED: [action needed]

### Issues Found

| Severity | Item | Issue | Recommended Action |
|----------|------|-------|-------------------|
| High/Med/Low | [item] | [description] | [fix] |

### Next Steps

1. [Action items for issues found]
2. [Re-validation triggers]

### Validation Context
[Explain what successful validation means for this specific architecture - tie back to original requirements and acceptance criteria]

### Future Considerations
[Operational learnings discovered during validation - scaling concerns, monitoring gaps, improvement opportunities]
```

> **HARD REQUIREMENT:** The `Validation Context` and `Future Considerations` sections are MANDATORY. The `/fabric-document` agent requires this information to complete the project documentation and capture lessons learned.
