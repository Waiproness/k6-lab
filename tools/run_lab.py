"""Run lab tests serially and retain real console output, metrics and exit codes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
PORTABLE_K6 = ROOT / '.tools/k6-v2.2.0-windows-amd64/k6.exe'
K6 = PORTABLE_K6 if PORTABLE_K6.is_file() else (shutil.which('k6') or 'k6')
REPORTS = ROOT / 'reports'

def run(name, script, *args, html=False):
    command = [str(K6), 'run', '--quiet', '--summary-trend-stats=avg,min,med,max,p(90),p(95),p(99)',
               '--summary-export', str(REPORTS / f'{name}.json')]
    if html:
        command += ['--out', f'web-dashboard=export=reports/{name}.html',
                    '--out', f'json=reports/{name}-series.jsonl']
    command += list(args) + [script]
    started = datetime.now(timezone.utc).isoformat()
    print(f'START {name} {started}', flush=True)
    env = dict(os.environ, K6_NO_USAGE_REPORT='true')
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (REPORTS / f'{name}.log').write_text(result.stdout + '\n' + result.stderr, encoding='utf-8')
    meta = {'started_utc': started, 'ended_utc': datetime.now(timezone.utc).isoformat(),
            'command': command[1:], 'exit_code': result.returncode}
    (REPORTS / f'{name}.meta.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(f'END {name}: exit={result.returncode}', flush=True)
    print(result.stdout[-650:], flush=True)
    if result.returncode not in (0, 99):
        print(result.stderr, flush=True)
        raise SystemExit(result.returncode)
    return result.returncode

if __name__ == '__main__':
    if sys.argv[1] == 'basics':
        run('0-1-first', '01-first-test.js')
        run('0-2-users', '01-first-test.js', '--vus', '5', '--duration', '20s')
        run('0-3-iterations', '01-first-test.js', '--vus', '5', '--iterations', '20')
        run('0-4-api', '04-pizza-api.js')
        run('0-5-no-token', '05-no-token.js')
        run('0-6-normal', '06-thresholds.js')
        run('0-6-strict', '06-thresholds.js', '-e', 'P95=300')
        run('0-7-normal', '07-requirement.js')
        run('0-7-strict', '07-requirement.js', '-e', 'P95=1')
        run('0-8-original', '08-bug-hunt-original.js', '--vus', '5', '--duration', '20s')
        run('explore', 'explore.js')
        run('0-8-fixed', '08-bug-hunt.js', '--vus', '5', '--duration', '20s')
    elif sys.argv[1] == 'journeys':
        if run('a1-smoke', 'a1-smoke.js') != 0:
            raise SystemExit('Smoke failed: inspect before larger tests.')
        for name in ['a2-average', 'a3-stress', 'a4-spike', 'a5-soak']:
            run(name, name + '.js', html=True)
