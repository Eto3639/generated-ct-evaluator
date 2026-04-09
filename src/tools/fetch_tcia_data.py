import argparse
import os
import requests
from tcia_utils import nbia

def download_dicom(series_uid, path):
    """Downloads a DICOM series from TCIA."""
    print(f"Downloading DICOM series {series_uid} to {path}...")
    nbia.downloadSeries(series_uid, input_type="list", path=path)
    print("DICOM download complete.")

def download_nifti(url, path):
    """Downloads a NIfTI file from a URL."""
    print(f"Downloading NIfTI from {url} to {path}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("NIfTI download complete.")
    else:
        print(f"Failed to download NIfTI. Status code: {response.status_code}")

def main():
    parser = argparse.ArgumentParser(description="Fetch sample lung CT data from TCIA or URL.")
    parser.add_argument("--series_uid", type=str,
                        default="1.3.6.1.4.1.14519.5.2.1.6279.6001.179049373630447233647222147017",
                        help="TCIA Series Instance UID")
    parser.add_argument("--url", type=str, help="Direct URL to a NIfTI file")
    parser.add_argument("--out", type=str, default="./sample_data", help="Output directory or file path")

    args = parser.parse_args()

    if not os.path.exists(args.out) and not args.url:
        os.makedirs(args.out)

    if args.url:
        download_nifti(args.url, args.out)
    else:
        download_dicom(args.series_uid, args.out)

if __name__ == "__main__":
    main()
