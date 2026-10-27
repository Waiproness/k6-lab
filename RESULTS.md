# K6 lab results

Actual measurements from 27 October 2026 (Asia/Bangkok), using k6 v2.2.0 against https://quickpizza.grafana.com.
Scripts, measurements and the draft reflection were prepared with Codex assistance. Review the evidence, make sure you understand each explanation, and adapt the reflection before submission.

## Part 0

- Step 0.1: http_req_duration = 281.45 ms (one request).
- Step 0.2: 77 requests; 3.6232 requests/s; p(95) = 554.78 ms.
  Each VU waits for its HTTP response and sleeps for 1 second before its next iteration. Five VUs therefore do not imply five requests per second; startup and finishing time also affect the reported rate.
- Step 0.3: 20 iterations shared by 5 VUs; see `reports/0-3-iterations.log`.
- Step 0.4: authenticated vegetarian pizza request; all three checks passed.
- Step 0.5: request without a token returned the expected 401; its responseCallback treats that expected status as success for http_req_failed.
- Step 0.6: normal exit code 0, p(95) 408.26 ms; P95=300 exit code 99, p(95) 409.71 ms.
- Step 0.7: 3 VUs for 30 seconds; p(95) 394.07 ms < 1000 ms; p(99) 432.57 ms < 1500 ms; failed 0.00% < 1%. All three rules passed (exit 0).
  Changed only the p(95) limit to 1 ms using P95=1: measured p(95) 446.07 ms, exit code 99.
- Step 0.8: original checks passed 185/219 (84.47%). The no-pepperoni check failed 9 times and the no-knife check failed 25 times; these may overlap in the same request.
  The catalogs returned `Pepperoni` and `Knife`, but the original exclusions used `pepperoni` and `knife`. Correcting their case fixed the observed problem.
  Corrected checks passed 222/222 (100.00%). The original run still exited 0 because it had no thresholds: failed checks alone do not fail the process.
  Random recommendations mean one manual request can happen to avoid both items even with incorrect exclusions. Repeated requests exposed the mistake. The fixed run is evidence for this sample, not a proof about every possible future response.

## Part A results

| Step | Test type | Users | Req/s | p(95) | Max | Failed | Checks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | Smoke | 1 | 0.4837 | 381.59 ms | 390.15 ms | 0.00% | 100.00% |
| A2 | Average load | 3 | 1.2957 | 566.30 ms | 935.69 ms | 0.00% | 100.00% |
| A3 | Stress | 5 | 2.1288 | 403.27 ms | 764.60 ms | 0.00% | 100.00% |
| A4 | Spike | 5 | 1.0167 | 535.79 ms | 1088.58 ms | 0.00% | 100.00% |
| A5 | Soak | 2 | 0.9582 | 576.32 ms | 1652.95 ms | 0.00% | 100.00% |

Users is the configured maximum. Response-time values use all HTTP requests; home and recommendation thresholds use their respective group submetrics.

## Part B — draft reflection for review

### 1. Results table

The Part A table above contains the actual A1–A5 measurements. The raw samples, summaries and HTML reports are retained in `reports/`.

### 2. Why fewer than 5 requests per second?

Step 0.2 achieved 3.6232 requests/s with 5 VUs. Each VU sends one request, waits for its response, and then sleeps for 1 second. Its average HTTP response took 318.34 ms, so each iteration takes longer than 1 second. Five users therefore produce fewer than 5 requests/s. Connection setup and run completion also affect the overall rate.

### 3. Average load, stress and the operational envelope

The overall p(95) changed from 566.30 ms at 3 VUs to 403.27 ms at 5 VUs. It did not grow in these runs. Both runs had zero failed HTTP requests and all checks passed. This is consistent with both loads being comfortably within the service's operational envelope; it does not identify its boundary. Shared-site traffic, network conditions and random sampling can explain differences, so a lower value in the stress run does not prove that increasing load made the server faster.

### 4. Spike and recovery

The baseline window (0–30 s) had p(95) 368.36 ms from 15 requests. During the 5-VU hold (35–65 s), it rose to 695.07 ms from 78 requests. After the load returned to 1 VU around 70 s, the first 20-second window (70–90 s) had p(95) 393.58 ms, close to baseline, and the following window (90–110 s) was 347.44 ms. Thus it was near baseline within the first approximately 20 seconds after ramp-down. However, the 110–130 s window rose again to 590.43 ms; this small sample does not establish a precise, sustained recovery time. Every window had zero HTTP failures. Timing is approximate because windows start at process launch, slightly before the k6 scenario starts. See `reports/stage-analysis.md` and the HTML dashboard.

### 5. Soak and degradation over time

During the 2-VU hold, the early window (30–150 s) had average 340.25 ms, p(95) 568.25 ms and failed rate 0.00%; the middle window (270–390 s) had average 334.60 ms, p(95) 572.30 ms and failed rate 0.00%; the late window (510–630 s) had average 347.23 ms, p(95) 626.20 ms and failed rate 0.00%. Compare all three windows rather than treating a single slow request as a trend. This short, low-load run cannot rule out long-term problems. A several-hour soak could expose a memory leak: retained allocations accumulate, increasing memory use, garbage-collection pauses and eventually errors or a crash.

For these observations, late-window p(95) was 10.2% higher than early-window p(95), while the average changed by 2.1%. There were no HTTP errors in any of the three windows. The tail was somewhat worse at the end, but the average was not steadily increasing across all three windows. This is insufficient evidence of sustained degradation or a specific resource leak.

### 6. Why p(95), rather than the average?

Many fast responses can hide a small set of very slow responses in the average. p(95) describes a latency boundary for 95% of requests, so it better expresses the experience of slower users and a testable service target. It still leaves the slowest 5% outside that boundary; p(99) and maximum latency provide additional context.

### 7. Why could controlled lab results differ?

First, requests over the internet include latency, jitter and routing effects that may be much smaller and more stable on a local lab network. Second, QuickPizza is shared with other learners, whose traffic and changing server conditions are outside our control. An isolated lab can control background load and server resources, producing different and often more repeatable measurements.

### 8. Why not hundreds of users against someone else's site?

High-volume tests consume real service capacity and can cause slowdowns, errors or outages for other users. A public practice site permits only small tests, not unlimited traffic. Stress, spike and breakpoint tests at large scale require an owned environment or explicit written authorization and agreed limits. This lab caps QuickPizza at 5 VUs and uses only 2 VUs for its longer soak.

### 9. Instagram: from a vague to a testable requirement

**Vague:** Instagram should load posts quickly.

**Testable example:** In an owned or explicitly authorized test environment, 3 concurrent users request the post-metadata endpoint for 30 seconds, with a 1-second think time after each response. The p(95) HTTP response duration must be below 1,000 ms, p(99) below 1,500 ms, and fewer than 1% of HTTP requests may fail. Each response must have a successful status and the expected post data. These are proposed test targets, not published Instagram guarantees. This measures API response time, not full screen rendering, media download or playback.

The latency and failure requirements map to these k6 options. The test would need an authorized endpoint and response checks; no requests were sent to Instagram.

```javascript
export const options = {
  vus: 3,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<1500'],
    http_req_failed: ['rate<0.01'],
  },
};
```

## Evidence and limitations

- `reports/*.log` retains real terminal output; `*.json` retains aggregate metrics; `*.meta.json` retains timestamps and exit codes.
- A2–A5 HTML dashboards and `*-series.jsonl` retain time-series evidence.
- These are individual runs on a shared service over the internet, not measurements of maximum capacity or proof of a causal performance change.
- Public repository: https://github.com/Waiproness/k6-lab. MyCourses submission must be completed by the student.
