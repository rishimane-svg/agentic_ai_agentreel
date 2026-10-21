# ScamShield — Option B Second Cut

This package modifies only the approved seven-scene 48-second pipeline. It does **not** replace your Planner, Researcher, Scriptwriter, Narrator or factual sources.

## Files
- `polish_second_cut.py` — run once from project root. Saves backups of the previous script and storyboard, then edits narration and visual briefs.
- `asset_generator.py` — place in `agents/`, replacing the old generator. Creates distinct, fictional mockup graphics instead of slide placeholders.
- `editor.py` — place in `agents/`, replacing the old editor. Exports `scamshield_second_cut.mp4` without overwriting the first cut.

## Run order

From `~/Desktop/scamshield_phase1`:

```bash
python polish_second_cut.py
python -m agents.asset_generator
python -m agents.narrator
```

**Stop here and inspect `outputs/narration_report.json`.** Only proceed when *every scene* says `OK`. The revised narration has not been tested against your Edge-TTS voice, and may require shortening. Do not crop audio or ignore timing warnings.

Then:

```bash
python -m agents.editor
```

The new outputs are `outputs/scamshield_second_cut.mp4` and `.srt`. The first-cut MP4 and SRT remain untouched.

**Do not rerun `agents.scriptwriter` or `agents.storyboarder` after applying the polish:** those programs may overwrite the manually revised `script.json` or `storyboard.json`.

## Academic transparency
- The new script is **human-edited from an LLM draft**, not a fresh AI-generated script.
- The storyboard and visuals are **rule-based/Pillow-generated**, not generative-image AI outputs.
- Record the content intervention in `logs/interventions.md` and explain it honestly in the viva.
- The facts are still labeled `local_source_notes`: check every government link and final wording before submission.
- Scene 2 intentionally uses **fictional** salary/fee amounts, not a real incident.
- The institutional handout requires an AI disclosure line: it is included on scene 7.
