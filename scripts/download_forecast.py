"""Download NESO 14-day wind forecast and upload to Google Drive.

On first run, creates a shared folder and shares it with the configured email.
On subsequent runs, uploads to the existing folder.

Requires:
  - GOOGLE_SERVICE_ACCOUNT_KEY env var (JSON key contents)
  - GDRIVE_SHARE_EMAIL env var (email to share folder with)
"""
import datetime
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen

RESOURCE_API = (
    "https://api.neso.energy/api/3/action/datapackage_show"
    "?id=14-days-ahead-operational-metered-wind-forecasts"
)

FOLDER_NAME = "NESO 14day wind fc (auto-archive)"
SHARE_EMAIL = os.environ.get("GDRIVE_SHARE_EMAIL", "geoff@watttime.org")
STATE_FILE = Path("data/gdrive_folder_id.txt")


def get_drive_service():
    """Build Google Drive API service from service account credentials."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    key_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not key_json:
        print("ERROR: GOOGLE_SERVICE_ACCOUNT_KEY env var not set")
        sys.exit(1)

    creds = service_account.Credentials.from_service_account_info(
        json.loads(key_json),
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    return build("drive", "v3", credentials=creds)


def get_or_create_folder(service):
    """Get existing folder ID from state file, or create a new folder."""
    # Check if we already have a folder ID
    if STATE_FILE.exists():
        folder_id = STATE_FILE.read_text().strip()
        # Verify it still exists
        try:
            service.files().get(fileId=folder_id, fields="id,name").execute()
            print(f"Using existing folder: {folder_id}")
            return folder_id
        except Exception:
            print("Stored folder ID is invalid, creating new folder")

    # Create folder
    folder_metadata = {
        "name": FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    folder_id = folder["id"]
    print(f"Created folder: {folder_id}")

    # Share with user
    permission = {
        "type": "user",
        "role": "writer",
        "emailAddress": SHARE_EMAIL,
    }
    service.permissions().create(
        fileId=folder_id,
        body=permission,
        sendNotificationEmail=True,
    ).execute()
    print(f"Shared folder with {SHARE_EMAIL}")

    # Save folder ID for future runs
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(folder_id)

    return folder_id


def upload_to_drive(service, folder_id, local_path, filename):
    """Upload a file to a Google Drive folder."""
    from googleapiclient.http import MediaFileUpload

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }
    media = MediaFileUpload(str(local_path), mimetype="text/csv")
    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,name,size")
        .execute()
    )
    size_mb = int(uploaded.get("size", 0)) / (1024 * 1024)
    print(f"  Uploaded: {uploaded['name']} ({size_mb:.1f} MB)")


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
    now = datetime.datetime.utcnow()
    timestamp = now.strftime("%Y-%m-%d_%H%M")

    print(f"NESO Wind Forecast Archive - {timestamp} UTC")

    # Set up Drive
    service = get_drive_service()
    folder_id = get_or_create_folder(service)

    # Get download URLs
    urls = get_download_urls()
    if not urls:
        print("ERROR: Could not fetch resource URLs from NESO API")
        sys.exit(1)

    print(f"Found {len(urls)} resources")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Download windfarm-level forecast
        if "windfarm" in urls:
            filename = f"windfarm_forecast_{timestamp}.csv"
            local_path = Path(tmpdir) / filename
            print(f"Downloading windfarm-level forecast...")
            data = urlopen(urls["windfarm"], timeout=120).read()
            local_path.write_bytes(data)
            print(f"  Downloaded: {len(data) / (1024*1024):.1f} MB")
            upload_to_drive(service, folder_id, local_path, filename)

        # Download national-level forecast
        if "national" in urls:
            filename = f"national_forecast_{timestamp}.csv"
            local_path = Path(tmpdir) / filename
            print(f"Downloading national-level forecast...")
            data = urlopen(urls["national"], timeout=120).read()
            local_path.write_bytes(data)
            print(f"  Downloaded: {len(data) / 1024:.0f} KB")
            upload_to_drive(service, folder_id, local_path, filename)

    print("Done!")


if __name__ == "__main__":
    main()
