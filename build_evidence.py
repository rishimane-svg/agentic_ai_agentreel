#!/usr/bin/env python3
"""Create auditable AgentReel evidence from LOCAL project code and logs.
No API/network calls. Does not read .env. Python 3.9+.
"""
import argparse, ast, csv, json, re, hashlib
from pathlib import Path
from datetime import datetime, timezone

FIELDS = ['source_log','record_index','timestamp','run_id','stage','provider','model','input_tokens','output_tokens','cost_inr','elapsed_s','status','evidence_note']
LOG_NAMES = ['run_log.jsonl','orchestrator_run_log.jsonl']
PROMPT_AGENTS = ['planner','researcher','scriptwriter','storyboarder']


def clean_text(v, limit=150):
    s = str(v if v is not None else '').replace('\n',' ').replace('\r',' ')
    return s[:limit]


def take(record, *names):
    for n in names:
        if record.get(n) is not None:
            return record[n]
    return ''


def generate(root, overwrite=False):
    root = root.resolve()
    if not (root/'agents').is_dir():
        raise SystemExit('ERROR: Run from ScamShield root (agents/ missing)')
    prompts, logs = root/'prompts', root/'logs'
    prompts.mkdir(exist_ok=True); logs.mkdir(exist_ok=True)
    created=[]
    def write(path, contents):
        if path.exists() and not overwrite:
            print('SKIP existing:',path.relative_to(root)); return
        path.write_text(contents,encoding='utf-8'); created.append(str(path.relative_to(root)))

    inventory = ['# Prompt provenance inventory','',
        'Generated from the **current local source files**; it does not certify these were the exact versions used for the approved reel.',
        'The files contain source excerpts and interpolation placeholders, **not resolved prompts or API responses**.',
        'No secret files were read. A generated prompt or changed code should not be described as an original historical prompt.', '']
    for agent in PROMPT_AGENTS:
        f=root/'agents'/f'{agent}.py'
        if not f.exists(): continue
        src=f.read_text(encoding='utf-8'); lines=src.splitlines()
        try: tree=ast.parse(src)
        except SyntaxError as e:
            inventory.append(f'- **{agent}**: source syntax error ({e}); extraction skipped');continue
        occurrences=[]
        for n in ast.walk(tree):
            if isinstance(n,(ast.Assign,ast.AnnAssign)):
                targets=n.targets if isinstance(n,ast.Assign) else [n.target]
                varnames=[t.id for t in targets if isinstance(t,ast.Name)]
                if any(('prompt' in x.lower() or x.lower() in ('messages','system_message')) for x in varnames):
                    val=n.value
                    if isinstance(val,(ast.Str,ast.Constant,ast.JoinedStr,ast.List,ast.Dict)) and hasattr(n,'lineno'):
                        fragment='\n'.join(lines[n.lineno-1:n.end_lineno]); occurrences.append((n.lineno,fragment))
        occurrences=sorted(set(occurrences))
        sha=hashlib.sha256(f.read_bytes()).hexdigest()
        content=[f'# {agent}: prompt-related source excerpts','',f'- Source: `agents/{agent}.py`',f'- Source SHA-256: `{sha}`','- Provenance: current working tree at generation time; historical version not established.','']
        if not occurrences:
            content+=['No standalone prompt assignment recognized by the extractor. **Inspect this agent manually.**','']
        for i,(lineno,frag) in enumerate(occurrences,1):
            content.extend([f'## Excerpt {i} — source line {lineno}','', '```python',frag,'```',''])
        dest=prompts/f'{agent}_current_source_excerpts.md';write(dest,'\n'.join(content))
        inventory.append(f'- `{dest.relative_to(root)}` — {len(occurrences)} recognized source assignment(s), SHA-256 `{sha[:12]}…`')
    inventory.extend(['', '## Manual check','',
        'Review API call sites and any dynamically built prompts; the AST extractor is intentionally conservative.',
        'Do not claim these excerpts are complete templates or prompt versions without checking the actual code.',
        'Where the written assignment requests versioned templates, save verified static templates separately and update agents to load them only after testing.', ''])
    write(prompts/'PROMPT_INVENTORY.md','\n'.join(inventory))

    rows=[]; counts={}
    for filename in LOG_NAMES:
        f=logs/filename
        if not f.is_file():continue
        for idx,line in enumerate(f.read_text(encoding='utf-8').splitlines(),1):
            if not line.strip():continue
            try: rec=json.loads(line)
            except (ValueError,TypeError):
                counts['invalid_json_rows']=counts.get('invalid_json_rows',0)+1
                continue
            if not isinstance(rec,dict):continue
            stage=take(rec,'agent','stage')
            # Orchestration rows are stage timing records, NOT per-model usage, and may duplicate model calls.
            is_orchestrator=filename=='orchestrator_run_log.jsonl'
            model='' if is_orchestrator else take(rec,'model')
            token_in='' if is_orchestrator else take(rec,'input_tokens','prompt_tokens')
            token_out='' if is_orchestrator else take(rec,'output_tokens','completion_tokens')
            cost='' if is_orchestrator else take(rec,'cost_inr')
            evidence='orchestration stage timing only; NOT an independent model call' if is_orchestrator else 'agent-authored log; provider invoice not independently verified'
            rows.append({
                'source_log':filename,'record_index':idx,
                'timestamp':clean_text(take(rec,'timestamp','ts','time')),
                'run_id':clean_text(take(rec,'run_id')),
                'stage':clean_text(stage),'provider':clean_text(take(rec,'provider') if not is_orchestrator else ''),
                'model':clean_text(model),'input_tokens':token_in,'output_tokens':token_out,
                'cost_inr':cost, 'elapsed_s':take(rec,'elapsed_s','latency_s','duration_s'),
                'status':clean_text(take(rec,'status')),'evidence_note':evidence
            })
    dest=logs/'cost_report.csv'
    from io import StringIO
    buf=StringIO(); w=csv.DictWriter(buf,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    write(dest,buf.getvalue())
    readme='''# Usage/cost evidence notes\n\nThis CSV is an **inventory of available log records**, not a verified bill or a complete single-run cost calculation. Rows from orchestration logs are stage executions and may overlap agent logs; **do not sum all rows as API calls**. Empty fields mean **not measured / not recorded**, not zero.\n\nGroq token logs can be checked against provider records if available. Edge-TTS/local graphical work should not be assigned hypothetical fees. The working reel was generated across several iterations, not one documented uninterrupted run.\n\nRows are included only where records are present; log gaps must remain gaps.\n'''
    write(logs/'COST_REPORT_NOTES.md',readme)
    interventions='''# Human interventions and approvals — historical reconstruction\n\n**Provenance:** Reconstructed from project discussion and existing artifacts, **not a contemporaneous timestamped log**. Exact timestamps, number of edits and formal intervention counts are **unknown** unless verified against original logs. Do not present these as the live-run intervention count.\n\n| Time | Stage | Human involvement | Reason | Record status |\n|---|---|---|---|---|\n| Not recorded | Scriptwriter | Edited generated voiceover and shortened scenes, including Scenes 2 and 4 | TTS timing and narrative clarity | Confirmed in development conversation; exact change count unknown |\n| Not recorded | Storyboard / graphics | Reviewed and revised visuals through multiple cuts | Improve engagement and contrast of scam examples | Confirmed; exact count unknown |\n| Not recorded | Asset Generator / Editor | Requested correction for colliding headings, subtitles and text overflow | Readability and safe layout | Confirmed; exact count unknown |\n| Not recorded | Editor | Requested reduced silent gaps; adopted approximately 53.26-second pacing | Reel engagement | Confirmed |\n| Not recorded | End card | Supplied college-logo SVG and approved new final video | Institutional branding | Confirmed; logo authorization still to verify |\n| Not recorded | Critic / QA | Chose to retain original narration despite measured loudness deviation | Listening preference; deviation documented, not waived by rubric | Confirmed |\n| Not recorded | Human review | Viewed and approved finished reel | Creative sign-off | Confirmed; mandatory Category A safety approval still needs explicit sign-off |\n\n## Formal review sign-off (complete manually)\n\n- Reviewer: **PENDING**\n- Review date: **PENDING**\n- Video SHA-256: **PENDING**\n- Facts and contacts reviewed against original official publications: **PENDING**\n- Logo permission/authorization checked: **PENDING**\n- Subtitle/mobile safe-zone review: **PENDING**\n- QA known deviation accepted for submission by faculty (if applicable): **PENDING**\n\n*Do not change these PENDING markers to PASS without performing the checks.*\n'''
    write(logs/'interventions.md',interventions)
    print('Source log records identified:',len(rows))
    print('New files:', ', '.join(created) or 'none (existing files left unchanged)')
    print('No provider calls were made. No source files or existing reports were modified.')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description='Build ScamShield evidence files from local code and logs.')
    ap.add_argument('--root',type=Path,default=Path('.'))
    ap.add_argument('--overwrite',action='store_true',help='Regenerate evidence files; review before using')
    args=ap.parse_args();generate(args.root,args.overwrite)
