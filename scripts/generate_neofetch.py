#!/usr/bin/env python3
"""Generates a neofetch-style SVG card from live public GitHub data."""

import datetime
import json
import os
import urllib.request
from collections import defaultdict
from xml.sax.saxutils import escape

USERNAME = os.environ.get("GH_USERNAME", "ZakariaShahruri")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"
OUT_PATH = os.environ.get("OUT_PATH", "neofetch.svg")

BG_TOP = "#0f2027"
BG_BOTTOM = "#2c5364"
LABEL_COLOR = "#39ff9c"
VALUE_COLOR = "#e6edf3"
MUTED_COLOR = "#8b98a5"
SWATCHES = [
    "#0f2027", "#c0392b", "#39ff9c", "#f1c40f",
    "#2f81f7", "#9b59b6", "#1abc9c", "#e6edf3",
]


def api_get(path):
    url = path if path.startswith("http") else f"{API}{path}"
    req = urllib.request.Request(url)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USERNAME)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_user():
    return api_get(f"/users/{USERNAME}")


def fetch_top_languages(limit=5):
    repos = api_get(f"/users/{USERNAME}/repos?per_page=100&type=owner")
    totals = defaultdict(int)
    for repo in repos:
        if repo.get("fork"):
            continue
        try:
            langs = api_get(repo["languages_url"])
        except Exception:
            continue
        for lang, size in langs.items():
            totals[lang] += size
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    return [name for name, _ in ranked[:limit]]


def format_uptime(created_at):
    created = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").date()
    today = datetime.date.today()
    days = (today - created).days
    years, remainder = divmod(days, 365)
    months = remainder // 30
    parts = []
    if years:
        parts.append(f"{years} yr")
    if months or not years:
        parts.append(f"{months} mo")
    return " ".join(parts)


def build_svg(user, languages):
    avatar_url = f"https://github.com/{USERNAME}.png?size=200"
    host = user.get("name") or USERNAME
    location = user.get("location") or "Unknown"
    bio = user.get("bio") or ""
    public_repos = user.get("public_repos", 0)
    followers = user.get("followers", 0)
    uptime = format_uptime(user["created_at"])
    lang_str = ", ".join(languages) if languages else "N/A"

    fields = [
        ("user", f"{USERNAME}@github"),
        ("os", bio or "Applied Computer Science Student"),
        ("host", host),
        ("uptime", uptime),
        ("languages", lang_str),
        ("repos", str(public_repos)),
        ("followers", str(followers)),
        ("location", location),
    ]

    field_y_start = 78
    field_line_height = 24
    swatch_y = field_y_start + field_line_height * len(fields) + 14

    field_lines = []
    for i, (label, value) in enumerate(fields):
        y = field_y_start + i * field_line_height
        field_lines.append(
            f'<text x="190" y="{y}" font-family="Fira Code, Consolas, monospace" '
            f'font-size="14" fill="{LABEL_COLOR}" font-weight="bold">{escape(label)}</text>'
        )
        field_lines.append(
            f'<text x="300" y="{y}" font-family="Fira Code, Consolas, monospace" '
            f'font-size="14" fill="{VALUE_COLOR}">{escape(value)}</text>'
        )

    swatch_squares = []
    for i, color in enumerate(SWATCHES):
        x = 190 + i * 26
        swatch_squares.append(
            f'<rect x="{x}" y="{swatch_y}" width="20" height="20" rx="4" fill="{color}" />'
        )

    width, height = 700, swatch_y + 40

    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{BG_TOP}" />
      <stop offset="100%" stop-color="{BG_BOTTOM}" />
    </linearGradient>
    <clipPath id="avatarClip">
      <circle cx="95" cy="95" r="55" />
    </clipPath>
  </defs>
  <rect width="{width}" height="{height}" rx="16" fill="url(#bg)" />
  <image href="{avatar_url}" x="40" y="40" width="110" height="110" clip-path="url(#avatarClip)" />
  <circle cx="95" cy="95" r="55" fill="none" stroke="{LABEL_COLOR}" stroke-width="2" opacity="0.6" />
  <line x1="190" y1="55" x2="{width - 40}" y2="55" stroke="{MUTED_COLOR}" stroke-width="1" opacity="0.4" />
  <text x="190" y="40" font-family="Fira Code, Consolas, monospace" font-size="18" fill="{VALUE_COLOR}" font-weight="bold">{escape(USERNAME)}</text>
  {"".join(field_lines)}
  {"".join(swatch_squares)}
</svg>'''
    return svg


def main():
    user = fetch_user()
    languages = fetch_top_languages()
    svg = build_svg(user, languages)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
