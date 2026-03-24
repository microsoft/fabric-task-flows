# Deployment Gotchas — Operational Reference

> Item API capabilities and deployment methods are in `registry_loader.build_deploy_method_map()`. This file contains only hard-won operational learnings.

## Key Learnings (Do Not Repeat These Mistakes)

1. **API "create without definition = ✅" does NOT mean fabric-cicd skips content files.** fabric-cicd reads the local directory and may expect content files even when the API doesn't require them.

2. **Empty stubs with wrong structure cause errors.** Example: `{"entities": []}` for Reflex fails, but `[]` works. Always copy exact content from the sample repo.

3. **Some items need extra files not obvious from the API.** Eventstream needs `eventstreamProperties.json` (not in API docs), Environment needs `Setting/Sparkcompute.yml` (not in API docs).

4. **Some items work BETTER without content files.** KQLDashboard's content file causes a fabric-cicd parser crash — `.platform` only works fine.

5. **When adding a new item type: check the sample repo FIRST, then test deployment, then run `sync-item-types.py` to update the registry.**
