# Onboarding output contract

Output documentation in `zh-TW`. Include source revision and timestamp in every package. Each code claim must be traced to a source path and exact 1-based lines. If source is inaccessible, write UNKNOWN and give an explicit question.

## 06-evidence-register.json

```json
{
  "schema_version": "1.0",
  "repository": {"root": "<local repo path>", "revision": "<git sha or UNKNOWN>"},
  "claims": [
    {"id":"C001", "statement":"<grounded claim>", "status":"CONFIRMED", "sources":[{"path":"src/foo.ext", "line_start":12, "line_end":34}], "notes":""}
  ],
  "open_questions": ["<specific missing evidence>"]
}
```

Use `CONFIRMED` only for direct code/config/schema evidence; `INFERRED` for architecture interpretation requiring assumptions; `UNKNOWN` for evidence gaps; `CONTRADICTED` for conflicting code/doc evidence. Validate file paths and ranges in the current repository before asserting confirmation. Do not put secret values or customer data in registers.

## Newcomer checklist

1. Can a new engineer explain the system's business goal in under 60 seconds?
2. Can they identify the main entrypoint and data storage location?
3. Can they trace one full example including failure handling?
4. Can they identify which module/file to modify for a requested rule change?
5. Can they state the test strategy and one safe hands-on exercise?
6. Can they distinguish verified behavior from unresolved questions?
