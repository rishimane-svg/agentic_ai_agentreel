
"""Researcher Agent: extract source-grounded facts for the reel."""
""" source-grounded Researcher prototype. """
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

ROOT = Path(__file__).resolve().parents[1]


def load_sources() -> dict:
    """Read source sections, keeping fictional examples separate."""
    path = ROOT / "data/sources/cyber_safety_notes.md"
    text = path.read_text(encoding="utf-8")

    sources = {}
    for section in re.split(r"(?=^## )", text, flags=re.MULTILINE):
        match = re.match(r"## Source (S\d+):", section)
        if not match:
            continue

        source_id = match.group(1)
        url_match = re.search(r"^URL:\s*(\S+)", section, re.MULTILINE)

        if not url_match:
            raise ValueError(f"Missing URL for {source_id}")

        sources[source_id] = {
            "url": url_match.group(1),
            "text": section.strip(),
        }

    if not sources:
        raise ValueError("No source sections found")

    return sources


def research() -> dict:
    """Extract facts from local sources using Groq."""
    load_dotenv(ROOT / ".env")

    plan_path = ROOT / "outputs/plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    sources = load_sources()

    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

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

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    if not isinstance(result.get("facts"), list):
        raise ValueError("Researcher did not return a facts list")

    validated = []
    rejected = []

    for fact in result["facts"]:
        if not isinstance(fact, dict):
            rejected.append({"fact": fact, "reason": "Invalid object"})
            continue

        source_id = fact.get("source_id", "")
        evidence = fact.get("evidence", "")
        claim = fact.get("claim", "")
        topic = fact.get("topic", "")

        if (
            source_id not in sources
            or not isinstance(evidence, str)
            or not evidence.strip()
            or evidence not in sources[source_id]["text"]
            or not isinstance(claim, str)
            or not claim.strip()
            or not isinstance(topic, str)
        ):
            rejected.append({
                "fact": fact,
                "reason": "Missing fields, unknown source, or unmatched evidence"
            })
            continue

        validated.append({
            "fact_id": f"F{len(validated) + 1:03d}",
            "claim": claim,
            "source_id": source_id,
            "source_url": sources[source_id]["url"],
            "evidence": evidence,
            "topic": topic,
            "verification_status": "matched_to_local_notes"
        })

    if not validated:
        raise ValueError("No facts passed evidence validation")

    output = {
        "topic": plan["title"],
        "grounding_level": "local_source_notes",
        "facts": validated,
        "rejected_count": len(rejected),
        "rejected": rejected
    }

    out_path = ROOT / "outputs/facts.json"
    out_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    usage = response.usage
    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "Researcher",
        "model": model,
        "input_tokens": usage.prompt_tokens if usage else None,
        "output_tokens": usage.completion_tokens if usage else None,
        "validated_facts": len(validated),
        "rejected_facts": len(rejected),
        "output": str(out_path),
    }

    log_path = ROOT / "logs/run_log.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log) + "\n")

    print(f"Researcher output: {out_path}")
    print(f"Accepted facts: {len(validated)}")
    print(f"Rejected facts: {len(rejected)}")
    print("Grounding: local source notes (official-source review pending)")

    return output


if __name__ == "__main__":
    research()
