# Stage observations

Computed from actual request samples. Windows use seconds after process launch, approximately aligned with k6 stages; allow about 1 second for startup. Each p(95) uses linear interpolation on samples in that window. Small samples make percentile estimates noisy.

## a4-spike

| Window | Seconds | Requests | Average (ms) | p(95) (ms) | Max (ms) | Failed |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 0–30 | 15 | 315.67 | 368.36 | 383.76 | 0.00% |
| high load | 35–65 | 78 | 357.99 | 695.07 | 1088.58 | 0.00% |
| recovery 1 | 70–90 | 9 | 319.32 | 393.58 | 412.70 | 0.00% |
| recovery 2 | 90–110 | 11 | 307.71 | 347.44 | 353.63 | 0.00% |
| recovery 3 | 110–130 | 9 | 360.08 | 590.43 | 717.49 | 0.00% |

## a5-soak

| Window | Seconds | Requests | Average (ms) | p(95) (ms) | Max (ms) | Failed |
| --- | --- | --- | --- | --- | --- | --- |
| early hold | 30–150 | 115 | 340.25 | 568.25 | 1088.75 | 0.00% |
| middle hold | 270–390 | 119 | 334.60 | 572.30 | 1124.31 | 0.00% |
| late hold | 510–630 | 117 | 347.23 | 626.20 | 1652.95 | 0.00% |
