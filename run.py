#!/usr/bin/env python3
"""ScamShield stage orchestrator (Python 3.9+; standard library).

Modes:
  --mode check  Preflight only, makes no changes.
  --mode qa     Run existing Critic against an approved MP4; no regeneration.
  --mode full --allow-regenerate   Run existing agents in order (may call APIs).

The approved MP4 is SHA256-guarded before/after each stage. The Critic's existing
exit code 2 for known QA failure is treated as a completed assessment, not a crash.
No autonomous repair is claimed. Per-stage timings are real; LLM token usage and
cost are NOT invented. Source agents must emit their own actual model-call logs.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent
STAGES = [
    ('planner', 'outputs/plan.json'),
    ('researcher', 'outputs/facts.json'),
    ('scriptwriter', 'outputs/script.json'),
    ('storyboarder', 'outputs/storyboard.json'),
    ('asset_generator', 'assets/manifest.csv'),
    ('narrator', 'outputs/narration_report.json'),
    ('editor', 'outputs/scamshield_final_polish.mp4'),
]


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def event(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')


def demand_present(path, kind='file'):
    if not path.is_file():
        raise RuntimeError('Required {} not found: {}'.format(kind, path))


def validate_json(path):
    demand_present(path)
    with path.open(encoding='utf-8') as f:
        result = json.load(f)
    if not isinstance(result, (dict, list)):
        raise ValueError('Expected JSON object/array in {}'.format(path))


def read_brief(path):
    demand_present(path, 'brief')
    text = path.read_text(encoding='utf-8')
    if not text.strip():
        raise ValueError('Brief is empty: {}'.format(path))
    return text


def safely_resolve(root, user_path):
    path = Path(user_path)
    return path if path.is_absolute() else root / path


def main(argv=None):
    parser = argparse.ArgumentParser(description='ScamShield agent orchestration with protected approved video')
    parser.add_argument('--mode', choices=['check', 'qa', 'full'], default='check')
    parser.add_argument('--brief', default='briefs/a05.yaml')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--video', default='outputs/scamshield_with_college_logo.mp4')
    parser.add_argument('--srt', default='outputs/scamshield_final_polish.srt')
    parser.add_argument('--allow-regenerate', action='store_true', help='Required for full mode; LLM calls may cost money')
    parser.add_argument('--report', default='outputs/qa_orchestrator.json')
    parser.add_argument('--log', default='logs/orchestrator_run_log.jsonl')
    args = parser.parse_args(argv)
    os.chdir(ROOT)
    run_id = 'scamshield-' + dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    brief = safely_resolve(ROOT, args.brief)
    video = safely_resolve(ROOT, args.video)
    srt = safely_resolve(ROOT, args.srt)
    report = safely_resolve(ROOT, args.report)
    log = safely_resolve(ROOT, args.log)

    try:
        read_brief(brief)
        demand_present(ROOT / 'agents' / 'critic.py', 'critic agent') if args.mode == 'qa' else None
        if args.mode in ('check', 'qa'):
            demand_present(video, 'approved MP4')
            demand_present(srt, 'SRT')
        if args.mode == 'full' and not args.allow_regenerate:
            raise RuntimeError('Full mode may overwrite generated outputs / make LLM calls. Re-run with --allow-regenerate.')
        if args.mode == 'full':
            for stage, _ in STAGES:
                demand_present(ROOT / 'agents' / (stage + '.py'), 'agent source')
            demand_present(ROOT / 'agents' / 'critic.py', 'critic agent')
        if args.mode == 'check':
            print('CHECK OK: brief and approved MP4/SRT exist; no source or output altered.')
            print('Approved MP4 SHA256:', sha256(video))
            print('Note: check mode does not test other agents, API credentials, or critic outcomes.')
            return 0
    except Exception as exc:
        print('PREFLIGHT FAILED:', exc, file=sys.stderr)
        return 1

    # Guard user's hand-approved output. Not an exhaustive transactional rollback
    # of other outputs; full mode intentionally regenerates intermediate artifacts.
    guard_hash = sha256(video) if video.is_file() else None
    env = os.environ.copy()
    env['PYTHONHASHSEED'] = str(args.seed)
    env['SCAMSHIELD_SEED'] = str(args.seed)
    env['SCAMSHIELD_BRIEF'] = str(brief)
    stage_names = [name for name, _ in STAGES] if args.mode == 'full' else []
    stage_names.append('critic')
    any_failed = False
    print('RUN ID:', run_id, '| mode:', args.mode)
    for name in stage_names:
        output_rel = next((out for stage, out in STAGES if stage == name), None)
        if name == 'critic':
            command = [sys.executable, '-m', 'agents.critic', '--video', str(video), '--srt', str(srt), '--report', str(report)]
        else:
            command = [sys.executable, '-m', 'agents.' + name]
        started = time.monotonic()
        print('START', name, flush=True)
        try:
            result = subprocess.run(command, cwd=str(ROOT), env=env, check=False)
            rc = result.returncode
        except OSError as exc:
            rc = 127
            print('EXECUTION ERROR:', exc, file=sys.stderr)
        elapsed = round(time.monotonic() - started, 3)
        status = 'ok' if rc == 0 else 'qa_failed' if name == 'critic' and rc == 2 else 'error'
        output_path = report if name == 'critic' else ROOT / output_rel
        if status == 'ok' and name != 'critic':
            try:
                demand_present(output_path, 'stage output')
                if output_path.suffix == '.json':
                    validate_json(output_path)
            except Exception as exc:
                status = 'error'
                print('OUTPUT VALIDATION ERROR:', exc, file=sys.stderr)
        record = {
            'ts': utc_now(), 'run_id': run_id, 'agent': name,
            'command': command, 'latency_s': elapsed,
            'exit_code': rc, 'status': status,
            'output_path': str(output_path.relative_to(ROOT)) if output_path.is_relative_to(ROOT) else str(output_path),
            'output_sha256': sha256(output_path) if output_path.is_file() else None,
            'model': 'not_measured_by_orchestrator',
            'input_tokens': None, 'output_tokens': None, 'cost_inr': None,
            'measurement_note': 'Per-model tokens/cost must come from actual provider usage recorded by stage agents',
        }
        event(log, record)
        print('END', name, status, 'elapsed', elapsed, 's')
        if guard_hash is not None and (not video.is_file() or sha256(video) != guard_hash):
            print('STOP: approved video changed unexpectedly. Inspect it; no automatic restoration performed.', file=sys.stderr)
            return 3
        if status == 'qa_failed':
            any_failed = True
            # The critic wrote the report. Preserve its honest FAIL and stop normally.
            break
        if status != 'ok':
            return 1
    print('Orchestration log:', log)
    print('QA report:', report)
    print('Note: automated critic REVIEWs still require documented human review.')
    return 2 if any_failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
