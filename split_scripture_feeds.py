#!/usr/bin/env python3
"""Split the combined scriptures.xml into five per-volume podcast feeds.

Reads scriptures.xml (already generated) and produces:
  - old-testament.xml
  - new-testament.xml
  - book-of-mormon.xml
  - doctrine-and-covenants.xml
  - pearl-of-great-price.xml

Each feed is a standalone valid podcast RSS feed pointing at the Church CDN.
"""
import os
import re
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

REPO = "/Users/ericwilde/.gus/tmp/podcast-feed/vger-faith-podcast"
SOURCE = os.path.join(REPO, "scriptures.xml")
FEED_HOST = "https://erwilde.github.io/vger-faith-podcast"

# Season number -> (slug, display name, art file)
VOLUMES = {
    1: ("old-testament", "Old Testament"),
    2: ("new-testament", "New Testament"),
    3: ("book-of-mormon", "Book of Mormon"),
    4: ("doctrine-and-covenants", "Doctrine and Covenants"),
    5: ("pearl-of-great-price", "Pearl of Great Price"),
}

# Register namespaces so output is clean
NS = {
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "atom": "http://www.w3.org/2005/Atom",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

tree = ET.parse(SOURCE)
root = tree.getroot()
channel = root.find("channel")

# Collect items by season
by_season = {1: [], 2: [], 3: [], 4: [], 5: []}
for item in channel.findall("item"):
    season_el = item.find(f"{{{NS['itunes']}}}season")
    if season_el is None:
        continue
    season = int(season_el.text)
    if season in by_season:
        by_season[season].append(item)

print(f"Loaded {sum(len(v) for v in by_season.values())} items across {len(by_season)} volumes")

now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

def build_feed(season_num, slug, display_name, items):
    """Build a standalone per-volume RSS feed string."""
    summary = (
        f"Personal feed for Eric Wilde — official chapter-by-chapter audio of the "
        f"{display_name}, streamed from the Church's CDN. "
        f"Audio © Intellectual Reserve, Inc.; for personal study."
    )
    short_desc = f"Chapter-by-chapter audio of the {display_name}, from the official Church CDN. Personal use only."
    art = f"{FEED_HOST}/scriptures-cover-v2.jpg"

    header = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{display_name}</title>
    <link>{FEED_HOST}</link>
    <atom:link href="{FEED_HOST}/{slug}.xml" rel="self" type="application/rss+xml"/>
    <language>en-us</language>
    <copyright>© Intellectual Reserve, Inc. — Personal Use</copyright>
    <itunes:author>The Church of Jesus Christ of Latter-day Saints</itunes:author>
    <itunes:summary>{summary}</itunes:summary>
    <description>{short_desc}</description>
    <itunes:owner>
      <itunes:name>Eric Wilde</itunes:name>
      <itunes:email>erwilde@telus.net</itunes:email>
    </itunes:owner>
    <itunes:image href="{art}"/>
    <image>
      <url>{art}</url>
      <title>{display_name}</title>
      <link>{FEED_HOST}</link>
    </image>
    <itunes:category text="Religion &amp;amp; Spirituality">
      <itunes:category text="Christianity"/>
    </itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>serial</itunes:type>
    <lastBuildDate>{now}</lastBuildDate>
"""
    # Render each item — strip the season element since each feed has one volume
    body_parts = []
    for item in items:
        # Remove season tag so Apple sees a clean one-volume feed
        season_el = item.find(f"{{{NS['itunes']}}}season")
        if season_el is not None:
            item.remove(season_el)
        # Serialize without the namespace prefix declarations
        item_str = ET.tostring(item, encoding="unicode")
        # Clean up namespace prefix attributes that ET may add
        item_str = re.sub(r' xmlns:[a-z]+="[^"]+"', "", item_str)
        # ET uses ns0/ns1 etc by default; convert to itunes
        item_str = item_str.replace("ns0:", "itunes:").replace(":ns0", ":itunes")
        body_parts.append("    " + item_str.strip())

    body = "\n".join(body_parts)
    footer = "\n  </channel>\n</rss>\n"
    # Fix &amp;amp; -> &amp; that we accidentally double-escaped above
    full = header + body + footer
    full = full.replace("&amp;amp;", "&amp;")
    return full

for season_num, (slug, display) in VOLUMES.items():
    items = by_season[season_num]
    feed_xml = build_feed(season_num, slug, display, items)
    out_path = os.path.join(REPO, f"{slug}.xml")
    with open(out_path, "w") as f:
        f.write(feed_xml)
    print(f"Wrote {out_path} — {len(feed_xml):,} bytes, {len(items)} episodes")
