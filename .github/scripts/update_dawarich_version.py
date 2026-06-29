#!/usr/bin/env python3

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: update_dawarich_version.py <new-release-version>")

    new_release = sys.argv[1].strip()
    if not new_release:
        raise SystemExit("The new release version cannot be empty")

    addon_version = f"{new_release}-1"

    build_path = ROOT / "dawarich" / "build.yaml"
    config_path = ROOT / "dawarich" / "config.yaml"
    readme_path = ROOT / "README.md"
    changelog_path = ROOT / "dawarich" / "CHANGELOG.md"

    build_text = build_path.read_text(encoding="utf-8")
    build_pattern = re.compile(r"(freikin/dawarich:)([^\s\"']+)")

    def replace_build_tag(match: re.Match[str]) -> str:
        return f"{match.group(1)}{new_release}"

    new_build_text, build_count = build_pattern.subn(replace_build_tag, build_text)
    if build_count != 2:
        raise SystemExit("Could not update both Dawarich image tags in dawarich/build.yaml")
    build_path.write_text(new_build_text, encoding="utf-8")

    config_text = config_path.read_text(encoding="utf-8")
    config_pattern = re.compile(r'(^version:\s*")[^"]+(")', re.MULTILINE)

    def replace_config_version(match: re.Match[str]) -> str:
        return f'{match.group(1)}{addon_version}{match.group(2)}'

    new_config_text, config_count = config_pattern.subn(replace_config_version, config_text, count=1)
    if config_count != 1:
        raise SystemExit("Could not update the addon version in dawarich/config.yaml")
    config_path.write_text(new_config_text, encoding="utf-8")

    readme_text = readme_path.read_text(encoding="utf-8")
    readme_pattern = re.compile(
        r'^\*\*Current Dawarich version: ([^*]+)\*\* \(\[release notes\]\(https://github\.com/Freika/dawarich/releases/tag/([^\)]+)\)\)$',
        re.MULTILINE,
    )

    def replace_readme_version(match: re.Match[str]) -> str:
        return (
            f"**Current Dawarich version: {new_release}** "
            f"([release notes](https://github.com/Freika/dawarich/releases/tag/{new_release}))"
        )

    new_readme_text, readme_count = readme_pattern.subn(replace_readme_version, readme_text, count=1)
    if readme_count != 1:
        raise SystemExit("Could not update the Dawarich version note in README.md")
    readme_path.write_text(new_readme_text, encoding="utf-8")

    changelog_text = changelog_path.read_text(encoding="utf-8")
    changelog_prefix = "# Changelog\n\n"
    if not changelog_text.startswith(changelog_prefix):
        raise SystemExit("Could not find the changelog header in dawarich/CHANGELOG.md")

    changelog_entry = (
        f"## {addon_version}\n\n"
        f"- Upgrade base image to Dawarich {new_release} — see upstream "
        f"[{new_release}](https://github.com/Freika/dawarich/releases/tag/{new_release}) release notes\n\n"
    )
    new_changelog_text = changelog_prefix + changelog_entry + changelog_text[len(changelog_prefix) :]
    changelog_path.write_text(new_changelog_text, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())