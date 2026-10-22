# Scriptwriter Prompt — v1

**Source:** `agents/scriptwriter.py`, function `make_prompt()`.

**Status:** Current source template, not an exact historical API request.

**Inputs:** Planner audience and validated Researcher facts.

**Output:** Six numbered narration lines.

**Note:** The final approved reel contains later human-reviewed revisions.

## Prompt construction

```python
def make_prompt(plan, facts):
    """Keep the model's task limited to the words spoken on screen."""
    return (
        "You are drafting the narration of a 48-second STUDENT CYBER-SAFETY awareness reel.\n"
        "Write EXACTLY SIX numbered lines, like '1. ...' through '6. ...'.\n"
        "NO JSON, NO headings, NO Markdown, NO extra lines.\n"
        "Total: 85–100 spoken words. Keep the lines short enough for their durations:\n"
        "1: 3 seconds — short hook about an internship offer.\n"
        "2: 9 seconds — a FICTIONAL suspicious upfront-fee job offer.\n"
        "3: 9 seconds — a FICTIONAL digital-arrest threat.\n"
        "4: 10 seconds — never share OTPs/passwords; independently verify.\n"
        "5: 9 seconds — EXACTLY name cybercrime.gov.in and 1930 for FINANCIAL cyber fraud.\n"
        "6: 4 seconds — brief reassuring closing slogan.\n"
        "Only use the supplied facts; no statistics, unverified contacts, or invented policies.\n"
        "Fictional examples must not be described as actual incidents.\n"
        "Use a calm, practical voice. No detailed scam instructions.\n"
        f"AUDIENCE: {plan.get('audience', 'college students')}\n"
        "SUPPORTED FACTS (not independent website verification):\n"
        + "\n".join(f"{f['fact_id']}: {f['claim']}" for f in facts)
    )
```
