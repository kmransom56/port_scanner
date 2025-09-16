#!/usr/bin/env python3
import sys, csv, re, argparse
p = argparse.ArgumentParser()
p.add_argument("channels_m3u", nargs='?', default="channels.m3u")
p.add_argument("mapping_csv", nargs='?', default="mapping.csv")
p.add_argument("out_m3u", nargs='?', default="channels_with_urls.m3u")
p.add_argument("--placeholder", help="URL template, use {id} for tvg-id (e.g. http://host/stream/{id})")
args = p.parse_args()
# load mapping CSV (tvg-id,url). Accept header or plain rows. Skip blank lines & comments (#).
mapping = {}
try:
    with open(args.mapping_csv, newline='', encoding='utf-8') as fh:
        rdr = csv.reader(fh)
        for row in rdr:
            if not row:
                continue
            if row[0].strip().startswith("#"):
                continue
            if len(row) < 2:
                continue
            tid = row[0].strip()
            url = row[1].strip()
            if tid and url:
                mapping[tid] = url
except FileNotFoundError:
    mapping = {}
extinf_re = re.compile(r'#EXTINF:[^\n]*tvg-id="([^"]*)"[^\n]*', re.IGNORECASE)
with open(args.channels_m3u, encoding='utf-8') as inp, open(args.out_m3u, "w", encoding='utf-8') as out:
    for line in inp:
        out.write(line)
        if line.startswith("#EXTINF"):
            m = extinf_re.search(line)
            tid = m.group(1) if m else ""
            url = mapping.get(tid)
            if url:
                out.write(url.rstrip() + "\n")
            elif args.placeholder:
                out.write(args.placeholder.format(id=tid) + "\n")
            else:
                out.write(f"#NO-URL for {tid}\n")
print(f"Wrote {args.out_m3u} (mapped: {sum(1 for v in mapping)} mappings)")
