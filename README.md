# NESO Wind Forecast Archive

Automated daily archive of NESO's **14 Days Ahead Operational Metered Wind Forecasts**
to Google Drive.

## Why

NESO publishes per-windfarm, half-hourly wind generation forecasts updated 8 times daily,
but only as a rolling snapshot (no historical archive). This workflow archives the forecast
twice daily for use in curtailment prediction model training and backtesting.

## What's archived

- **Windfarm-level forecast** (~16 MB/snapshot): per-farm capacity, forecast MW, region
- **National-level forecast** (~46 KB/snapshot): aggregate wind forecast

Files are uploaded to a Google Drive folder shared with the team.

## Source

- Dataset: [14 Days Ahead Operational Metered Wind Forecasts](https://www.neso.energy/data-portal/14-days-ahead-operational-metered-wind-forecasts)
- Dataset ID: `ca6fc361-9099-4ab2-ac02-c959431e84bc`
- License: NESO Open Data Licence

## Setup

### GitHub Secrets required

| Secret | Value |
|--------|-------|
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Full JSON contents of the service account key file |
| `GDRIVE_SHARE_EMAIL` | Email to share the Drive folder with (e.g. `geoff@watttime.org`) |

### Schedule

GitHub Actions runs at 06:00 and 18:00 UTC daily. Can also be triggered manually
from the Actions tab.

### First run

On first run, the script creates a Google Drive folder and shares it with the
configured email. The folder ID is saved to `data/gdrive_folder_id.txt` and
committed to the repo for subsequent runs.
