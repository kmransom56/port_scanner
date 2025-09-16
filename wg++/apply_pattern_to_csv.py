#!/usr/bin/env python3
import csv, sys, re, argparse
p = argparse.ArgumentParser()
p.add_argument('in_csv', nargs='?', default='mapping.csv')
p.add_argument('out_csv', nargs='?', default='mapping_with_pattern.csv')
p.add_argument('--template', '-t', default='http://example.local/stream/{id}', help='URL template, use {id}')
p.add_argument('--only-if-empty', action='store_true', help='Only replace when stream_url column is empty')
args = p.parse_args()
with open(args.in_csv, newline='', encoding='utf-8') as fh_in:
    rdr = csv.reader(fh_in)
    rows = list(rdr)
# detect header
start_idx = 0
has_header = False
if rows and any(h.lower().startswith('tvg-id') for h in rows[0]):
    has_header = True
    start_idx = 1
out_rows = []
if has_header:
    out_rows.append(['tvg-id','stream_url'])
for r in rows[start_idx:]:
    if not r:
        continue
    tid = r[0].strip()
    url = r[1].strip() if len(r) > 1 else ''
    if args.only_if_empty:
        if url:
            out_rows.append([tid, url])
            continue
    # apply template
    new_url = args.template.format(id=tid)
    out_rows.append([tid, new_url])
with open(args.out_csv, 'w', newline='', encoding='utf-8') as fh_out:
    w = csv.writer(fh_out)
    for row in out_rows:
        w.writerow(row)
print(f'Wrote {args.out_csv} ({len(out_rows)} rows)')
