#!/usr/bin/env python3
"""Einmalige Abfrage: Geckos (Gekkonidae) um Tràng An und in ganz Ninh Bình aus GBIF."""
import json, urllib.parse, urllib.request
def hole(pfad, **p):
    u = "https://api.gbif.org/v1" + pfad + "?" + urllib.parse.urlencode(p, doseq=True)
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "ninhbinh-karte (github.com/kidkodama/schutzgebiete-vietnam)"}), timeout=60))
fam = hole("/species/match", name="Gekkonidae", rank="FAMILY", strict="true")["usageKey"]
for titel, la, lo in [("TRANG AN (20,15-20,35 N, 105,80-106,00 O)", "20.15,20.35", "105.80,106.00"), ("GANZ NINH BINH-KARTE", "20.18,20.43", "105.43,105.97")]:
    a = hole("/occurrence/search", taxonKey=fam, decimalLatitude=la, decimalLongitude=lo, occurrenceStatus="PRESENT", limit=0, facet="speciesKey", facetLimit=100)
    print("==", titel, "Nachweise:", a["count"])
    for c in a["facets"][0]["counts"] if a["facets"] else []:
        s = hole(f"/species/{c['name']}")
        vn = [v["vernacularName"] for v in hole(f"/species/{c['name']}/vernacularNames", limit=100).get("results", []) if v.get("language") in ("eng", "deu")][:3]
        neu = hole("/occurrence/search", taxonKey=c["name"], decimalLatitude=la, decimalLongitude=lo, limit=1, occurrenceStatus="PRESENT")["results"]
        print(f"  {c['count']:4d} | {s.get('canonicalName')} | {', '.join(vn)} | zuletzt {neu[0].get('eventDate','?')[:10] if neu else '?'} | {neu[0].get('datasetName','') if neu else ''}")
