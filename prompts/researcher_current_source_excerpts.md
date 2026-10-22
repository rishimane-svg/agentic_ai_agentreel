# researcher: prompt-related source excerpts

- Source: `agents/researcher.py`
- Source SHA-256: `7b67123933ff7cf1f33441902e38701ac3ff43697c20035459811a2f9f75534b`
- Provenance: current working tree at generation time; historical version not established.

## Excerpt 1 — source line 55

```python
    prompt = f"""
You are the Researcher Agent for a cyber-safety awareness video.

Research objectives:
{json.dumps(plan["objectives"], indent=2)}

AVAILABLE SOURCE NOTES:
{json.dumps(sources, indent=2)}

TASK:
Extract 6 to 10 useful factual claims supported by these notes.

Ensure the facts collectively cover:
1. Online job or internship scam warning signs
2. Digital arrest intimidation
3. Independent verification and credential protection
4. Official cybercrime reporting

Do not invent facts to satisfy topic coverage.
If a topic lacks supporting evidence, report that gap.

Return a JSON object with a "facts" array.
Each fact must have:
- claim: a short factual statement
- source_id: S001, S002,S003 or S004
- evidence: an EXACT continuous quotation from that source's notes
- topic: short category name

Rules:
- Use only the provided source notes.
- Do not invent statistics, contacts, quotations or URLs.
- Do not treat synthetic scenarios as verified incidents.
- Do not imply you independently browsed or verified websites.
- If insufficient evidence exists, return fewer facts.
- Return JSON only.
"""
```
