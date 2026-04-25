#!/usr/bin/env python3
"""Generate scripture audio podcast feed pointing at Church CDN."""
import os
import re
from datetime import datetime, timezone, timedelta
from xml.sax.saxutils import escape

FEED_HOST = "https://erwilde.github.io/vger-faith-podcast"
DURATION_DIR = "/Users/ericwilde/vger/data/scripture-audio/durations"

# Map volume slug -> (CDN path, season number, season title, display name)
VOLUMES = [
    ("old-testament", "the-old-testament", 1, "Old Testament", "Old Testament"),
    ("new-testament", "the-new-testament", 2, "New Testament", "New Testament"),
    ("book-of-mormon", "the-book-of-mormon-another-testament-of-jesus-christ", 3, "Book of Mormon", "Book of Mormon"),
    ("doctrine-and-covenants", "the-doctrine-and-covenants", 4, "Doctrine and Covenants", "Doctrine and Covenants"),
    ("pearl-of-great-price", "the-pearl-of-great-price", 5, "Pearl of Great Price", "Pearl of Great Price"),
]

def fmt_dur(seconds):
    s = int(round(float(seconds)))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"

def humanize_title(filename, vol_display):
    """Turn '2015-11-0010-genesis-01-male-voice-64k-eng.mp3' into 'Genesis 1'."""
    # Strip prefix and suffix
    base = filename
    base = re.sub(r"^\d{4}-\d{2}-\d{4}-", "", base)
    base = re.sub(r"-male-voice-64k-eng\.mp3$", "", base)
    # Now we have something like 'genesis-01' or '1-nephi-05' or 'section-89' or 'official-declaration-1'
    parts = base.split("-")
    # Detect trailing zero-padded chapter number
    if parts and re.match(r"^\d+$", parts[-1]):
        chap = int(parts[-1])
        book = "-".join(parts[:-1])
        # Special handling for single-chapter books that shouldn't get " 1"
        SINGLE_CHAPTER = {"words-of-mormon", "obadiah", "philemon", "2-john", "3-john", "jude"}
        if book in SINGLE_CHAPTER and chap == 1:
            return titlecase_book(book)
        # Special handling for "official-declaration-N" — number is part of identity
        if book == "official-declaration":
            return f"Official Declaration {chap}"
        return f"{titlecase_book(book)} {chap}"
    return titlecase_book(base)

def titlecase_book(s):
    """Title-case a book name with Roman-numeral and special handling."""
    if not s:
        return s
    # Special hand-mappings
    SPECIAL = {
        "1-nephi": "1 Nephi",
        "2-nephi": "2 Nephi",
        "jacob": "Jacob",
        "enos": "Enos",
        "jarom": "Jarom",
        "omni": "Omni",
        "words-of-mormon": "Words of Mormon",
        "mosiah": "Mosiah",
        "alma": "Alma",
        "helaman": "Helaman",
        "3-nephi": "3 Nephi",
        "4-nephi": "4 Nephi",
        "mormon": "Mormon",
        "ether": "Ether",
        "moroni": "Moroni",
        "title-page": "Title Page",
        "traditional-title-page": "Traditional Title Page",
        "introduction": "Introduction",
        "testimony-of-three-witnesses": "Testimony of Three Witnesses",
        "testimony-of-eight-witnesses": "Testimony of Eight Witnesses",
        "testimony-of-the-prophet-joseph-smith": "Testimony of the Prophet Joseph Smith",
        "brief-explanation-about-the-book-of-mormon": "Brief Explanation about the Book of Mormon",
        "old-testament-title-page": "Old Testament Title Page",
        "new-testament-title-page": "New Testament Title Page",
        "epistle-dedicatory": "Epistle Dedicatory",
        "section": "Section",
        "official-declaration-1": "Official Declaration 1",
        "official-declaration-2": "Official Declaration 2",
        "introduction-testimony-of-the-twelve-apostles": "Introduction — Testimony of the Twelve Apostles",
        "title": "Title",
        "introductory-note": "Introductory Note",
        "joseph-smith-matthew": "Joseph Smith—Matthew",
        "joseph-smith-history": "Joseph Smith—History",
        "the-articles-of-faith": "The Articles of Faith",
        "song-of-solomon": "Song of Solomon",
        "1-samuel": "1 Samuel",
        "2-samuel": "2 Samuel",
        "1-kings": "1 Kings",
        "2-kings": "2 Kings",
        "1-chronicles": "1 Chronicles",
        "2-chronicles": "2 Chronicles",
        "1-corinthians": "1 Corinthians",
        "2-corinthians": "2 Corinthians",
        "1-thessalonians": "1 Thessalonians",
        "2-thessalonians": "2 Thessalonians",
        "1-timothy": "1 Timothy",
        "2-timothy": "2 Timothy",
        "1-peter": "1 Peter",
        "2-peter": "2 Peter",
        "1-john": "1 John",
        "2-john": "2 John",
        "3-john": "3 John",
    }
    if s in SPECIAL:
        return SPECIAL[s]
    # Default: capitalize each word
    return " ".join(w.capitalize() for w in s.split("-"))

# Build episode list
episodes = []  # (volume_slug, cdn_path, filename, title, duration, size, season, episode_num, vol_display)
for slug, cdn_path, season, season_title, vol_display in VOLUMES:
    tsv = f"{DURATION_DIR}/{slug}.tsv"
    with open(tsv) as f:
        rows = [line.rstrip("\n").split("\t") for line in f if line.strip()]
    # rows: [duration, size, filename]
    for ep_num, (dur, size, fname) in enumerate(rows, start=1):
        title = humanize_title(fname, vol_display)
        episodes.append((slug, cdn_path, fname, title, float(dur), int(size), season, ep_num, season_title))

print(f"Total episodes: {len(episodes)}")

# Build XML items — pubDate spreads across history so episodes order properly
# Use 2015-11-01 as the "release" base, increment by 1 minute per episode
base_date = datetime(2015, 11, 1, 12, 0, 0, tzinfo=timezone.utc)
items_xml = []
for i, (slug, cdn_path, fname, title, dur, size, season, ep_num, season_title) in enumerate(episodes):
    pub_dt = base_date + timedelta(minutes=i)
    pub_rfc = pub_dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    cdn_url = f"https://media2.ldscdn.org/assets/scriptures/{cdn_path}/{fname}"
    guid = f"lds-scripture-audio-{slug}-{fname}"
    items_xml.append(f"""    <item>
      <title>{escape(title)}</title>
      <description>{escape(season_title)} — {escape(title)}. Read aloud from the official audio recording of The Church of Jesus Christ of Latter-day Saints.</description>
      <itunes:summary>{escape(season_title)} — {escape(title)}</itunes:summary>
      <itunes:subtitle>{escape(season_title)}</itunes:subtitle>
      <pubDate>{pub_rfc}</pubDate>
      <enclosure url="{cdn_url}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{guid}</guid>
      <itunes:duration>{fmt_dur(dur)}</itunes:duration>
      <itunes:author>The Church of Jesus Christ of Latter-day Saints</itunes:author>
      <itunes:explicit>false</itunes:explicit>
      <itunes:season>{season}</itunes:season>
      <itunes:episode>{ep_num}</itunes:episode>
    </item>""")

now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
items_combined = "\n".join(items_xml)

rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>LDS Scriptures — Audio (Eric's Private Feed)</title>
    <link>{FEED_HOST}</link>
    <atom:link href="{FEED_HOST}/scriptures.xml" rel="self" type="application/rss+xml"/>
    <language>en-us</language>
    <copyright>© Intellectual Reserve, Inc. — Personal Use</copyright>
    <itunes:author>The Church of Jesus Christ of Latter-day Saints</itunes:author>
    <itunes:summary>Personal feed for Eric Wilde — official chapter-by-chapter audio of the standard works (Old Testament, New Testament, Book of Mormon, Doctrine and Covenants, Pearl of Great Price), streamed from the Church's CDN. Organized as seasons: 1=OT, 2=NT, 3=BoM, 4=D&amp;C, 5=PoGP. Audio © Intellectual Reserve, Inc.; for personal study.</itunes:summary>
    <description>Chapter-by-chapter audio of the LDS standard works, streamed from the official Church CDN. Personal use only.</description>
    <itunes:owner>
      <itunes:name>Eric Wilde</itunes:name>
      <itunes:email>erwilde@telus.net</itunes:email>
    </itunes:owner>
    <itunes:image href="{FEED_HOST}/scriptures-cover.jpg"/>
    <image>
      <url>{FEED_HOST}/scriptures-cover.jpg</url>
      <title>LDS Scriptures — Audio</title>
      <link>{FEED_HOST}</link>
    </image>
    <itunes:category text="Religion &amp; Spirituality">
      <itunes:category text="Christianity"/>
    </itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>serial</itunes:type>
    <lastBuildDate>{now}</lastBuildDate>
{items_combined}
  </channel>
</rss>
"""

out = "/Users/ericwilde/.gus/tmp/podcast-feed/vger-faith-podcast/scriptures.xml"
with open(out, "w") as f:
    f.write(rss)
print(f"Wrote {out} — {len(rss)} bytes, {len(episodes)} episodes")
