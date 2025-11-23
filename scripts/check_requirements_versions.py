import re
from pathlib import Path

import requests
from packaging import version

print_red = lambda x: print("\33[91m", x, "\33[0m")
print_green = lambda x: print("\33[92m", x, "\33[0m")
print_yellow = lambda x: print("\33[93m", x, "\33[0m")

# Regex matching some_weird_package2[full]==4.3.2abcd
regex = re.compile(r"^[a-zA-Z0-9_\-\[\]]+==[a-zA-Z0-9.]+")


def check_requirements_versions(requirements_files):
    for requirements_file in requirements_files:
        requirements_path = Path(requirements_file)

        if not requirements_path.exists():
            print(f"{requirements_path.name} does not exists.")
            print()
            continue

        with open(requirements_path) as f:
            requirements = f.readlines()

        print(f" #### {requirements_path.name}")
        print()
        print(" Package                       Version        Latest         ")
        print(" ----------------------------- -------------- ---------------")

        for line in requirements:
            match = regex.match(line)
            if not match:
                continue

            # Extract package and version from regex match (e.g. some_weird_package2[full] and 4.3.2abcd)
            # and remove the extras requirements if present (e.g. remove [full] leaving only some_weird_package2)
            package, requirements_version = match.group().split("==")
            if "[" in package:
                package = package[: package.index("[")]

            # Retrieve package info from Pypi and extract latest version
            response = requests.get(f"https://pypi.org/pypi/{package}/json")
            latest_version = response.json().get("info").get("version")

            # Print with colors:
            # - green if versions are exactly equal (no update available)
            # - yellow if major versions are equal (minor or patch update available)
            # - red otherwise (major update available or another issue)
            print_with_colors = print_red
            if version.parse(latest_version) == version.parse(requirements_version):
                print_with_colors = print_green
            elif version.parse(latest_version).major == version.parse(requirements_version).major:
                print_with_colors = print_yellow

            print_with_colors(f"{package:30}{requirements_version:15}{latest_version:15}")

        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("requirements_file", nargs="+", help="requirements file")
    args = parser.parse_args()

    try:
        check_requirements_versions(args.requirements_file)
    except KeyboardInterrupt:
        pass
