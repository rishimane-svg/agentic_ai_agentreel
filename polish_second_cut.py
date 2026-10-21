"""Apply ScamShield second-cut content without overwriting originals irreversibly.

Run from project root: python polish_second_cut.py
Uses existing outputs/script.json and outputs/storyboard.json.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / 'outputs'

VOICE = {
  1: 'Fake internship?',
  2: 'A job offer promises easy money, but demands a registration fee upfront. That is a warning sign. Always verify the recruiter.',
  3: 'Then a caller posing as a police officer threatens a so-called digital arrest and demands your personal details.',
  4: 'Never share OTPs, passwords or bank details. Verify suspicious callers using contact details from official websites.',
  5: 'Report suspected cybercrime at cybercrime.gov.in. For financial cyber fraud, call 1930 promptly.',
  6: 'Pause. Verify. Report.',
  7: '',
}
HEADLINES = {
  1: 'FAKE INTERNSHIP?', 2: 'SPOT THE RED FLAGS', 3: 'DIGITAL ARREST SCAM',
  4: 'PROTECT YOUR DETAILS', 5: 'REPORT THROUGH OFFICIAL CHANNELS',
  6: 'PAUSE. VERIFY. REPORT.', 7: 'STAY SAFE ONLINE',
}
VISUALS = {
  1: 'Phone showing a fictional internship notification and a caution badge',
  2: 'Fictional recruiter chat showing a high-paying job offer, upfront registration fee and urgent payment request',
  3: 'Mock video call from a self-declared police officer, anonymous silhouette, suspicious demand and warning signals',
  4: 'Split comparison: suspicious message versus independent verification through an official website',
  5: 'Reporting action card for cybercrime.gov.in and 1930 specifically for financial cyber fraud',
  6: 'Three bold action cards: pause, verify, report',
  7: 'Clear end card with cybercrime.gov.in, financial cyber fraud helpline, and mandatory AI-agent disclosure',
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
        if [s.get('start_s') for s in scenes] != [0,3,12,21,31,40,44] or [s.get('end_s') for s in scenes] != [3,12,21,31,40,44,48]:
            raise ValueError(f'{label} timeline differs from the approved 48s sequence')
    for path in (script_path, board_path):
        backup = path.with_name(path.stem + '_before_second_cut.json')
        if not backup.exists():
            shutil.copy2(path, backup)
    for scene in script['scenes']:
        i = scene['scene_id']
        scene['voiceover'] = VOICE[i]
        scene['visual_intent'] = VISUALS[i]
        scene['fact_ids'] = FACT_IDS[i]
    script['word_count'] = sum(len(s['voiceover'].split()) for s in script['scenes'])
    script['generation_mode'] = 'human_edited_from_llm_draft'
    script['qa_status'] = 'requires_factual_review_and_new_audio_timing'
    script['revision_note'] = 'Polished second-cut narration; not a new model-generated script. Values in mock offers are fictional.'
    for scene in board['scenes']:
        i = scene['scene_id']
        scene['voiceover'] = VOICE[i]
        scene['visual_description'] = VISUALS[i]
        scene['on_screen_text'] = HEADLINES[i]
        scene['fact_ids'] = FACT_IDS[i]
        if i == 2:
            scene['on_screen_disclaimer'] = 'Fictional example'
        if i == 7:
            scene['disclosure_required'] = True
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
