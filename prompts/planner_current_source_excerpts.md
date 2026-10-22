# planner: prompt-related source excerpts

- Source: `agents/planner.py`
- Source SHA-256: `a20376202563aef0fac38bf805055ea048f762e0b8356e2500855d110ed47ef0`
- Provenance: current working tree at generation time; historical version not established.

## Excerpt 1 — source line 19

```python
    prompt = (
        "You are a planning agent for a student cyber-safety awareness reel. "
        "Return ONLY a JSON object with keys: title (string), audience (string), "
        "duration_s (integer), objectives (list of strings), "
        "stages (list of objects with agent and task string fields), "
        "safety_checks (list of strings). "
        "Include Researcher, Scriptwriter, Storyboarder, Asset Generator, Editor, "
        "and Critic stages. Do not invent statistics, helplines, or policies. "
        "Never treat fictional scenarios as real cases. Keep duration_s equal "
        "to the provided brief. Provide planning only, not a completed script.\n\n"
        f"BRIEF:\n{yaml.safe_dump(brief, sort_keys=False)}"
    )
```
