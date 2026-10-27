"""Verify delivered evidence without sending any network traffic."""
import base64
import gzip
import json
from pathlib import Path
import re
import statistics

reports = Path('reports')
for name, expected_exit in [('0-1-first', 0), ('0-2-users', 0), ('0-3-iterations', 0),
                            ('0-4-api', 0), ('0-5-no-token', 0), ('0-6-normal', 0),
                            ('0-6-strict', 99), ('0-7-normal', 0), ('0-7-strict', 99),
                            ('0-8-original', 0), ('0-8-fixed', 0), ('explore', 0),
                            ('a1-smoke', 0), ('a2-average', 0), ('a3-stress', 0),
                            ('a4-spike', 0), ('a5-soak', 0)]:
    meta = json.loads((reports / f'{name}.meta.json').read_text())
    assert meta['exit_code'] == expected_exit, (name, meta['exit_code'])
    m = json.loads((reports / f'{name}.json').read_text())['metrics']
    assert m['http_reqs']['count'] > 0, name
    if name not in ('0-8-original', 'explore'):
        assert m['checks']['fails'] == 0, name
    if name.startswith('a') and name != 'a1-smoke':
        samples = [j for line in (reports / f'{name}-series.jsonl').read_text().splitlines()
                   if (j := json.loads(line))['type'] == 'Point']
        durations = [j['data']['value'] for j in samples if j['metric'] == 'http_req_duration']
        checks = [j['data']['value'] for j in samples if j['metric'] == 'checks']
        vus = [j['data']['value'] for j in samples if j['metric'] == 'vus']
        assert len(durations) == m['http_reqs']['count'], name
        assert len(checks) == m['checks']['passes'] + m['checks']['fails'], name
        assert abs(statistics.quantiles(durations, n=100, method='inclusive')[94] - m['http_req_duration']['p(95)']) < 1e-6, name
        assert max(vus) <= (2 if name == 'a5-soak' else 5), name
        html = (reports / f'{name}.html').read_text()
        encoded = re.search(r'<script id="data"[^>]*>(.*?)</script>', html, re.S)
        assert encoded, name
        frames = [json.loads(line) for line in gzip.decompress(base64.b64decode(encoded.group(1))).decode().splitlines() if line]
        assert len(frames) > 3 and any(frame['event'] == 'config' for frame in frames), name
    print(f'PASS {name}: {m["http_reqs"]["count"]} requests, exit {expected_exit}')

assert json.loads((reports / '0-3-iterations.json').read_text())['metrics']['iterations']['count'] == 20
assert json.loads((reports / '0-8-original.json').read_text())['metrics']['checks']['fails'] > 0
for name in ['01-first-test', '04-pizza-api', '05-no-token', '06-thresholds', '07-requirement',
             '08-bug-hunt', 'explore', 'journey', 'a1-smoke', 'a2-average', 'a3-stress', 'a4-spike', 'a5-soak']:
    assert Path(name + '.js').is_file(), name
assert 'pending' not in Path('RESULTS.md').read_text(encoding='utf-8')
print('All lab evidence checks passed. No requests sent by this verification.')
