# NESO Wind Forecast Archive

Automated daily archive of NESO's **14 Days Ahead Operational Metered Wind Forecasts**.

## Why

NESO publishes per-windfarm, half-hourly wind generation forecasts updated 8 times daily,
but only as a rolling snapshot (no historical archive). This workflow archives the forecast
daily for use in curtailment prediction model training and backtesting.

## What's archived

- **Windfarm-level forecast** (~3 MB gzipped): per-farm capacity, forecast MW, region
- **National-level forecast** (~10 KB gzipped): aggregate wind forecast

Files are gzip-compressed and committed to the `data/` directory.

## Source

- Dataset: [14 Days Ahead Operational Metered Wind Forecasts](https://www.neso.energy/data-portal/14-days-ahead-operational-metered-wind-forecasts)
- Dataset ID: `ca6fc361-9099-4ab2-ac02-c959431e84bc`
- License: NESO Open Data Licence

## Schedule

GitHub Actions runs daily at 06:00 UTC.

## Storage

~3 MB/day gzipped = ~1.1 GB/year. GitHub recommends repos under 1 GB.
If the repo grows too large, migrate to Git LFS or reduce to weekly snapshots
(consecutive forecasts overlap by 13+ days, so daily is somewhat redundant).

## Reading the data

```python
import gzip
import pandas as pd

with gzip.open("data/windfarm_forecast_2026-04-11_0600.csv.gz", "rt") as f:
    df = pd.read_csv(f)
```
