#!/usr/bin/env python3
import csv, re, sys
# Reads mapping.csv (header or not) and channels.m3u to filter by keywords into multiple csvs
mapping_in = sys.argv[1] if len(sys.argv) > 1 else 'mapping.csv'
channels_m3u = sys.argv[2] if len(sys.argv) > 2 else 'channels.m3u'
# Output files
outs = {
    'us': 'mapping_us.csv',
    'uk': 'mapping_uk.csv',
    'ca': 'mapping_ca.csv',
    'eu': 'mapping_eu.csv',
    'motorsport': 'mapping_motorsport.csv'
}
# Patterns (lowercase) to match in tvg-id or display name
pat_us = re.compile(r'(espn|foxsports|nbc|nbcsn|cbssports|accntv|tbs|cbs|abc|nbc|fox)', re.I)
pat_uk = re.compile(r'(sky|bbc|itv|channel 4|channel 5|sky sports|bbc sport|bt sport)', re.I)
pat_ca = re.compile(r'(sportsnet|tsn|cbc|ctv|rds)', re.I)
pat_eu = re.compile(r'(eurosport|sport|tv|rtv|canal+|beIN|sport1|sport2|rtl)', re.I)
pat_moto = re.compile(r'(racingtv|lemans|leman|gtworld|formulae|bike|motocross|karting|touringcar|hillclimb|motorvision|motorsport)', re.I)
# load channels display names by tvg-id
display = {}
with open(channels_m3u, encoding='utf-8') as fh:
    for line in fh:
        if line.startswith('#EXTINF'):
            # attempt to extract tvg-id and display name
            m = re.search(r'tvg-id="([^"]*)"', line)
            d = re.search(r',\s*(.*)$', line)
            if m:
                tid = m.group(1)
                name = d.group(1).strip() if d else ''
                display[tid] = name.lower()
# read mapping header and rows
rows = []
with open(mapping_in, newline='', encoding='utf-8') as fh:
    rdr = csv.reader(fh)
    hdr = next(rdr)
    # detect if header contains 'tvg-id' else treat first as data
    if 'tvg-id' not in [h.lower() for h in hdr]:
        # first row is data
        fh.seek(0)
        rdr = csv.reader(fh)
    for r in rdr:
        if not r or r[0].strip().startswith('#'):
            continue
        rows.append(r)
# prepare writers
writers = {}
files = {}
for k, fname in outs.items():
    f = open(fname, 'w', newline='', encoding='utf-8')
    files[k] = f
    writers[k] = csv.writer(f)
    writers[k].writerow(['tvg-id','stream_url'])
# filter rows
for r in rows:
    tid = r[0].strip()
    url = r[1].strip() if len(r) > 1 else ''
    name = display.get(tid, '')
    text = (tid + ' ' + name).lower()
    if pat_moto.search(text):
        writers['motorsport'].writerow([tid, url])
    if pat_us.search(text):
        writers['us'].writerow([tid, url])
    if pat_uk.search(text):
        writers['uk'].writerow([tid, url])
    if pat_ca.search(text):
        writers['ca'].writerow([tid, url])
    if pat_eu.search(text):
        writers['eu'].writerow([tid, url])
# close
for f in files.values():
    f.close()
print('Wrote region mapping files: ' + ', '.join(outs.values()))
