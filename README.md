# HNN XMLTV

XMLTV guide for the **Watch HNN Live** stream (Hawaii News Now, KHNL):

```
https://live-streaming-mcdn.api.graylive.quickplay.com/khnl-xos1-input-1/khnl-xos1-input-1-v4.isml/khnl-xos1-input-1-v4.m3u8
```

`hnn.xml` is rebuilt every 6 hours by GitHub Actions from Gray's public schedule feed
(the one hawaiinewsnow.com/livestream uses for "On Now / Next"). It covers about 7 days ahead.
Channel id is `2001`; change `--channel-id` in `.github/workflows/update.yml` to match your M3U `tvg-id`.

Run locally: `python hnn_xmltv.py --days 7 --channel-id 2001 --out hnn.xml`
