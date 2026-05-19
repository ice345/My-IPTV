#!/usr/bin/env python3
"""Convert IPTV txt channel lists to M3U playlists."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_EPG = "http://kakaxi.indevs.in/epg.xml"


def split_channel_line(line: str) -> tuple[str, str] | None:
    if "," not in line:
        return None

    name, url = line.split(",", 1)
    name = name.strip()
    url = url.strip()
    if not name or not url:
        return None
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("rtp://") or url.startswith("udp://")):
        return None

    url = url.split("$", 1)[0].strip()
    return name, url


def convert_file(source: Path, output: Path, epg_url: str) -> int:
    current_group = ""
    entries: list[tuple[str, str, str]] = []

    for raw_line in source.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.endswith(",#genre#"):
            current_group = line.rsplit(",", 1)[0].strip()
            continue

        channel = split_channel_line(line)
        if channel is None:
            continue

        name, url = channel
        entries.append((name, url, current_group))

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(f'#EXTM3U x-tvg-url="{epg_url}"\n')
        for name, url, group in entries:
            group_attr = f' group-title="{group}"' if group else ""
            handle.write(f'#EXTINF:-1 tvg-name="{name}"{group_attr},{name}\n')
            handle.write(f"{url}\n")

    return len(entries)


def iter_sources(paths: list[Path]) -> list[Path]:
    sources: list[Path] = []
    for path in paths:
        if path.is_dir():
            sources.extend(sorted(path.rglob("*.txt")))
        elif path.suffix.lower() == ".txt":
            sources.append(path)
    return sources


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert IPTV txt files to M3U files.")
    parser.add_argument("paths", nargs="*", type=Path, default=[Path(".")])
    parser.add_argument("--epg-url", default=DEFAULT_EPG)
    args = parser.parse_args()

    converted = 0
    for source in iter_sources(args.paths):
        output = source.with_suffix(".m3u")
        count = convert_file(source, output, args.epg_url)
        print(f"{source} -> {output} ({count} channels)")
        converted += 1

    return 0 if converted else 1


if __name__ == "__main__":
    raise SystemExit(main())
