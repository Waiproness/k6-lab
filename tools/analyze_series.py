"""Summarize saved samples by stage; does not send requests."""
import json
from datetime import datetime
from pathlib import Path

REPORTS = Path('reports')

def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)

def analyze(name, windows):
    meta = json.loads((REPORTS / f'{name}.meta.json').read_text())
    # The runner starts the clock just before launching k6, so stage offsets
    # differ from engine time by process initialization (approximately 1 s).
    origin = datetime.fromisoformat(meta['started_utc'])
    samples = []
    for line in (REPORTS / f'{name}-series.jsonl').read_text().splitlines():
        point = json.loads(line)
        if point['type'] != 'Point' or point['metric'] not in ('http_req_duration', 'http_req_failed'):
            continue
        data = point['data']
        seconds = (datetime.fromisoformat(data['time']) - origin).total_seconds()
        samples.append((seconds, point['metric'], data['value'], data['tags'].get('group', '')))
    result = []
    for label, start, end in windows:
        points = [p for p in samples if start <= p[0] < end]
        durations = [p[2] for p in points if p[1] == 'http_req_duration']
        failures = [p[2] for p in points if p[1] == 'http_req_failed']
        result.append({'window': label, 'start_s': start, 'end_s': end, 'requests': len(durations),
                       'p95_ms': percentile(durations, 0.95),
                       'avg_ms': sum(durations) / len(durations) if durations else None,
                       'max_ms': max(durations) if durations else None,
                       'failed_rate': sum(failures) / len(failures) if failures else None})
    return result

results = {}
for name, windows in {
    'a4-spike': [('baseline', 0, 30), ('high load', 35, 65), ('recovery 1', 70, 90),
                 ('recovery 2', 90, 110), ('recovery 3', 110, 130)],
    'a5-soak': [('early hold', 30, 150), ('middle hold', 270, 390), ('late hold', 510, 630)],
}.items():
    if (REPORTS / f'{name}.meta.json').exists():
        results[name] = analyze(name, windows)
if not results:
    raise SystemExit('No completed spike or soak run yet.')
(REPORTS / 'stage-analysis.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
lines = ['# Stage observations', '',
         'Computed from actual request samples. Windows use seconds after process launch, approximately aligned with k6 stages; allow about 1 second for startup. Each p(95) uses linear interpolation on samples in that window. Small samples make percentile estimates noisy.', '']
for name, rows in results.items():
    lines += [f'## {name}', '', '| Window | Seconds | Requests | Average (ms) | p(95) (ms) | Max (ms) | Failed |',
              '| --- | --- | --- | --- | --- | --- | --- |']
    for r in rows:
        lines.append(f"| {r['window']} | {r['start_s']}–{r['end_s']} | {r['requests']} | {r['avg_ms']:.2f} | {r['p95_ms']:.2f} | {r['max_ms']:.2f} | {100 * r['failed_rate']:.2f}% |")
    lines.append('')
(REPORTS / 'stage-analysis.md').write_text('\n'.join(lines), encoding='utf-8')
print(json.dumps(results, indent=2))
