"""Download NESO 14-day wind forecast and commit to repo.

Saves windfarm-level and national-level CSVs to data/ directory.
GitHub Actions workflow commits and pushes after this script runs.

Requires no credentials - NESO data portal is open.
"""
import datetime
import json
import gzip
import sys
from pathlib import Path
from urllib.request import urlopen

RESOURCE_API = (
    "https://api.neso.energy/api/3/action/datapackage_show"
    "?id=14-days-ahead-operational-metered-wind-forecasts"
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def get_download_urls():
    """Get current download URLs from the NESO resource API."""
    data = json.loads(urlopen(RESOURCE_API, timeout=30).read())
    resources = data.get("result", {}).get("resources", [])

    urls = {}
    for r in resources:
        path = r.get("path", "")
        if "windunit" in path.lower():
            urls["windfarm"] = path
        elif "wind_forecast" in path.lower():
            urls["national"] = path

    return urls


def main():
    now = datetime.datetime.now(datetime.UTC)
    timestamp = now.strftime("%Y-%m-%d_%H%M")

    print(f"NESO Wind Forecast Archive - {timestamp} UTC")

    urls = get_download_urls()
    if not urls:
        print("ERROR: Could not fetch resource URLs from NESO API")
        sys.exit(1)

    print(f"Found {len(urls)} resources")

    for key, url in urls.items():
        filename = f"{key}_forecast_{timestamp}.csv.gz"
        out_path = DATA_DIR / filename
        print(f"Downloading {key} forecast...")
        raw = urlopen(url, timeout=120).read()
        # Gzip compress to save repo space (~80% reduction)
        compressed = gzip.compress(raw)
        out_path.write_bytes(compressed)
        raw_mb = len(raw) / (1024 * 1024)
        gz_mb = len(compressed) / (1024 * 1024)
        print(f"  {raw_mb:.1f} MB -> {gz_mb:.1f} MB (gzipped)")

    print("Done!")


if __name__ == "__main__":
    main()
