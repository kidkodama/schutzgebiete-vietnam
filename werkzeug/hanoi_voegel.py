#!/usr/bin/env python3
"""Holt alle in GBIF gemeldeten Vogelarten für Hanoi nach hanoi/daten/voegel.json.
Scheitert der Abruf, bleibt die vorhandene Datei stehen."""
import collections, json, re, sys, time, urllib.error, urllib.parse, urllib.request
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
def wiki_titel(sprache, namen):
    """Wissenschaftlicher Name -> Artikeltitel. Wikipedia leitet auf den üblichen Namen um. 50 Namen je Abfrage."""
    aus = {}
    for i in range(0, len(namen), 50):
        teil = namen[i:i + 50]
        u = f"https://{sprache}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(dict(action="query", titles="|".join(teil), redirects=1, format="json", formatversion=2))
        for v in range(5):
            try:
                q = urllib.request.Request(u, headers={"User-Agent": "hanoi-karte (github.com/kidkodama/schutzgebiete-vietnam)"})
                j = json.load(urllib.request.urlopen(q, timeout=60))["query"]; break
            except Exception as e:
                print(" wiki", sprache, e); time.sleep(10 * (v + 1)); j = {}
        um = {n: n for n in teil}
        for x in j.get("normalized", []):
            for k, w in um.items():
                if w == x["from"]: um[k] = x["to"]
        for x in j.get("redirects", []):
            for k, w in um.items():
                if w == x["from"]: um[k] = x["to"]
        da = {s["title"] for s in j.get("pages", []) if not s.get("missing") and not s.get("invalid")}
        for n, w in um.items():
            ti = re.sub(r"\s*\(.*\)$", "", w).strip()
            if w in da and ti and ti.lower() != n.lower(): aus[n] = ti
        time.sleep(1)
    print(" Wikipedia", sprache, len(aus))
    return aus
def art(c):
    k = int(c["name"]); s = hole(f"/species/{k}") or {}
    if s.get("rank") != "SPECIES": return None
    vn = (hole(f"/species/{k}/vernacularNames", limit=200) or {}).get("results", [])
    def nm(sprachen):
        """GBIF enthält auch falsche Namen (z. B. Eisvogel als Blauspecht): nur, was mindestens zwei Quellen gleich nennen."""
        z = collections.Counter(v["vernacularName"].strip() for v in vn if v.get("language") in sprachen and v.get("vernacularName"))
        return next((n for n, a in z.most_common(1) if a >= 2 and not n.isupper()), None)
    sci = s.get("canonicalName") or s.get("species")
    i = hole(f"/species/{k}/iucnRedListCategory") or {}
    return dict(k=k, sci=sci, o=s.get("order"), f=s.get("family"),
                de=nm(("deu", "de")), en=nm(("eng", "en")), vi=nm(("vie", "vi")), iucn=i.get("category") or "NE", n=c["count"])
with ThreadPoolExecutor(8) as pool: arten = [a for a in pool.map(art, zahlen) if a and a["sci"]]
namen = [a["sci"] for a in arten]
for sprache in ("de", "en", "vi"):
    titel = wiki_titel(sprache, namen)
    for a in arten:
        if a["sci"] in titel: a[sprache] = titel[a["sci"]]
arten.sort(key=lambda a: -a["n"])
with open("hanoi/daten/voegel.json", "w", encoding="utf-8") as f:
    json.dump(dict(raum=gid or "rechteck", nachweise=antw["count"], stand=time.strftime("%Y-%m-%d"), arten=arten), f, ensure_ascii=False, separators=(",", ":"))
print("Arten", len(arten), "mit de", sum(1 for a in arten if a["de"]), "vi", sum(1 for a in arten if a["vi"]))
