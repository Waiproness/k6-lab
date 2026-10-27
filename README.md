# K6 lab — QuickPizza

ITDS362, Week 9, lab sheet version 2.0 (21 October 2026).

Public repository: https://github.com/Waiproness/k6-lab

This folder contains the lab scripts, actual run evidence and a draft Part B reflection. Review and adapt `RESULTS.md` before submitting your repository link on MyCourses. Part B question 9 uses Instagram, as selected by the student; it is a proposed requirement, not an actual test of Instagram.

## Run on Windows PowerShell

k6 v2.2.0 was installed on Windows using `winget install k6 --source winget --version 2.2.0`. A fresh shell can run `k6 version` through PATH. The original measurements used the same version as a portable binary stored locally in `.tools/` and excluded from Git. On another machine, install k6 using the [official installation guide](https://grafana.com/docs/k6/latest/set-up/install-k6/).

```powershell
$k6 = 'k6' # For a globally installed k6
if (Test-Path '.\.tools\k6-v2.2.0-windows-amd64\k6.exe') {
  $k6 = '.\.tools\k6-v2.2.0-windows-amd64\k6.exe'
}
& $k6 version
& $k6 run 01-first-test.js
& $k6 run --vus 5 --duration 20s 01-first-test.js
& $k6 run --vus 5 --iterations 20 01-first-test.js
& $k6 run 04-pizza-api.js
& $k6 run 05-no-token.js
& $k6 run 06-thresholds.js
$LASTEXITCODE
& $k6 run -e P95=300 06-thresholds.js
$LASTEXITCODE
& $k6 run 07-requirement.js
& $k6 run -e P95=1 07-requirement.js
$LASTEXITCODE
& $k6 run explore.js
& $k6 run --vus 5 --duration 20s 08-bug-hunt.js
& $k6 run a1-smoke.js
& $k6 run --out web-dashboard=export=reports/a2-average.html a2-average.js
& $k6 run --out web-dashboard=export=reports/a3-stress.html a3-stress.js
& $k6 run --out web-dashboard=export=reports/a4-spike.html a4-spike.js
& $k6 run --out web-dashboard=export=reports/a5-soak.html a5-soak.js
```

Run tests one at a time. Never exceed 5 virtual users on QuickPizza. Average and stress stages total 3 minutes each; spike totals 2 minutes 20 seconds; soak totals 11 minutes including its ramps, at no more than 2 users. A small final grace period may allow an in-progress iteration to finish.

## Evidence

- `reports/*.log`: actual terminal summaries and diagnostics.
- `reports/*.json`: actual aggregate metrics; `*.meta.json` records command, UTC timestamps and process exit code.
- `reports/a2-average.html` through `a5-soak.html`: standalone time-series dashboards.
- The original bug-hunt run is retained separately from the corrected run.
- `reports/stage-analysis.md`: measured spike and soak windows calculated from raw samples; windows are approximately aligned with the stages.

To regenerate the analysis and verify the evidence without sending requests:

```powershell
python tools/analyze_series.py
python tools/build_results.py
python tools/verify_results.py
```

Checks validate responses; thresholds decide the test exit status. A threshold failure (exit 99) is an expected part of Steps 0.6 and 0.7. Do not change observed numbers to match examples in the sheet.

## Submission

Use a public GitHub repository named `k6-lab`. Review files for personal data before publishing; `.tools/` must stay excluded. Commit and push your work, then submit the repository link yourself on MyCourses. Check the deadline there.
