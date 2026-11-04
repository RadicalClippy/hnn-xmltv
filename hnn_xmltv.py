"""Build an XMLTV guide for the "Watch HNN Live" stream (khnl-xos1-input-1).

Pulls the schedule from Gray's public EPG feed (the one hawaiinewsnow.com/livestream
uses for "On Now / Next") and writes hnn.xml.

Usage:  python hnn_xmltv.py [--days 7] [--channel-id 2001] [--out hnn.xml]
Re-run it daily (cron / Task Scheduler) to keep the guide current.
"""
import argparse
import json
import urllib.request
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape, quoteattr

FEED = ("https://data-store-cdn.api.graycms.quickplay.com/content/epglite"
        "?reg=us&dt=web&client=gray-gm-web&prop=gm%7Ckhnl%7Ckhnl&start={start}&end={end}")
SOURCE_CHANNEL = "khnl_xos1_input_1"  # "Watch HNN Live" = khnl-xos1-input-1 m3u8
LOGO = ("https://image-resizer-cloud-cdn.api.graycms.quickplay.com/image/"
        "9A86A052-6EA7-459F-BBF1-895477233914/0-16x9.jpg?width=250")


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def parse(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def xmltv_time(dt):
    return dt.strftime("%Y%m%d%H%M%S +0000")


def fetch(start, end):
    req = urllib.request.Request(FEED.format(start=iso(start), end=iso(end)),
                                 headers={"User-Agent": "hnn-xmltv/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    for ch in data.get("data", []):
        airings = ch.get("airing") or []
        if airings and airings[0]["ch"]["cs"] == SOURCE_CHANNEL:
            return airings
    return []


def collect(days):
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start, stop = now - timedelta(hours=2), now + timedelta(days=days)
    seen = {}
    while start < stop:
        airings = fetch(start, stop)
        if not airings:
            break
        for a in airings:
            seen[a["id"]] = a
        last_end = max(parse(a["sc_ed_dt"]) for a in airings)
        if last_end <= start:  # no progress; avoid an endless loop
            break
        start = last_end
    return sorted(seen.values(), key=lambda a: a["sc_st_dt"])


def text(pgm, key):
    vals = pgm.get(key) or []
    return vals[0]["n"].strip() if vals and vals[0].get("n") else ""


def build(airings, channel_id):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<tv generator-info-name="hnn_xmltv.py">',
           f'  <channel id={quoteattr(channel_id)}>',
           '    <display-name>Hawaii News Now</display-name>',
           '    <display-name>Watch HNN Live</display-name>',
           f'    <icon src={quoteattr(LOGO)} />',
           '  </channel>']
    for a in airings:
        pgm = a.get("pgm", {})
        title = text(pgm, "lon") or "Hawaii News Now"
        desc = text(pgm, "lod")
        out.append(f'  <programme start="{xmltv_time(parse(a["sc_st_dt"]))}" '
                   f'stop="{xmltv_time(parse(a["sc_ed_dt"]))}" channel={quoteattr(channel_id)}>')
        out.append(f'    <title lang="en">{escape(title)}</title>')
        if desc and desc != title:
            out.append(f'    <desc lang="en">{escape(desc)}</desc>')
        out.append('    <category lang="en">News</category>')
        img = (pgm.get("ex_ia") or [{}])[0].get("u")
        if img:
            out.append(f'    <icon src={quoteattr(img)} />')
        out.append('  </programme>')
    out.append('</tv>')
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--channel-id", default="2001",
                    help="must match tvg-id in your M3U (NostalgiaTV lineup uses 2001)")
    ap.add_argument("--out", default="hnn.xml")
    args = ap.parse_args()
    airings = collect(args.days)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(build(airings, args.channel_id))
    if airings:
        print(f"Wrote {len(airings)} programmes to {args.out} "
              f"({airings[0]['sc_st_dt']} .. {airings[-1]['sc_ed_dt']})")
    else:
        print(f"No schedule data returned; wrote empty guide to {args.out}")


if __name__ == "__main__":
    main()
