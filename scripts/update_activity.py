"""Generate a self-contained profile graph from GitHub's contribution calendar."""

import json
import math
import subprocess
from datetime import datetime, timezone
from html import escape
from pathlib import Path


QUERY = '''query {
  user(login: "ardakrt") {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}'''


def main():
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}"],
        check=True, capture_output=True, text=True, encoding="utf-8",
    )
    payload = json.loads(result.stdout)
    if payload.get("errors"):
        raise RuntimeError("GitHub did not return the contribution calendar")
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [day for week in weeks for day in week["contributionDays"]][-31:]
    if len(days) < 2:
        raise RuntimeError("Not enough contribution data; preserving existing graph")

    width, height = 1000, 320
    left, right, top, bottom = 55, 965, 85, 255
    maximum = max(4, max(day["contributionCount"] for day in days))
    step = max(1, math.ceil(maximum / 4))
    ceiling = step * 4
    points = [
        (left + i * (right - left) / (len(days) - 1),
         bottom - day["contributionCount"] * (bottom - top) / ceiling)
        for i, day in enumerate(days)
    ]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = f"{left},{bottom} {line} {right},{bottom}"
    total = sum(day["contributionCount"] for day in days)
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">GitHub activity — ardakrt</title>',
        f'<desc id="desc">{total} contributions from {days[0]["date"]} through {days[-1]["date"]}. Updated {updated}.</desc>',
        '<defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#c41e3a" stop-opacity=".35"/><stop offset="100%" stop-color="#c41e3a" stop-opacity=".02"/></linearGradient></defs>',
        '<rect width="100%" height="100%" rx="12" fill="#0d1117"/>',
        '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif">',
        '<text x="28" y="37" fill="#c41e3a" font-size="21" font-weight="600">Contribution activity</text>',
        f'<text x="965" y="37" text-anchor="end" fill="#8b949e" font-size="14">{total} contributions · Last {len(days)} days</text>',
    ]
    for i in range(5):
        value = i * step
        y = bottom - i * (bottom - top) / 4
        svg.extend([
            f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#21262d" stroke-dasharray="3 6"/>',
            f'<text x="40" y="{y + 4}" text-anchor="end" fill="#8b949e" font-size="12">{value}</text>',
        ])
    svg.extend([
        f'<polygon points="{area}" fill="url(#fill)"/>',
        f'<polyline points="{line}" fill="none" stroke="#c41e3a" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>',
    ])
    for (x, y), day in zip(points, days):
        label = escape(f'{day["date"]}: {day["contributionCount"]} contributions')
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#f0f6fc"><title>{label}</title></circle>')
    for index in [0, 5, 10, 15, 20, 25, len(days) - 1]:
        label = datetime.strptime(days[index]["date"], "%Y-%m-%d").strftime("%b %d")
        svg.append(f'<text x="{points[index][0]:.1f}" y="282" text-anchor="middle" fill="#8b949e" font-size="12">{label}</text>')
    svg.extend([
        f'<text x="965" y="308" text-anchor="end" fill="#6e7681" font-size="11">GitHub contribution calendar · Updated {updated}</text>',
        '</g></svg>',
    ])
    output = Path(__file__).resolve().parents[1] / "assets" / "activity.svg"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(svg) + "\n", encoding="utf-8")
    print(f"Updated {output.name}: {len(days)} days, {total} contributions")


if __name__ == "__main__":
    main()
