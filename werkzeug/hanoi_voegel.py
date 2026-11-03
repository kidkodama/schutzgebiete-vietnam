#!/usr/bin/env python3
"""Holt alle in GBIF gemeldeten Vogelarten für Hanoi nach hanoi/daten/voegel.json.
Scheitert der Abruf, bleibt die vorhandene Datei stehen."""
import json, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
API = "https://api.gbif.org/v1"
def hole(pfad, **par):
    u = f"{API}{pfad}" + ("?" + urllib.parse.urlencode(par, doseq=True) if par else "")
    for v in range(5):
        try:
            q = urllib.request.Request(u, headers={"User-Agent": "hanoi-karte (github.com/kidkodama/schutzgebiete-vietnam)"})
            return json.load(urllib.request.urlopen(q, timeout=90))
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(3 * (v + 1))
        except Exception:
            time.sleep(3 * (v + 1))
    raise RuntimeError("nicht erreichbar: " + u)
GRUND = dict(classKey=212, hasCoordinate="true", hasGeospatialIssue="false", occurrenceStatus="PRESENT", limit=0)
RECHTECK = dict(decimalLatitude="20.55,21.40", decimalLongitude="105.25,106.05")
facette = hole("/occurrence/search", **GRUND, **RECHTECK, facet="gadmLevel1Gid", facetLimit=30)["facets"]
gid = None
for c in (facette[0]["counts"] if facette else []):
    g = hole("/geocode/gadm/" + c["name"]) or {}
    print(" Region", c["name"], g.get("name"), c["count"])
    if (g.get("name") or "").replace(" ", "").lower() in ("hànội", "hanoi", "hànoi"): gid = c["name"]
raum = dict(gadmGid=gid) if gid else RECHTECK
print("Raum:", raum)
antw = hole("/occurrence/search", **GRUND, **raum, facet="speciesKey", facetLimit=3000)
zahlen = antw["facets"][0]["counts"] if antw["facets"] else []
print("Nachweise", antw["count"], "Artschlüssel", len(zahlen))
if not zahlen: sys.exit("ABBRUCH: keine Arten, Datei bleibt unverändert")
def art(c):
    k = int(c["name"]); s = hole(f"/species/{k}") or {}
    if s.get("rank") != "SPECIES": return None
    vn = (hole(f"/species/{k}/vernacularNames", limit=200) or {}).get("results", [])
    def nm(sprachen):
        for v in vn:
            if v.get("language") in sprachen and v.get("vernacularName"): return v["vernacularName"]
    i = hole(f"/species/{k}/iucnRedListCategory") or {}
    return dict(k=k, sci=s.get("canonicalName") or s.get("species"), o=s.get("order"), f=s.get("family"),
                de=nm(("deu", "de")), en=nm(("eng", "en")), vi=nm(("vie", "vi")), iucn=i.get("category") or "NE", n=c["count"])
with ThreadPoolExecutor(8) as pool: arten = [a for a in pool.map(art, zahlen) if a and a["sci"]]
arten.sort(key=lambda a: -a["n"])
with open("hanoi/daten/voegel.json", "w", encoding="utf-8") as f:
    json.dump(dict(raum=gid or "rechteck", nachweise=antw["count"], stand=time.strftime("%Y-%m-%d"), arten=arten), f, ensure_ascii=False, separators=(",", ":"))
print("Arten", len(arten), "mit de", sum(1 for a in arten if a["de"]), "vi", sum(1 for a in arten if a["vi"]))
