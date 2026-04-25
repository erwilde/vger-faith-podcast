#!/usr/bin/env python3
"""Generate Apple Podcasts-compatible RSS feed."""
import os
from datetime import datetime, timezone, timedelta
from xml.sax.saxutils import escape

REPO = "erwilde/vger-faith-podcast"
TAG = "v1.0"
FEED_HOST = "https://erwilde.github.io/vger-faith-podcast"
DOWNLOAD_BASE = f"https://github.com/{REPO}/releases/download/{TAG}"

def fmt_dur(seconds):
    s = int(round(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{sec:02d}"
    return f"{m:02d}:{sec:02d}"

# Episodes — chronological release order (oldest first; iTunes shows newest at top by pubDate)
# pubDate ordering: assign in chronological order so the newest podcast is at the top
EPISODES = [
    # (filename, title, description, duration_sec, size_bytes, pub_date, season, episode, season_title)
    ("temple-worship-prayer-circle.mp3",
     "Bonus — Ancient Temple Worship & the Prayer Circle",
     "A research-grounded exploration of ancient temple worship, the sacred prayer circle, and how the practice survived and was restored in the latter days. Includes ANE temple parallels, Qumran texts, and early Christian liturgical evidence.",
     1823.871020, 29183204,
     "2026-04-02T08:00:00Z", 0, 0, "Special Topics"),

    ("cfm-ep01-exodus14-sea-parts.mp3",
     "CFM Exodus EP01 — Exodus 14: The Sea Parts",
     "Deep dive into Israel's deliverance at the Red Sea. Egyptian historical context, the pillar of cloud and fire, the doctrine of standing still, and the typology of baptism in Christ.",
     3433.136327, 54931158,
     "2026-04-05T08:00:00Z", 1, 1, "Come Follow Me — Exodus"),

    ("cfm-ep02-exodus15-song-deliverance.mp3",
     "CFM Exodus EP02 — Exodus 15: The Song of Deliverance",
     "The Song of Moses and Miriam — Israel's first hymn of deliverance. Hebrew poetry, ancient Near Eastern parallels, and the prophetic foreshadowing of the Lamb in Revelation 15.",
     3626.060408, 58018204,
     "2026-04-08T08:00:00Z", 1, 2, "Come Follow Me — Exodus"),

    ("cfm-ep03-exodus16-bread-heaven.mp3",
     "CFM Exodus EP03 — Exodus 16: Bread from Heaven",
     "Manna in the wilderness. The daily-bread theology of dependence, the Sabbath revealed before Sinai, and the bread-of-life christology that runs from Exodus to John 6.",
     3453.387755, 55255075,
     "2026-04-11T08:00:00Z", 1, 3, "Come Follow Me — Exodus"),

    ("cfm-ep04-exodus17-18-water-war-wisdom.mp3",
     "CFM Exodus EP04 — Exodus 17–18: Water, War, and Wisdom",
     "Water from the rock at Massah and Meribah, the battle with Amalek and Aaron and Hur holding up Moses' hands, and Jethro's counsel on shared leadership — the foundations of priesthood organization.",
     3646.703673, 58348394,
     "2026-04-15T08:00:00Z", 1, 4, "Come Follow Me — Exodus"),

    ("cfm-ep05-exodus19-20-sinai.mp3",
     "CFM Exodus EP05 — Exodus 19–20: Sinai and the Ten Commandments",
     "Israel arrives at Sinai. The Lord's offer of a kingdom of priests, theophany on the mountain, and the Decalogue read in light of restoration scripture and ancient Near Eastern covenant forms.",
     3003.120000, 18018720,
     "2026-04-19T08:00:00Z", 1, 5, "Come Follow Me — Exodus"),

    ("cfm-ep06-exodus24-covenant.mp3",
     "CFM Exodus EP06 — Exodus 24: The Covenant Ratified",
     "The covenant ratification ceremony — blood at the altar, the elders ascending, eating and drinking before God on the mountain. The Old Testament prefigure of sacrament and temple.",
     3184.176000, 19105056,
     "2026-04-21T08:00:00Z", 1, 6, "Come Follow Me — Exodus"),

    ("cfm-ep07-exodus31-32-golden-calf.mp3",
     "CFM Exodus EP07 — Exodus 31–32: The Golden Calf Apostasy",
     "Israel's collapse into idolatry while Moses is on the mount. Aaron's failure of leadership, Moses' intercession, and the prophetic pattern of apostasy and restoration.",
     3400.488000, 20402928,
     "2026-04-22T08:00:00Z", 1, 7, "Come Follow Me — Exodus"),

    ("cfm-ep08-exodus33-34-face-to-face.mp3",
     "CFM Exodus EP08 — Exodus 33–34: Face to Face with the Glory of God",
     "Moses speaks with the Lord face to face as a man speaks with his friend. The cleft of the rock, the proclamation of the divine name, and the renewed tablets — the climax of the Sinai narrative.",
     3686.496000, 22118976,
     "2026-04-23T08:00:00Z", 1, 8, "Come Follow Me — Exodus"),

    ("sacred-markings-ep01-holiness-vestments-aaron.mp3",
     "Sacred Markings EP01 — Holiness to the LORD: The Vestments of Aaron",
     "The high priest's robe in Exodus 28 — ephod, breastplate, Urim and Thummim, the golden plate. What the embroidered marks meant and how they shaped every later sacred garment tradition.",
     3209.160000, 19254960,
     "2026-04-24T15:00:00Z", 2, 1, "Sacred Markings on Ancient Religious Clothing"),

    ("sacred-markings-ep02-nations-clothed-thread.mp3",
     "Sacred Markings EP02 — Nations Clothed in Thread: ANE, Qumran, and the Christian Seal",
     "Comparative survey across ancient Near Eastern, Qumran, Jewish, and early Christian sources. Tassels, fringes, sacred dyes, and the Christian sphragis — the seal placed on the body at baptism.",
     3428.760000, 20572560,
     "2026-04-24T16:00:00Z", 2, 2, "Sacred Markings on Ancient Religious Clothing"),

    ("sacred-markings-ep03-robe-of-glory-restored.mp3",
     "Sacred Markings EP03 — The Robe of Glory Restored: Christ to the Temple Today",
     "From the Hymn of the Pearl to the modern temple — how the robe-of-glory motif runs from early Christianity through the restoration. Concludes with Janet Ewell's 2026 Interpreter Foundation paper on gamma marks.",
     3491.928000, 20951568,
     "2026-04-24T17:00:00Z", 2, 3, "Sacred Markings on Ancient Religious Clothing"),

    ("sacred-markings-complete-with-bonus.mp3",
     "Sacred Markings Complete — Full Deep Dive Plus Interpreter Foundation Bonus",
     "All three Sacred Markings episodes concatenated into a single 3-hour deep dive, followed by a bonus segment integrating Janet Ewell's April 17, 2026 Interpreter Foundation paper, 'Gamma Marks: Recent Works Relevant to Their Study.'",
     10994.760000, 65968796,
     "2026-04-24T19:00:00Z", 2, 4, "Sacred Markings on Ancient Religious Clothing"),
]

now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

items_xml = []
for fname, title, desc, dur, size, pubdate_iso, season, episode_num, season_title in EPISODES:
    pub_dt = datetime.fromisoformat(pubdate_iso.replace("Z", "+00:00"))
    pub_rfc = pub_dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    url = f"{DOWNLOAD_BASE}/{fname}"
    guid = f"{REPO}-{TAG}-{fname}"
    season_xml = ""
    if season > 0:
        season_xml = f"<itunes:season>{season}</itunes:season>\n      <itunes:episode>{episode_num}</itunes:episode>"
    items_xml.append(f"""    <item>
      <title>{escape(title)}</title>
      <description>{escape(desc)}</description>
      <itunes:summary>{escape(desc)}</itunes:summary>
      <itunes:subtitle>{escape(season_title)}</itunes:subtitle>
      <pubDate>{pub_rfc}</pubDate>
      <enclosure url="{url}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{guid}</guid>
      <itunes:duration>{fmt_dur(dur)}</itunes:duration>
      <itunes:author>Eric Wilde</itunes:author>
      <itunes:explicit>false</itunes:explicit>
      {season_xml}
    </item>""")

items_combined = "\n".join(items_xml)

rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>V'Ger Faith — Eric's Scripture Study Podcast</title>
    <link>{FEED_HOST}</link>
    <atom:link href="{FEED_HOST}/feed.xml" rel="self" type="application/rss+xml"/>
    <language>en-us</language>
    <copyright>© 2026 Eric Wilde — Personal Use</copyright>
    <itunes:author>Eric Wilde</itunes:author>
    <itunes:summary>Personal scripture-study podcast feed for Dr. Eric Wilde. Deep dives into Come Follow Me readings (Old Testament 2026), temple worship, sacred history, and the long chain of witnesses across ancient and modern revelation. Produced privately for personal use; not affiliated with any church or institution.</itunes:summary>
    <description>Personal scripture-study podcast feed for Dr. Eric Wilde. Come Follow Me deep dives, temple worship, and the long chain of witnesses across ancient and modern revelation.</description>
    <itunes:owner>
      <itunes:name>Eric Wilde</itunes:name>
      <itunes:email>erwilde@telus.net</itunes:email>
    </itunes:owner>
    <itunes:image href="{FEED_HOST}/cover.jpg"/>
    <image>
      <url>{FEED_HOST}/cover.jpg</url>
      <title>V'Ger Faith — Eric's Scripture Study Podcast</title>
      <link>{FEED_HOST}</link>
    </image>
    <itunes:category text="Religion &amp; Spirituality">
      <itunes:category text="Christianity"/>
    </itunes:category>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    <lastBuildDate>{now}</lastBuildDate>
{items_combined}
  </channel>
</rss>
"""

out = "/Users/ericwilde/.gus/tmp/podcast-feed/vger-faith-podcast/feed.xml"
with open(out, "w") as f:
    f.write(rss)
print(f"Wrote {out} — {len(rss)} bytes, {len(EPISODES)} episodes")
