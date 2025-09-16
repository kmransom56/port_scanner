#!/usr/bin/env python3
import sys, re, argparse
p = argparse.ArgumentParser()
p.add_argument("channels_m3u", nargs='?', default="channels.m3u")
p.add_argument("out_m3u", nargs='?', default="channels_placeholder.m3u")
p.add_argument("--template", default="http://localhost/stream/{id}", help="Template for placeholders; use {id}")
args = p.parse_args()
extinf_re = re.compile(r'#EXTINF:[^\n]*tvg-id="([^"]*)"', re.IGNORECASE)
with open(args.channels_m3u, encoding='utf-8') as inp, open(args.out_m3u, "w", encoding='utf-8') as out:
    for line in inp:
        out.write(line)
        if line.startswith("#EXTINF"):
            m = extinf_re.search(line)
            tid = m.group(1) if m else "unknown"
            out.write(args.template.format(id=tid) + "\n")
print(f"Wrote {args.out_m3u}")
