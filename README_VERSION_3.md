# ScamShield Version 3 — installation

This package includes:
- `polish_third_cut.py` (put in the project root)
- `asset_generator.py` (replace `agents/asset_generator.py`)
- `editor.py` (replace `agents/editor.py`)

It preserves your first-cut and second-cut videos. The revised third cut is 59 seconds and has 7 scenes.

## Run from the activated venv in `scamshield_phase1`:

1. `python polish_third_cut.py`
2. `python -m agents.asset_generator`
3. `python -m agents.narrator`
4. **Review the audio report.** If any clip is TOO LONG, do not export. Shorten only that scene's `voiceover` in `outputs/script.json`, run Narrator again, and then synchronize the corresponding `voiceover` in `outputs/storyboard.json` (do not rerun the polishing script).
5. Only once all narrated scenes are OK: `python -m agents.editor`

Expected output files: `outputs/scamshield_third_cut.mp4` and `outputs/scamshield_third_cut.srt`.

## Important
- Do **not** rerun `agents.scriptwriter` or `agents.storyboarder` after applying Version 3: they may overwrite your reviewed content.
- The script is a **human-reviewed revision of an LLM-assisted draft**, not a fresh LLM generation. The visuals are **programmatically drawn mockups**, not text-to-image AI pictures. Record these interventions honestly.
- All amounts and conversations displayed in the fictional scam mockups are illustrative.
- Fact IDs are references to your local source notes. Independently confirm the final claims against the official source documents before submission.
- The four-second end card contains the assignment disclosure. Review the final screen, captions, music licensing (if added), loudness and export size.
- The scripts were tested using representative JSON files and generated all seven visuals; live Edge-TTS and FFmpeg full export must run on your Mac.
