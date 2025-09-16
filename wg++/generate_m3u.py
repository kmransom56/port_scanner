#!/usr/bin/python
# Usage: ./generate_m3u.py [epg_file.gz] > channels.m3u
import sys, gzip, xml.etree.ElementTree as ET

fpath = sys.argv[1] if len(sys.argv) > 1 else "epg_ripper_ALL_SOURCES1.xml.gz"

def local(tag): return tag.rsplit("}",1)[-1] if "}" in tag else tag

def find_display_name(elem):
	for c in elem:
		if local(c.tag) == "display-name":
			return (c.text or "").strip()
	return ""

with gzip.open(fpath, "rb") as fh:
	print("#EXTM3U")
	for event, elem in ET.iterparse(fh, events=("end",)):
		if local(elem.tag) == "channel":
			cid = elem.get("id","")
			name = find_display_name(elem) or cid
			logo = ""
			for c in elem:
				if local(c.tag) == "icon":
					logo = c.get("src","") or ""
					break
			# sanitize quotes
			name_s = name.replace('"', "'")
			logo_s = (logo or "").replace('"', "'")
			print(f'#EXTINF:-1 tvg-id="{cid}" tvg-name="{name_s}" tvg-logo="{logo_s}",{name_s}')
			elem.clear()