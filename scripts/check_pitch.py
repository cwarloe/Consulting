#!/usr/bin/env python3
"""Drift guard for the pitch package (no dependencies).

1. The Markdown and HTML copies of the pitch package must cite the same
   outbound links, so an edit to one copy that misses the other is caught.
2. Every relative link in a tracked Markdown file must point at a file that
   exists.
3. Every in-page link (href="#...") in the HTML brief must match an id on the
   page, ids must be unique, and any local href/src must point at a file that
   exists, so renaming a section can't silently break the brief's navigation.

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
HTML_LOCAL = re.compile(r'(?:href|src)="([^"]+)"')
HTML_ID = re.compile(r'\sid="([^"]+)"')


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

    ids = HTML_ID.findall(html_text)
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"{HTML.name}: duplicate id=\"{dup}\"")
    anchors = 0
    for target in HTML_LOCAL.findall(html_text):
        if target.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
            continue
        if target.startswith("#"):
            anchors += 1
            if target[1:] not in ids:
                errors.append(f"{HTML.name}: in-page link {target} has no matching id")
            continue
        file_part = target.split("#", 1)[0]
        if file_part and not (HTML.parent / file_part).exists():
            errors.append(f"{HTML.name}: broken link -> {target}")

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
        f"{local_links} local links in {len(md_files)} Markdown files resolve; "
        f"{anchors} in-page links in {HTML.name} match ids."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
