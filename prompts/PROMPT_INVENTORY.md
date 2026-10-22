# Prompt provenance inventory

Generated from the **current local source files**; it does not certify these were the exact versions used for the approved reel.
The files contain source excerpts and interpolation placeholders, **not resolved prompts or API responses**.
No secret files were read. A generated prompt or changed code should not be described as an original historical prompt.

- `prompts/planner_current_source_excerpts.md` — 1 recognized source assignment(s), SHA-256 `a20376202563…`
- `prompts/researcher_current_source_excerpts.md` — 1 recognized source assignment(s), SHA-256 `7b67123933ff…`
- `prompts/scriptwriter_current_source_excerpts.md` — 0 recognized source assignment(s), SHA-256 `70a4ebb21ffa…`
- `prompts/storyboarder_current_source_excerpts.md` — 0 recognized source assignment(s), SHA-256 `83a145f7c7e3…`

## Manual check

Review API call sites and any dynamically built prompts; the AST extractor is intentionally conservative.
Do not claim these excerpts are complete templates or prompt versions without checking the actual code.
Where the written assignment requests versioned templates, save verified static templates separately and update agents to load them only after testing.

## Additional verified records

- `scriptwriter_v1.md` — Source-level prompt construction from
  `agents/scriptwriter.py`; not necessarily the exact historical
  request used for the approved reel.
- `storyboarder_rule_based.md` — Documents that Storyboarder uses
  deterministic Python logic without an LLM prompt.