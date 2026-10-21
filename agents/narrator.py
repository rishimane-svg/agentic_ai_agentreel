"""Narrator for ScamShield: synthesize each spoken scene and audit timing.

Run from project root: python -m agents.narrator
Requires: edge-tts and ffprobe (from FFmpeg).
"""

import asyncio
import json
import shutil
import subprocess
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "outputs" / "script.json"
AUDIO_DIR = ROOT / "assets" / "audio"
REPORT_PATH = ROOT / "outputs" / "narration_report.json"
VOICE = "en-IN-NeerjaNeural"
RATE = "+0%"


def duration_seconds(path):
    """Measure real media duration using ffprobe, not word estimates."""
    command = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


async def render_scene(scene):
    """Generate scene narration and compare audio duration to slot length."""
    scene_id = int(scene["scene_id"])
    text = scene.get("voiceover", "").strip()
    slot = float(scene["end_s"]) - float(scene["start_s"])
    if slot <= 0:
        raise ValueError("Scene {} has invalid timing".format(scene_id))

    record = {
        "scene_id": scene_id,
        "start_s": scene["start_s"],
        "end_s": scene["end_s"],
        "slot_s": slot,
        "voiceover": text,
        "audio_file": None,
        "audio_duration_s": 0.0,
        "fits_slot": True,
    }
    if not text:
        return record

    destination = AUDIO_DIR / "scene_{:02d}.mp3".format(scene_id)
    await edge_tts.Communicate(text, voice=VOICE, rate=RATE).save(str(destination))
    length = duration_seconds(destination)
    record["audio_file"] = str(destination.relative_to(ROOT))
    record["audio_duration_s"] = round(length, 3)
    record["fits_slot"] = length <= slot - 0.15
    return record


async def run():
    if not SCRIPT_PATH.exists():
        raise FileNotFoundError("Missing outputs/script.json; run Scriptwriter first")
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe missing; install FFmpeg")
    data = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("script.json does not contain a scenes list")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    results = []
    for scene in scenes:
        record = await render_scene(scene)
        results.append(record)
        state = "OK" if record["fits_slot"] else "TOO LONG"
        print("Scene {:02d}: audio {:.2f}s / slot {:.2f}s — {}".format(
            record["scene_id"], record["audio_duration_s"], record["slot_s"], state
        ))

    report = {
        "voice": VOICE,
        "rate": RATE,
        "source_script": "outputs/script.json",
        "narrated_scenes": sum(bool(row["voiceover"]) for row in results),
        "all_clips_fit": all(row["fits_slot"] for row in results),
        "scenes": results,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Report saved:", REPORT_PATH)
    if not report["all_clips_fit"]:
        print("Some clips exceed their scene slots. Review before editing; do not silently truncate speech.")


if __name__ == "__main__":
    asyncio.run(run())
