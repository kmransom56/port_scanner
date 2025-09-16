#!/usr/bin/env python3
import sys, re, csv
src = sys.argv[1] if len(sys.argv) > 1 else "channels.m3u"
outfile = sys.argv[2] if len(sys.argv) > 2 else "mapping.csv"
template = sys.argv[3] if len(sys.argv) > 3 else "http://localhost/stream/{id}"
extinf_re = re.compile(r'#EXTINF:[^\n]*tvg-id="([^"]*)"', re.IGNORECASE)
with open(src, encoding='utf-8') as inp, open(outfile, "w", newline='', encoding='utf-8') as out:
    writer = csv.writer(out)
    writer.writerow(["tvg-id","stream_url"])
    for line in inp:
        if line.startswith("#EXTINF"):
            m = extinf_re.search(line)
            tid = m.group(1) if m else ""
            if tid:
                url = template.format(id=tid)
                writer.writerow([tid, url])
print(f"Wrote mapping template to {outfile}")
