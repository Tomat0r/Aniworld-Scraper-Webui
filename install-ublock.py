import requests
import zipfile
import os
import shutil
from io import BytesIO
from tempfile import TemporaryDirectory

def get_latest_ublock_chromium_release():
    releases_url = "https://api.github.com/repos/gorhill/uBlock/releases"
    response = requests.get(releases_url)
    response.raise_for_status()

    releases = response.json()
    for release in releases:
        for asset in release.get("assets", []):
            if "chromium" in asset["name"]:
                return asset["browser_download_url"]

    raise RuntimeError("No Chromium release found")

def download_and_extract_zip(url, extract_to, new_folder_name):
    with TemporaryDirectory() as temp_dir:
        response = requests.get(url)
        response.raise_for_status()

        with zipfile.ZipFile(BytesIO(response.content)) as thezip:
            thezip.extractall(temp_dir)

        extracted_folders = os.listdir(temp_dir)
        if extracted_folders:
            src_folder = os.path.join(temp_dir, extracted_folders[0])
            dest_folder = os.path.join(extract_to, new_folder_name)
            if os.path.exists(dest_folder):
                shutil.rmtree(dest_folder)
            shutil.move(src_folder, dest_folder)

def main():
    try:
        url = get_latest_ublock_chromium_release()
        if url:
            print(f"Downloading: {url}")
            download_and_extract_zip(url, "./src/extensions", "ublock")
            print("Download and extraction complete, folder renamed to 'ublock'.")
        else:
            print("No suitable release found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
