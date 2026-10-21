# ScamShield Version 3 — Layout Fix

This patch fixes two visual problems without changing the approved narration, script, voice files or timeline:

- Scene 4: `SUSPICIOUS` and `VERIFY` are centered in their own comparison panels.
- All narrated scenes: captions occupy a dedicated band below the main artwork, rather than obscuring phones, cards and buttons.
- Artwork below the panel is moved or condensed where needed to leave space for captions.
- Video output is renamed `outputs/scamshield_third_cut_layout_fixed.mp4` (with matching `.srt`) so your previous cut remains intact.

## Install
Copy `asset_generator.py` and `editor.py` into the project's `agents/` folder, replacing those two files only. Backup the previous files if desired.

## Run
From `~/Desktop/scamshield_phase1` with your `.venv` active:

```bash
python -m agents.asset_generator
python -m agents.editor
```

**Do not rerun** the Scriptwriter, Storyboarder, Narrator or the Version 3 polish script. The audio files and scene timing are unchanged. The Editor still checks that each clip fits its slot.

## Testing performed
Both files compile under Python. The image generator produced all seven PNGs on sample project data, and the Editor's caption renderer produced seven captioned frames without an overlap or validation error. Full MP4 export was not executed here with your Mac's narration files.

## Caveat
The Editor shows whole-scene verbatim subtitles in a compact dedicated caption lane. For a final published reel, progressive phrase-by-phrase captions would be more dynamic, but this patch fixes the two reported overlap defects while retaining your current pipeline.
