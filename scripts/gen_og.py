#!/usr/bin/env python3
"""
Per-sensor Open Graph card generator.

Renders a 1200x630 PNG for each sensor entry so that a link dropped into
Slack, X, Bluesky or a PR review previews the *sensor* ("Mutation Testing",
Test Effectiveness, oracle high / independence medium / predictive) rather
than the generic site card.

Rendering is done by driving headless Chromium (via the `playwright` package
that already ships in this repo's virtualenv) over a small HTML template, so
the cards inherit the site's real design tokens — the antique-gold accent,
the family palette, the Fraunces / Inter / JetBrains Mono type stack — instead
of a hand-rolled second look.

Neither playwright nor Chromium is a build requirement:

  * Generation is *cached*. `og/manifest.json` records a hash of every input
    that affects a card (title, family, the three badge dimensions, entry id
    and TEMPLATE_VERSION). Unchanged sensors are skipped, so a normal build
    does no rendering at all and no PNG is rewritten (which matters: rsync
    deploys re-upload anything whose mtime/content moved).
  * If playwright or a browser is missing, generation is *skipped with a
    warning*, never a failure. build.py only points og:image at a card that
    actually exists on disk and otherwise falls back to the site-wide og.png.

Because the cards are checked into git CI never needs to render them: the
manifest is in sync, every sensor is skipped, and the committed PNGs ship
with the checkout that CI rsyncs to the server. (They live in `og/cards/`,
not `og/sensors/`, because .gitignore's `sensors/` rule has no leading slash
and so ignores a directory of that name at *any* depth.)

Usage:
    .venv/bin/python scripts/gen_og.py        # regenerate what changed
    .venv/bin/python scripts/gen_og.py --force
"""

import hashlib
import os
import html
import json
import sys
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent.parent
OG_DIR = SITE_ROOT / "og" / "cards"
MANIFEST_PATH = SITE_ROOT / "og" / "manifest.json"

# Bump when the template changes so every card is re-rendered.
TEMPLATE_VERSION = 1

WIDTH, HEIGHT = 1200, 630

# Family palette, copied from the dark-theme :root block of
# css/observatory.css (--fam-*). Kept as a literal rather than parsed so a
# CSS edit can't silently repaint the cards without a TEMPLATE_VERSION bump.
FAMILY_COLORS = {
    "structural": "#e5c07b",
    "behavioral": "#61afef",
    "test-effectiveness": "#c678dd",
    "invariants": "#98c379",
    "adversarial": "#e06c75",
    "runtime": "#56b6c2",
    "change": "#d19a66",
    "architecture": "#abb2bf",
    "evolution": "#a37cc0",
    "comprehension": "#7fb5d5",
}

DOTS = {"maximum": 5, "high": 4, "medium": 3, "low": 2, "minimum": 1}

FONT_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700"
    "&family=Inter:wght@300;400;500;600"
    "&family=JetBrains+Mono:wght@400;500;600"
    "&display=block"
)


def card_key(item):
    """Stable hash of everything the rendered card depends on."""
    payload = json.dumps(
        {
            "v": TEMPLATE_VERSION,
            "title": item.get("title", ""),
            "family_name": item.get("family_name", ""),
            "family_slug": item.get("family_slug", ""),
            "oracle": item.get("oracle", ""),
            "independence": item.get("independence", ""),
            "type": item.get("type", ""),
            "id": item.get("id", ""),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _dots(level, color):
    filled = DOTS.get(str(level).lower(), 0)
    out = ""
    for i in range(5):
        cls = "on" if i < filled else "off"
        style = f"background:{color}" if i < filled else ""
        out += f'<span class="dot {cls}" style="{style}"></span>'
    return out


def _meter(label, level, color):
    return f"""
      <div class="meter">
        <div class="meter-label">{html.escape(label)}</div>
        <div class="meter-dots">{_dots(level, color)}</div>
        <div class="meter-value">{html.escape(str(level or '—').title())}</div>
      </div>"""


def card_html(item):
    """The 1200x630 card as a standalone HTML document."""
    fam_slug = item.get("family_slug", "")
    color = FAMILY_COLORS.get(fam_slug, "#d4a056")
    title = html.escape(item.get("title", ""))
    # Long titles step down a size or two so they never overflow two lines.
    n = len(item.get("title", ""))
    title_size = 92 if n <= 22 else 78 if n <= 32 else 64 if n <= 46 else 54

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONT_URL}" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: {WIDTH}px; height: {HEIGHT}px; }}
  body {{
    background: #0a0e14;
    color: #e8edf2;
    font-family: "Inter", -apple-system, "Segoe UI", "DejaVu Sans", sans-serif;
    font-weight: 300;
    -webkit-font-smoothing: antialiased;
    position: relative;
    overflow: hidden;
  }}
  /* Faint observatory grid + a family-tinted glow in the top-right, so the
     card is recognisably from this site before you read a word of it. */
  .grid {{
    position: absolute; inset: 0;
    background-image:
      linear-gradient(rgba(30,41,59,0.55) 1px, transparent 1px),
      linear-gradient(90deg, rgba(30,41,59,0.55) 1px, transparent 1px);
    background-size: 60px 60px;
  }}
  /* The limb of a dome, in the family's colour. Deliberately a *flat* fill
     rather than a radial gradient: a smooth gradient across 1200x630 costs
     ~80KB of PNG per card (134KB vs 54KB measured), and these are checked
     into git. */
  .glow {{
    position: absolute; top: -220px; right: -160px;
    width: 640px; height: 640px; border-radius: 50%;
    background: {color}0f;
    box-shadow: inset 0 0 0 1px {color}26;
  }}
  .frame {{
    position: absolute; inset: 0;
    border-top: 8px solid {color};
    padding: 62px 72px 56px;
    display: flex; flex-direction: column; justify-content: space-between;
  }}
  .top {{ display: flex; align-items: center; gap: 14px; }}
  .wordmark {{
    font-family: "JetBrains Mono", "SF Mono", "DejaVu Sans Mono", monospace;
    font-size: 19px; font-weight: 500; letter-spacing: 0.30em;
    text-transform: uppercase; color: #d4a056;
  }}
  .sep {{ flex: 1; height: 1px; background: #1e293b; }}
  .entry-id {{
    font-family: "JetBrains Mono", "SF Mono", "DejaVu Sans Mono", monospace;
    font-size: 18px; letter-spacing: 0.12em; color: #8a96a8;
  }}
  .mid {{ margin-top: -8px; }}
  .family {{
    display: inline-flex; align-items: center; gap: 12px;
    font-family: "JetBrains Mono", "SF Mono", "DejaVu Sans Mono", monospace;
    font-size: 21px; font-weight: 500; letter-spacing: 0.18em;
    text-transform: uppercase; color: {color};
    margin-bottom: 22px;
  }}
  .family .mark {{
    width: 13px; height: 13px; border-radius: 50%; background: {color};
    box-shadow: 0 0 0 5px {color}22;
  }}
  h1 {{
    font-family: "Fraunces", Georgia, "DejaVu Serif", "Times New Roman", serif;
    font-size: {title_size}px; font-weight: 600; line-height: 1.06;
    letter-spacing: -0.015em; color: #e8edf2;
    max-width: 1000px;
  }}
  .meters {{ display: flex; gap: 64px; align-items: flex-end; }}
  .meter-label {{
    font-family: "JetBrains Mono", "SF Mono", "DejaVu Sans Mono", monospace;
    font-size: 15px; letter-spacing: 0.20em; text-transform: uppercase;
    color: #8a96a8; margin-bottom: 12px;
  }}
  .meter-dots {{ display: flex; gap: 8px; margin-bottom: 10px; }}
  .dot {{ width: 13px; height: 13px; border-radius: 50%; }}
  .dot.off {{ background: transparent; box-shadow: inset 0 0 0 2px #243044; }}
  .meter-value {{ font-size: 21px; font-weight: 400; color: #e8edf2; }}
  .type-pill {{
    font-family: "JetBrains Mono", "SF Mono", "DejaVu Sans Mono", monospace;
    font-size: 17px; font-weight: 500; letter-spacing: 0.14em;
    text-transform: uppercase; color: #0a0e14; background: #d4a056;
    padding: 9px 16px; border-radius: 3px;
  }}
  .bottom {{ display: flex; align-items: flex-end; justify-content: space-between; }}
  .domain {{
    font-family: "JetBrains Mono", "SF Mono", "DejaVu Sans Mono", monospace;
    font-size: 18px; letter-spacing: 0.06em; color: #aab4c4;
  }}
</style>
</head>
<body>
  <div class="grid"></div>
  <div class="glow"></div>
  <div class="frame">
    <div class="top">
      <div class="wordmark">Software Observatory</div>
      <div class="sep"></div>
      <div class="entry-id">{html.escape(item.get('id', ''))}</div>
    </div>

    <div class="mid">
      <div class="family"><span class="mark"></span>{html.escape(item.get('family_name', ''))}</div>
      <h1>{title}</h1>
    </div>

    <div class="bottom">
      <div class="meters">
{_meter('Oracle', item.get('oracle'), color)}
{_meter('Independence', item.get('independence'), color)}
        <div class="type-pill">{html.escape(str(item.get('type', '') or '').title())}</div>
      </div>
      <div class="domain">softwareobservatory.com</div>
    </div>
  </div>
</body>
</html>"""


def _load_manifest():
    try:
        with open(MANIFEST_PATH) as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get("cards"), dict):
            return data["cards"]
    except (OSError, ValueError):
        pass
    return {}


def _write_manifest(cards):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(
            {"template_version": TEMPLATE_VERSION, "cards": cards},
            f,
            indent=1,
            sort_keys=True,
        )
        f.write("\n")


def generate(items, force=False, quiet=False):
    """Render OG cards for `items`, skipping unchanged ones.

    `items` is a list of dicts with slug/title/family_slug/family_name/
    oracle/independence/type/id.

    Returns a dict: {"written": n, "skipped": n, "removed": n, "error": str|None}.
    Never raises — a missing browser is a skipped step, not a failed build.
    """
    def say(msg):
        if not quiet:
            print(msg)

    cards = _load_manifest()
    OG_DIR.mkdir(parents=True, exist_ok=True)

    wanted = {}
    stale = []
    for item in items:
        slug = item["slug"]
        key = card_key(item)
        wanted[slug] = key
        png = OG_DIR / f"{slug}.png"
        if force or cards.get(slug) != key or not png.exists():
            stale.append(item)

    # Drop cards for sensors that no longer exist.
    removed = 0
    for slug in list(cards):
        if slug not in wanted:
            png = OG_DIR / f"{slug}.png"
            if png.exists():
                png.unlink()
            del cards[slug]
            removed += 1

    if not stale:
        if removed:
            _write_manifest(cards)
        return {"written": 0, "skipped": len(items), "removed": removed, "error": None}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {
            "written": 0,
            "skipped": len(items) - len(stale),
            "removed": removed,
            "error": (
                f"playwright not installed; {len(stale)} OG card(s) not rendered "
                "(pages fall back to /og.png)"
            ),
        }

    # This machine's Chromium needs libasound.so.2, which was extracted by
    # hand into .browser-libs/ (system apt is blocked) — see OPERATIONS.md. Add
    # it to the loader path when it's there; harmless when it isn't.
    libdir = SITE_ROOT / ".browser-libs" / "usr" / "lib" / "x86_64-linux-gnu"
    if libdir.is_dir():
        existing = os.environ.get("LD_LIBRARY_PATH", "")
        parts = [str(libdir)] + [p_ for p_ in existing.split(":") if p_]
        os.environ["LD_LIBRARY_PATH"] = ":".join(parts)

    written = 0
    try:
        with sync_playwright() as p:
            # --no-sandbox: required under WSL / most CI containers, and the
            # only content rendered is this file's own template.
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page(
                viewport={"width": WIDTH, "height": HEIGHT},
                device_scale_factor=1,
            )
            for item in stale:
                page.set_content(card_html(item), wait_until="load")
                # Wait for the webfonts. If the network is unavailable the
                # fallbacks (Georgia / DejaVu Serif, DejaVu Sans/Mono) render
                # instead — a plainer card, never a failed build.
                try:
                    page.wait_for_function(
                        "document.fonts.status === 'loaded'", timeout=8000
                    )
                except Exception:
                    say("  warning: webfonts did not load; using fallback faces")
                page.screenshot(path=str(OG_DIR / f"{item['slug']}.png"))
                cards[item["slug"]] = card_key(item)
                written += 1
                say(f"  og/cards/{item['slug']}.png")
            browser.close()
    except Exception as exc:  # browser missing, sandbox denied, crash, ...
        if written:
            _write_manifest(cards)
        first = str(exc).strip().splitlines()[0] if str(exc).strip() else exc.__class__.__name__
        return {
            "written": written,
            "skipped": len(items) - len(stale),
            "removed": removed,
            "error": f"{first} — {len(stale) - written} card(s) not rendered "
                     "(pages fall back to /og.png)",
        }

    _write_manifest(cards)
    return {
        "written": written,
        "skipped": len(items) - len(stale),
        "removed": removed,
        "error": None,
    }


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build

    items = build.og_card_items(build.load_sensors())
    result = generate(items, force="--force" in sys.argv)
    print(
        f"{result['written']} written, {result['skipped']} unchanged, "
        f"{result['removed']} removed"
    )
    if result["error"]:
        print(f"warning: {result['error']}")


if __name__ == "__main__":
    main()
