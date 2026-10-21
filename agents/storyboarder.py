
"""Storyboarder: convert the approved script into a visual plan."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VISUAL_STYLES = {
    1: {
        "visual": "Illustrated student checking an internship message on a phone",
        "text": "Internship offer? Think first.",
    },
    2: {
        "visual": "Fictional internship offer interface showing upfront fees",
        "text": "RED FLAG: Upfront fees",
    },
    3: {
        "visual": "Abstract video call interface with warning symbols; no real faces",
        "text": "Digital arrest scam alert",
    },
    4: {
        "visual": "Student verifying a company's identity independently",
        "text": "VERIFY. NEVER SHARE OTPs.",
    },
    5: {
        "visual": "Clean graphic showing the official cybercrime portal and financial fraud helpline",
        "text": "cybercrime.gov.in | Financial fraud: 1930",
    },
    6: {
        "visual": "Confident student with a digital shield illustration",
        "text": "Stay safe. Stay smart.",
    },
    7: {
        "visual": "Minimal end card with reporting details and AI disclosure",
        "text": "Created with AI agents — LY Agentic AI Lab",
    },
}


def create_storyboard():
    """Create scene-by-scene visual instructions from script.json."""
    script_path = ROOT / "outputs/script.json"
    script = json.loads(script_path.read_text(encoding="utf-8"))

    scenes = script["scenes"]
    if len(scenes) != 7:
        raise ValueError("Expected seven scenes")

    storyboard = []

    for scene in scenes:
        scene_id = scene["scene_id"]
        style = VISUAL_STYLES[scene_id]

        shot = {
            "scene_id": scene_id,
            "start_s": scene["start_s"],
            "end_s": scene["end_s"],
            "duration_s": scene["end_s"] - scene["start_s"],
            "voiceover": scene["voiceover"],
            "visual_description": style["visual"],
            "on_screen_text": style["text"],
            "asset_type": "illustration_or_graphic",
            "animation": "gentle_zoom_or_fade",
            "fact_ids": scene["fact_ids"],
            "safety_notes": [
                "Use fictional illustrations, not real people's likenesses",
                "Do not present fictional scam examples as real incidents",
                "Do not invent statistics or reporting contacts",
            ],
        }

        if scene_id == 2:
            shot["on_screen_disclaimer"] = "Fictional scam example"

        if scene_id == 7:
            shot["disclosure_required"] = True

        storyboard.append(shot)

    if storyboard[0]["start_s"] != 0:
        raise ValueError("Storyboard must start at zero")

    if storyboard[-1]["end_s"] != script["duration_s"]:
        raise ValueError("Storyboard duration mismatch")

    result = {
        "title": script["title"],
        "duration_s": script["duration_s"],
        "format": "9:16",
        "resolution": "1080x1920",
        "style": "Modern illustrated cyber-safety awareness",
        "generation_mode": "rule_based_storyboard",
        "scenes": storyboard,
        "status": "draft_requires_visual_review",
    }

    output_path = ROOT / "outputs/storyboard.json"
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Storyboard saved: {output_path}")
    print(f"Scenes: {len(storyboard)}")
    print(f"Duration: {result['duration_s']} seconds")
    print("Mode: rule_based_storyboard")

    return result


if __name__ == "__main__":
    create_storyboard()
