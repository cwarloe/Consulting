#!/usr/bin/env python3
"""Drift guard for the pitch package (no dependencies).

1. The Markdown and HTML copies of the pitch package must cite the same
   outbound links, so an edit to one copy that misses the other is caught.
2. Every relative link in a tracked Markdown file must point at a file that
   exists.

Run from the repo root:  python3 scripts/check_pitch.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PITCH = ROOT / "pitch" / "2026-bronco-entrepreneur-challenge"
MD = PITCH / "pitch-package.md"
HTML = PITCH / "october-25-pitch-brief.html"

MD_LINK = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
MD_AUTOLINK = re.compile(r"<(https?://[^>\s]+)>")
HTML_HREF = re.compile(r'href="([^"]+)"')


def outbound(urls):
    return {u for u in urls if u.startswith(("http://", "https://"))}


def main() -> int:
    errors = []

    md_text = MD.read_text(encoding="utf-8")
    html_text = HTML.read_text(encoding="utf-8")
    md_urls = outbound(MD_LINK.findall(md_text)) | set(MD_AUTOLINK.findall(md_text))
    html_urls = outbound(HTML_HREF.findall(html_text))
    for url in sorted(md_urls - html_urls):
        errors.append(f"only in {MD.name}: {url}")
    for url in sorted(html_urls - md_urls):
        errors.append(f"only in {HTML.name}: {url}")

    md_files = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)
    local_links = 0
    for path in md_files:
        for target in MD_LINK.findall(path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local_links += 1
            file_part = target.split("#", 1)[0]
            if file_part and not (path.parent / file_part).exists():
                errors.append(f"{path.relative_to(ROOT)}: broken link -> {target}")

    if errors:
        print("Pitch package check failed:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(
        f"OK: {len(md_urls)} outbound links match between {MD.name} and {HTML.name}; "
        f"{local_links} local links in {len(md_files)} Markdown files resolve."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
