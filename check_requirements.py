
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

REQUIREMENTS_FILE = Path(__file__).parent / "requirements.txt"
PYPI_URL = "https://pypi.org/pypi"


def get_json(url):
    try:
        with urlopen(url, timeout=15) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return None
        raise


def main():
    missing_packages = []
    missing_versions = []
    valid_releases = []
    checked = 0

    with open(REQUIREMENTS_FILE, "r", encoding="utf-8-sig") as file:
        lines = file.readlines()

    for line in lines:
        line = line.split("#", 1)[0].strip()

        if not line:
            continue

        match = re.match(
            r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*==\s*([^\s;]+)",
            line,
        )

        if not match:
            continue

        name, version = match.groups()
        checked += 1

        package_name = quote(name, safe="")
        package_version = quote(version, safe="")

        package_url = f"{PYPI_URL}/{package_name}/json"
        version_url = (
            f"{PYPI_URL}/{package_name}/{package_version}/json"
        )

        try:
            package_data = get_json(package_url)

            if package_data is None:
                missing_packages.append(name)
                continue

            version_data = get_json(version_url)

            if version_data is None:
                missing_versions.append(f"{name}=={version}")
                continue

            urls = version_data.get("urls", [])

            if urls:
                upload_time = urls[0].get("upload_time", "")

                if upload_time:
                    valid_releases.append(
                        (upload_time, name, version)
                    )

        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
        ) as error:
            print(f"Could not check {name}=={version}: {error}")

    print(f"dependency checked: {checked}")
    print(f"package not exist: {len(missing_packages)}")
    print(f"version not on pypi: {len(missing_versions)}")

    if valid_releases:
        oldest = min(valid_releases, key=lambda item: item[0])

        print(
            f"oldest pinned release: "
            f"{oldest[1]}=={oldest[2]} ({oldest[0][:4]})"
        )
    else:
        print("oldest pinned release: None found")


if __name__ == "__main__":
    main()
