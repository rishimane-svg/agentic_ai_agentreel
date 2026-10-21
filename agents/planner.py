"""Planner agent: turns a video brief into a structured production plan."""
import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from groq import Groq

ROOT = Path(__file__).resolve().parents[1]


def create_plan(brief_path: Path) -> dict:
    """Call the Groq LLM, validate a minimal schema, and save its plan."""
    load_dotenv(ROOT / ".env")
    brief = yaml.safe_load(brief_path.read_text(encoding="utf-8"))
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
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
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    expected = {"title", "audience", "duration_s", "objectives", "stages", "safety_checks"}
    missing = expected - set(result)
    if missing:
        raise ValueError(f"Planner missing required fields: {sorted(missing)}")
    if int(result["duration_s"]) != int(brief["duration_s"]):
        raise ValueError("Planner changed the requested video duration")
    if not isinstance(result["stages"], list) or not isinstance(result["objectives"], list):
        raise ValueError("Planner returned malformed lists")
    out = ROOT / "outputs" / "plan.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    usage = response.usage
    print(f"Planner output: {out}")
    if usage:
        print(f"Tokens: input={usage.prompt_tokens}, output={usage.completion_tokens}")
    return result


if __name__ == "__main__":
    create_plan(ROOT / "briefs" / "a05.yaml")
