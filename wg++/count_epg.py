#!/usr/bin/python
Usage: ./count_epg.py [epg_file.gz]
import sys, gzip, xml.etree.ElementTree as ET

fpath = sys.argv[1] if len(sys.argv) > 1 else "epg_ripper_ALL_SOURCES1.xml.gz"
chans = 0
progs = 0
def local(tag): return tag.rsplit("}",1)[-1] if "}" in tag else tag

with gzip.open(fpath, "rb") as fh:
# iterparse on binary file object
for event, elem in ET.iterparse(fh, events=("end",)):
t = local(elem.tag)
if t == "channel":
chans += 1
elem.clear()
elif t == "programme":
progs += 1
elem.clear()

print("File:", fpath)
print("Channels:", chans)
print("Programmes:", progs)