"""ScamShield Scriptwriter Agent.

Uses Groq, then local Ollama Qwen for narration drafts; Python owns the JSON.
Falls back to an explicitly labelled local draft only if both fail.
Requires Python 3.9+ and the installed groq/python-dotenv packages.
"""

import json
import os
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
LOGS = ROOT / "logs"

# Fixed timeline means the model never has to calculate timestamps.
SCENES = [
    (0, 3, "Hook", [], "Phone showing an alarming internship message"),
    (3, 12, "Fake job offer", ["online_job_scam"], "Fictional job offer demanding a fee"),
    (12, 21, "Digital arrest scam", ["digital_arrest_intimidation"], "Illustrated threatening video call; no real faces"),
    (21, 31, "Protect yourself", ["credential_protection", "independent_verification"], "Student independently verifying a message"),
    (31, 40, "Report", ["official_reporting"], "Official reporting portal and financial fraud helpline"),
    (40, 44, "Closing message", [], "Simple confident cyber-safety slogan"),
    (44, 48, "End card", [], "AI disclosure and official cybercrime portal"),
]

# These lines are a *backup draft*, not an LLM-produced script.
BACKUP_LINES = [
    "An internship offer that sounds too good?",
    "Imagine a recruiter asking for a registration fee right away. Upfront fees and unrealistic promises can be warning signs of online job scams.",
    "Or imagine a caller claiming to be an officer, threatening you with digital arrest. Scammers can impersonate authorities and use intimidating video calls.",
    "Don't share passwords, OTPs, or banking details. Check suspicious claims using contact information you find independently, not details supplied by the caller.",
    "Report suspected cybercrime at cybercrime.gov.in. For financial cyber fraud, the reporting helpline is 1930.",
    "Stop. Check. Report. Stay safe online.",
]


def word_count(text):
    """Count approximate spoken words."""
    return len(text.split())


def parse_lines(content):
    """Extract six numbered narration lines, tolerating common LLM formatting."""
    if not content or not content.strip():
        raise ValueError("Empty narration response")
    text = content.strip()
    text = re.sub(r"```(?:text|markdown)?\s*|```", "", text, flags=re.I)
    # Accept 1. text, 1) text, **1.** text, Scene 1: text, etc.
    pattern = re.compile(
        r"^\s*(?:\*\*)?(?:scene\s*)?([1-6])\s*[.):\-]\s*(?:\*\*)?\s*(.*)$",
        flags=re.I,
    )
    found = {}
    current = None
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            current = int(match.group(1))
            if current in found:
                raise ValueError(f"Duplicate narration line {current}")
            found[current] = match.group(2).strip().strip('"')
        elif current is not None and line.strip():
            found[current] += " " + line.strip()
    if sorted(found) != list(range(1, 7)):
        raise ValueError("Could not extract six numbered narration lines")
    return [found[i].strip() for i in range(1, 7)]


def ollama_narration(prompt):
    """Use an available local Qwen 3B model through Ollama's HTTP API."""
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    explicit_model = os.getenv("OLLAMA_MODEL", "").strip()
    if explicit_model:
        model_name = explicit_model
    else:
        with urllib.request.urlopen(base + "/api/tags", timeout=3) as resp:
            data = json.load(resp)
        models = [m.get("name", "") for m in data.get("models", [])]
        candidates = [m for m in models if "qwen" in m.lower() and
                      ("3b" in m.lower() or ":3" in m.lower())]
        if not candidates:
            raise ValueError("No local Qwen 3B found; run 'ollama list' and set OLLAMA_MODEL")
        model_name = candidates[0]
    body = json.dumps({
        "model": model_name,
        "prompt": prompt + "\nRespond with the six numbered narration lines only.",
        "stream": False,
        "options": {"temperature": 0.2},
    }).encode("utf-8")
    request = urllib.request.Request(
        base + "/api/generate", data=body,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=120) as resp:
        result = json.load(resp)
    lines = parse_lines(result.get("response", ""))
    validate_lines(lines, minimum_words=55)
    if word_count(" ".join(lines)) < 75:
        # One targeted revision attempt; retain a sound short draft if it fails.
        revised_prompt = (
            "Expand these SIX numbered narration lines to 80–95 words TOTAL. "
            "Keep their numbers and topics in the same order. "
            "Add only practical explanations supported by the provided research; "
            "do not invent facts. Put both cybercrime.gov.in and 1930 (for "
            "financial cyber fraud) in line 5. Return ONLY lines 1. through 6.\n\n"
            + "\n".join(f"{i}. {line}" for i, line in enumerate(lines, 1))
        )
        revision_body = json.dumps({
            "model": model_name, "prompt": revised_prompt,
            "stream": False, "options": {"temperature": 0.1},
        }).encode("utf-8")
        revision_request = urllib.request.Request(
            base + "/api/generate", data=revision_body,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(revision_request, timeout=120) as resp:
                revised = parse_lines(json.load(resp).get("response", ""))
            validate_lines(revised, minimum_words=75)
            lines = revised
        except (ValueError, urllib.error.URLError, TimeoutError):
            pass  # Keep the valid original 55–74 word AI draft, flagged below.
    return lines, model_name


def validate_lines(lines, minimum_words=75):
    """Check basic narration size and required safety/reporting content."""
    if len(lines) != 6 or any(not line.strip() for line in lines):
        raise ValueError("Must have six nonempty narration lines")
    total = sum(word_count(line) for line in lines)
    if not minimum_words <= total <= 120:
        raise ValueError(f"Narration has {total} words (expected {minimum_words}–120)")
    narration = " ".join(lines).lower()
    required = {
        "job scam": ("job", "internship", "recruiter"),
        "digital arrest": ("digital arrest",),
        "identity check": ("verify", "check", "independent"),
        "reporting portal": ("cybercrime.gov.in",),
        "financial fraud helpline": ("1930",),
    }
    for label, alternatives in required.items():
        if not any(term in narration for term in alternatives):
            raise ValueError(f"Missing topic: {label}")
    if "1930" not in lines[4] or "cybercrime.gov.in" not in lines[4]:
        raise ValueError("Reporting channels must appear in scene 5")
    return total


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


def write_script():
    """Generate, validate and save a scene-structured narration draft."""
    load_dotenv(ROOT / ".env")
    plan = json.loads((OUTPUTS / "plan.json").read_text(encoding="utf-8"))
    research = json.loads((OUTPUTS / "facts.json").read_text(encoding="utf-8"))
    facts = research["facts"]
    fact_by_id = {item["fact_id"]: item for item in facts}
    if len(fact_by_id) != len(facts):
        raise ValueError("Duplicate fact IDs in facts.json")

    # The source-grounded fallback and any reporting text require these IDs.
    def pick_ids(topic):
        ids = [f["fact_id"] for f in facts if f.get("topic") == topic]
        if not ids:
            raise ValueError(f"Research is missing required topic: {topic}")
        return ids[:2]

    scene_fact_ids = [
        [],
        pick_ids("online_job_scam"),
        pick_ids("digital_arrest_intimidation"),
        pick_ids("credential_protection") + pick_ids("independent_verification"),
        pick_ids("official_reporting"),
        [],
        pick_ids("official_reporting"),
    ]
    # Guarantee that the reporting facts include both official channels.
    reporting_claims = " ".join(fact_by_id[i]["claim"].lower() for i in
                                [f["fact_id"] for f in facts if f.get("topic") == "official_reporting"])
    if "1930" not in reporting_claims or "portal" not in reporting_claims:
        raise ValueError("facts.json must support both 1930 and the reporting portal")

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    narration = None
    mode = "llm"
    errors = []
    prompt = make_prompt(plan, facts)
    usage = None

    if os.getenv("GROQ_API_KEY"):
        try:
            client = Groq(api_key=os.environ["GROQ_API_KEY"], timeout=30.0, max_retries=0)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                # No response_format: Python constructs and validates the JSON.
            )
            usage = response.usage
            narration = parse_lines(response.choices[0].message.content or "")
            validate_lines(narration, minimum_words=55)
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {str(exc)[:400]}")
    else:
        errors.append("GROQ_API_KEY not set")

    if narration is None:
        try:
            narration, model = ollama_narration(prompt)
            mode = "ollama_llm"
        except Exception as exc:
            errors.append(f"Ollama: {type(exc).__name__}: {str(exc)[:250]}")

    if narration is None:
        narration = BACKUP_LINES
        validate_lines(narration)
        mode = "local_fallback"

    scenes = []
    for idx, ((start, end, label, _topics, visual), ids) in enumerate(
        zip(SCENES, scene_fact_ids), start=1
    ):
        scenes.append({
            "scene_id": idx,
            "start_s": start,
            "end_s": end,
            "voiceover": narration[idx - 1] if idx <= 6 else "",
            "visual_intent": visual,
            "fact_ids": ids,
        })

    script = {
        "title": plan.get("title", "ScamShield: Think Before You Click"),
        "duration_s": 48,
        "scenes": scenes,
        "call_to_action": "Report cybercrime at cybercrime.gov.in; call 1930 for financial cyber fraud.",
        "word_count": validate_lines(narration, minimum_words=55 if mode != "local_fallback" else 75),
        "generation_mode": mode,
        "grounding_level": research.get("grounding_level", "unverified"),
        "qa_status": "draft_short_narration_requires_review" if word_count(" ".join(narration)) < 75 else "draft_requires_fact_and_audio_review",
        "notes": "Fact IDs identify intended evidence, not independently verified claim entailment.",
    }

    output = OUTPUTS / "script.json"
    output.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": "Scriptwriter",
        "model": model if mode in ("llm", "ollama_llm") else "local_template",
        "status": mode,
        "input_tokens": getattr(usage, "prompt_tokens", None),
        "output_tokens": getattr(usage, "completion_tokens", None),
        "word_count": script["word_count"],
        "errors": errors,
        "output_path": str(output),
    }
    with (LOGS / "run_log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(log, ensure_ascii=False) + "\n")

    print(f"Script saved: {output}")
    print(f"Generation mode: {mode}")
    if errors:
        print("Generation attempts: " + " | ".join(errors))
    print(f"Scenes: {len(scenes)}; words: {script['word_count']}; timeline: 0–48 seconds")
    if script["word_count"] < 75:
        print("WARNING: AI draft is short; extend narration or adjust pacing before video export")
    print("Status: DRAFT; review factual claims and actual spoken-audio timing before video export")
    return script


if __name__ == "__main__":
    write_script()
