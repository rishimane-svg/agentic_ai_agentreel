"""Apply ScamShield third-cut content without overwriting originals irreversibly.

Run from project root: python polish_third_cut.py
Uses existing outputs/script.json and outputs/storyboard.json.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / 'outputs'

VOICE = {
  1: "Two cyber scams every student should know.",
  2: "A dream internship arrives by message. Great pay, immediate selection, then an upfront registration fee. That's a warning sign. Check the recruiter independently.",
  3: "Another caller claims to be police. They threaten a so-called digital arrest and demand your details. An official-looking call alone proves nothing.",
  4: "Both scams use pressure. Don't share OTPs, passwords or bank details. Pause, and check official contact information yourself.",
  5: "Report suspected cybercrime at cybercrime.gov.in. For financial cyber fraud, call 1930 promptly.",
  6: "Take a moment. Verify before you trust.",
  7: "",
}
START = [0, 6, 17, 29, 39, 50, 55]
END = [6, 17, 29, 39, 50, 55, 59]
HEADLINES = {
  1: 'TWO SCAMS. ONE SMART RESPONSE.', 2: 'THE FAKE INTERNSHIP TRAP',
  3: 'THE DIGITAL ARREST TRAP', 4: 'WHAT BOTH SCAMS SHARE',
  5: 'KNOW WHERE TO REPORT', 6: 'THINK BEFORE YOU TRUST',
  7: 'SCAMSHIELD: STAY SAFE ONLINE',
}
VISUALS = {
  1: 'Two incoming alerts: internship offer and suspicious official-looking call',
  2: 'Fictional recruiter chat shows attractive job offer, then fee and urgency warning',
  3: 'Fictional video call with generic anonymous avatar and intimidation demand',
  4: 'Two scams point to the same pressure technique, then a safety checklist',
  5: 'Separate high-contrast website reporting card and financial-fraud helpline card',
  6: 'Clear closing shield and concise memorable verification message',
  7: 'Minimal end card with reporting information and exact lab AI disclosure',
}
FACT_IDS = {
  1: [], 2: ['F001','F002'], 3: ['F003','F004'],
  4: ['F005','F006'], 5: ['F007','F008'], 6: [], 7: ['F007','F008'],
}


def apply():
    script_path = OUTPUTS / 'script.json'
    board_path = OUTPUTS / 'storyboard.json'
    if not script_path.exists() or not board_path.exists():
        raise FileNotFoundError('Run Scriptwriter and Storyboarder first; script.json and storyboard.json are required')
    script = json.loads(script_path.read_text(encoding='utf-8'))
    board = json.loads(board_path.read_text(encoding='utf-8'))
    for label, data in [('script', script), ('storyboard', board)]:
        scenes = data.get('scenes', [])
        if len(scenes) != 7 or [s.get('scene_id') for s in scenes] != list(range(1, 8)):
            raise ValueError(f'{label} must have scene IDs 1..7')
        if scenes[0].get('start_s') != 0 or scenes[-1].get('end_s') not in (48, 59):
            raise ValueError(f'{label} timeline unexpected')
    for path in (script_path, board_path):
        backup = path.with_name(path.stem + '_before_third_cut.json')
        if not backup.exists():
            shutil.copy2(path, backup)
    for scene in script['scenes']:
        i = scene['scene_id']
        scene['start_s'] = START[i-1]
        scene['end_s'] = END[i-1]
        scene['voiceover'] = VOICE[i]
        scene['visual_intent'] = VISUALS[i]
        scene['fact_ids'] = FACT_IDS[i]
    script['duration_s'] = 59
    script['word_count'] = sum(len(s['voiceover'].split()) for s in script['scenes'])
    script['generation_mode'] = 'human_edited_from_llm_draft'
    script['qa_status'] = 'requires_factual_review_and_new_audio_timing'
    script['revision_note'] = 'Polished third-cut narration; not a new model-generated script. Values in mock offers are fictional.'
    for scene in board['scenes']:
        i = scene['scene_id']
        scene['start_s'] = START[i-1]
        scene['end_s'] = END[i-1]
        scene['voiceover'] = VOICE[i]
        scene['visual_description'] = VISUALS[i]
        scene['on_screen_text'] = HEADLINES[i]
        scene['duration_s'] = END[i-1] - START[i-1]
        scene['fact_ids'] = FACT_IDS[i]
        if i == 2:
            scene['on_screen_disclaimer'] = 'Fictional example'
        if i == 7:
            scene['disclosure_required'] = True
    board['duration_s'] = 59
    board['generation_mode'] = 'human_edited_rule_based_storyboard'
    board['status'] = 'draft_requires_visual_and_audio_review'
    script_path.write_text(json.dumps(script, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    board_path.write_text(json.dumps(board, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Updated script and storyboard; original copies preserved.')
    print('Narration words:', script['word_count'])
    print('Next: python -m agents.asset_generator; python -m agents.narrator')
    print('Do NOT rerun Scriptwriter or Storyboarder: they would overwrite these edits.')

if __name__ == '__main__':
    apply()
