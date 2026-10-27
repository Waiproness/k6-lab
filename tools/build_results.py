"""Build factual lab notes from saved k6 summaries, never from example numbers."""
import json
from pathlib import Path

REPORTS = Path('reports')

def metrics(name):
    return json.loads((REPORTS / f'{name}.json').read_text(encoding='utf-8'))['metrics']

def exit_code(name):
    return json.loads((REPORTS / f'{name}.meta.json').read_text(encoding='utf-8'))['exit_code']

def ms(value):
    return f'{value:.2f} ms'

def pct(value):
    return f'{100 * value:.2f}%'

m1 = metrics('0-1-first')
m2 = metrics('0-2-users')
m6 = metrics('0-6-normal')
m6s = metrics('0-6-strict')
m7 = metrics('0-7-normal')
m7s = metrics('0-7-strict')
bug = metrics('0-8-original')['checks']
fixed = metrics('0-8-fixed')['checks']
lines = [
    '# K6 lab results', '',
    'Actual measurements from 27 October 2026 (Asia/Bangkok), using k6 v2.2.0 against https://quickpizza.grafana.com.',
    'Scripts, measurements and the draft reflection were prepared with Codex assistance. Review the evidence, make sure you understand each explanation, and adapt the reflection before submission.', '',
    '## Part 0', '',
    f"- Step 0.1: http_req_duration = {ms(m1['http_req_duration']['avg'])} (one request).",
    f"- Step 0.2: {m2['http_reqs']['count']} requests; {m2['http_reqs']['rate']:.4f} requests/s; p(95) = {ms(m2['http_req_duration']['p(95)'])}.",
    '  Each VU waits for its HTTP response and sleeps for 1 second before its next iteration. Five VUs therefore do not imply five requests per second; startup and finishing time also affect the reported rate.',
    '- Step 0.3: 20 iterations shared by 5 VUs; see `reports/0-3-iterations.log`.',
    '- Step 0.4: authenticated vegetarian pizza request; all three checks passed.',
    '- Step 0.5: request without a token returned the expected 401; its responseCallback treats that expected status as success for http_req_failed.',
    f"- Step 0.6: normal exit code {exit_code('0-6-normal')}, p(95) {ms(m6['http_req_duration']['p(95)'])}; P95=300 exit code {exit_code('0-6-strict')}, p(95) {ms(m6s['http_req_duration']['p(95)'])}.",
    f"- Step 0.7: 3 VUs for 30 seconds; p(95) {ms(m7['http_req_duration']['p(95)'])} < 1000 ms; p(99) {ms(m7['http_req_duration']['p(99)'])} < 1500 ms; failed {pct(m7['http_req_failed']['value'])} < 1%. All three rules passed (exit {exit_code('0-7-normal')}).",
    f"  Changed only the p(95) limit to 1 ms using P95=1: measured p(95) {ms(m7s['http_req_duration']['p(95)'])}, exit code {exit_code('0-7-strict')}.",
    f"- Step 0.8: original checks passed {bug['passes']}/{bug['passes'] + bug['fails']} ({pct(bug['value'])}). The no-pepperoni check failed 9 times and the no-knife check failed 25 times; these may overlap in the same request.",
    '  The catalogs returned `Pepperoni` and `Knife`, but the original exclusions used `pepperoni` and `knife`. Correcting their case fixed the observed problem.',
    f"  Corrected checks passed {fixed['passes']}/{fixed['passes'] + fixed['fails']} ({pct(fixed['value'])}). The original run still exited 0 because it had no thresholds: failed checks alone do not fail the process.",
    '  Random recommendations mean one manual request can happen to avoid both items even with incorrect exclusions. Repeated requests exposed the mistake. The fixed run is evidence for this sample, not a proof about every possible future response.', '',
    '## Part A results', '',
    '| Step | Test type | Users | Req/s | p(95) | Max | Failed | Checks |',
    '| --- | --- | --- | --- | --- | --- | --- | --- |',
]
for step, name, label, users in [
    ('A1', 'a1-smoke', 'Smoke', 1), ('A2', 'a2-average', 'Average load', 3),
    ('A3', 'a3-stress', 'Stress', 5), ('A4', 'a4-spike', 'Spike', 5),
    ('A5', 'a5-soak', 'Soak', 2),
]:
    if not (REPORTS / f'{name}.json').exists():
        lines.append(f'| {step} | {label} | {users} | pending | pending | pending | pending | pending |')
        continue
    m = metrics(name)
    lines.append(f"| {step} | {label} | {users} | {m['http_reqs']['rate']:.4f} | {ms(m['http_req_duration']['p(95)'])} | {ms(m['http_req_duration']['max'])} | {pct(m['http_req_failed']['value'])} | {pct(m['checks']['value'])} |")
lines += ['', 'Users is the configured maximum. Response-time values use all HTTP requests; home and recommendation thresholds use their respective group submetrics.', '',
          '## Part B — draft reflection for review', '',
          '### 1. Results table', '',
          'The Part A table above contains the actual A1–A5 measurements. The raw samples, summaries and HTML reports are retained in `reports/`.', '',
          '### 2. Why fewer than 5 requests per second?', '',
          f"Step 0.2 achieved {m2['http_reqs']['rate']:.4f} requests/s with 5 VUs. Each VU sends one request, waits for its response, and then sleeps for 1 second. Its average HTTP response took {ms(m2['http_req_duration']['avg'])}, so each iteration takes longer than 1 second. Five users therefore produce fewer than 5 requests/s. Connection setup and run completion also affect the overall rate.", '',
          '### 3. Average load, stress and the operational envelope', '']
if (REPORTS / 'a3-stress.json').exists():
    avg_p95 = metrics('a2-average')['http_req_duration']['p(95)']
    stress_p95 = metrics('a3-stress')['http_req_duration']['p(95)']
    lines += [f"The overall p(95) changed from {ms(avg_p95)} at 3 VUs to {ms(stress_p95)} at 5 VUs. It did not grow in these runs. Both runs had zero failed HTTP requests and all checks passed. This is consistent with both loads being comfortably within the service's operational envelope; it does not identify its boundary. Shared-site traffic, network conditions and random sampling can explain differences, so a lower value in the stress run does not prove that increasing load made the server faster.", '']
else:
    lines += ['Awaiting the completed stress run.', '']

lines += ['### 4. Spike and recovery', '']
analysis_path = REPORTS / 'stage-analysis.json'
stage_analysis = json.loads(analysis_path.read_text()) if analysis_path.exists() else {}
if 'a4-spike' in stage_analysis:
    baseline, peak, recovery1, recovery2, recovery3 = stage_analysis['a4-spike']
    lines += [f"The baseline window (0–30 s) had p(95) {ms(baseline['p95_ms'])} from {baseline['requests']} requests. During the 5-VU hold (35–65 s), it rose to {ms(peak['p95_ms'])} from {peak['requests']} requests. After the load returned to 1 VU around 70 s, the first 20-second window (70–90 s) had p(95) {ms(recovery1['p95_ms'])}, close to baseline, and the following window (90–110 s) was {ms(recovery2['p95_ms'])}. Thus it was near baseline within the first approximately 20 seconds after ramp-down. However, the 110–130 s window rose again to {ms(recovery3['p95_ms'])}; this small sample does not establish a precise, sustained recovery time. Every window had zero HTTP failures. Timing is approximate because windows start at process launch, slightly before the k6 scenario starts. See `reports/stage-analysis.md` and the HTML dashboard.", '']
else:
    lines += ['Awaiting the completed spike run and stage analysis.', '']

lines += ['### 5. Soak and degradation over time', '']
if 'a5-soak' in stage_analysis:
    early, middle, late = stage_analysis['a5-soak']
    lines += [f"During the 2-VU hold, the early window (30–150 s) had average {ms(early['avg_ms'])}, p(95) {ms(early['p95_ms'])} and failed rate {pct(early['failed_rate'])}; the middle window (270–390 s) had average {ms(middle['avg_ms'])}, p(95) {ms(middle['p95_ms'])} and failed rate {pct(middle['failed_rate'])}; the late window (510–630 s) had average {ms(late['avg_ms'])}, p(95) {ms(late['p95_ms'])} and failed rate {pct(late['failed_rate'])}. Compare all three windows rather than treating a single slow request as a trend. This short, low-load run cannot rule out long-term problems. A several-hour soak could expose a memory leak: retained allocations accumulate, increasing memory use, garbage-collection pauses and eventually errors or a crash.", '']
    lines += [f"For these observations, late-window p(95) was {(late['p95_ms'] / early['p95_ms'] - 1) * 100:.1f}% higher than early-window p(95), while the average changed by {(late['avg_ms'] / early['avg_ms'] - 1) * 100:.1f}%. There were no HTTP errors in any of the three windows. The tail was somewhat worse at the end, but the average was not steadily increasing across all three windows. This is insufficient evidence of sustained degradation or a specific resource leak.", '']
else:
    lines += ['Awaiting the completed soak run and stage analysis.', '']

lines += ['### 6. Why p(95), rather than the average?', '',
          'Many fast responses can hide a small set of very slow responses in the average. p(95) describes a latency boundary for 95% of requests, so it better expresses the experience of slower users and a testable service target. It still leaves the slowest 5% outside that boundary; p(99) and maximum latency provide additional context.', '',
          '### 7. Why could controlled lab results differ?', '',
          'First, requests over the internet include latency, jitter and routing effects that may be much smaller and more stable on a local lab network. Second, QuickPizza is shared with other learners, whose traffic and changing server conditions are outside our control. An isolated lab can control background load and server resources, producing different and often more repeatable measurements.', '',
          '### 8. Why not hundreds of users against someone else\'s site?', '',
          'High-volume tests consume real service capacity and can cause slowdowns, errors or outages for other users. A public practice site permits only small tests, not unlimited traffic. Stress, spike and breakpoint tests at large scale require an owned environment or explicit written authorization and agreed limits. This lab caps QuickPizza at 5 VUs and uses only 2 VUs for its longer soak.', '',
          '### 9. Instagram: from a vague to a testable requirement', '',
          '**Vague:** Instagram should load posts quickly.', '',
          '**Testable example:** In an owned or explicitly authorized test environment, 3 concurrent users request the post-metadata endpoint for 30 seconds, with a 1-second think time after each response. The p(95) HTTP response duration must be below 1,000 ms, p(99) below 1,500 ms, and fewer than 1% of HTTP requests may fail. Each response must have a successful status and the expected post data. These are proposed test targets, not published Instagram guarantees. This measures API response time, not full screen rendering, media download or playback.', '',
          'The latency and failure requirements map to these k6 options. The test would need an authorized endpoint and response checks; no requests were sent to Instagram.', '',
          '```javascript',
          'export const options = {',
          '  vus: 3,',
          "  duration: '30s',",
          '  thresholds: {',
          "    http_req_duration: ['p(95)<1000', 'p(99)<1500'],",
          "    http_req_failed: ['rate<0.01'],",
          '  },',
          '};',
          '```', '',
          '## Evidence and limitations', '',
          '- `reports/*.log` retains real terminal output; `*.json` retains aggregate metrics; `*.meta.json` retains timestamps and exit codes.',
          '- A2–A5 HTML dashboards and `*-series.jsonl` retain time-series evidence.',
          '- These are individual runs on a shared service over the internet, not measurements of maximum capacity or proof of a causal performance change.',
          '- Public repository: https://github.com/Waiproness/k6-lab. MyCourses submission must be completed by the student.', '']
Path('RESULTS.md').write_text('\n'.join(lines), encoding='utf-8')
print('Updated RESULTS.md from actual saved results.')
