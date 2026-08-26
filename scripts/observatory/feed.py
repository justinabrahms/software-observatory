"""The RSS feed (rss.xml)."""

import html

from .config import SITE_URL
from .dates import first_seen_dates
from .render import blurb_text
from .taxonomy import FAMILY_BY_SLUG


FEED_AUTHOR = "Justin Abrahms"


FEED_AUTHOR_EMAIL = "justin@abrah.ms"  # already published on /contact/


FEED_MAX_ITEMS = 20


def _rfc822(iso_date):
    """YYYY-MM-DD -> RFC 822, which is what RSS readers parse."""
    import datetime
    d = datetime.date.fromisoformat(iso_date)
    return d.strftime("%a, %d %b %Y 00:00:00 +0000")


def generate_rss(sensors, output_dir):
    """Write rss.xml — the most recent sensor entries, newest first.

    Reverse-chronological and capped so a new subscriber gets a readable
    window instead of the whole catalog in one dump, and so every entry added
    later actually shows up as something new.
    """
    published = first_seen_dates(sensors)
    ordered = sorted(
        sensors,
        key=lambda s: (published.get(s["slug"], ""), s["slug"]),
        reverse=True,
    )[:FEED_MAX_ITEMS]

    items = ""
    for s in ordered:
        fam = FAMILY_BY_SLUG.get(s.get("family", ""), {})
        blurb = blurb_text(s.get("body_html", ""), limit=200)
        url = f"{SITE_URL}/sensors/{s['slug']}/"
        items += f"""    <item>
      <title>{html.escape(s['title'])}</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <pubDate>{_rfc822(published[s['slug']])}</pubDate>
      <author>{FEED_AUTHOR_EMAIL} ({html.escape(FEED_AUTHOR)})</author>
      <dc:creator>{html.escape(FEED_AUTHOR)}</dc:creator>
      <description>{html.escape(blurb)}</description>
      <category>{html.escape(fam.get('name', ''))}</category>
    </item>
"""
    # lastBuildDate is the newest item's date, not the clock: a build that
    # changes nothing should produce a byte-identical feed (otherwise every
    # deploy re-uploads rss.xml and every conditional GET misses). The feed
    # genuinely has not changed since its newest entry.
    last_build = _rfc822(published[ordered[0]["slug"]]) if ordered else _rfc822("1970-01-01")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Software Observatory</title>
    <link>{SITE_URL}</link>
    <atom:link href="{SITE_URL}/rss.xml" rel="self" type="application/rss+xml"/>
    <description>New entries in the catalog of epistemic sensors for software correctness.</description>
    <language>en</language>
    <copyright>Content licensed CC BY-SA 4.0 — {html.escape(FEED_AUTHOR)}</copyright>
    <managingEditor>{FEED_AUTHOR_EMAIL} ({html.escape(FEED_AUTHOR)})</managingEditor>
    <webMaster>{FEED_AUTHOR_EMAIL} ({html.escape(FEED_AUTHOR)})</webMaster>
    <image>
      <url>{SITE_URL}/og.png</url>
      <title>Software Observatory</title>
      <link>{SITE_URL}</link>
    </image>
    <lastBuildDate>{last_build}</lastBuildDate>
{items.rstrip()}
  </channel>
</rss>"""
    with open(output_dir / "rss.xml", "w") as f:
        f.write(feed)
