#!/usr/bin/env python3
import sys, re, csv
src = sys.argv[1] if len(sys.argv) > 1 else "channels.m3u"
extinf_re = re.compile(r'#EXTINF:[^\n]*tvg-id="([^"]*)"[^\n]*tvg-name="([^"]*)"[^\n]*tvg-logo="([^"]*)",.*$')
# fallback simpler regex if attributes are in different order
alt_re = re.compile(r'#EXTINF:[^\n]*tvg-id="([^"]*)"[^\n]*,.*$')
with open(src, newline='', encoding='utf-8') as fh, open("channels.csv", "w", newline='', encoding='utf-8') as out:
    writer = csv.writer(out)
    writer.writerow(["tvg-id","name","logo"])
    for line in fh:
        line = line.rstrip("\r\n")
        if not line.startswith("#EXTINF"):
            continue
        m = extinf_re.match(line)
        if m:
            tid, name, logo = m.groups()
        else:
            m2 = alt_re.match(line)
            if m2:
                tid = m2.group(1)
                name = m2.group(2).split(",")[-1].strip() if len(m2.groups()) > 1 else ""
                logo = ""
            else:
                continue
        writer.writerow([tid, name, logo])
print("Wrote channels.csv (tvg-id,name,logo)")
