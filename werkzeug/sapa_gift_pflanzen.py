#!/usr/bin/env python3
"""Holt die in GBIF gemeldeten Schlangenarten für Sa Pa nach sapa/daten/schlangen*.json.
Scheitert der Abruf, bleibt die vorhandene Datei stehen."""
import collections, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
API = "https://api.gbif.org/v1"
def hole(pfad, **par):
    u = f"{API}{pfad}" + ("?" + urllib.parse.urlencode(par, doseq=True) if par else "")
    for v in range(5):
        try:
            q = urllib.request.Request(u, headers={"User-Agent": "sapa-karte (github.com/kidkodama/schutzgebiete-vietnam)"})
            return json.load(urllib.request.urlopen(q, timeout=90))
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            time.sleep(3 * (v + 1))
        except Exception:
            time.sleep(3 * (v + 1))
    raise RuntimeError("nicht erreichbar: " + u)
def wiki_titel(sprache, namen):
    """Wissenschaftlicher Name -> Artikeltitel. Wikipedia leitet auf den üblichen Namen um. 50 Namen je Abfrage."""
    aus = {}
    for i in range(0, len(namen), 50):
        teil = namen[i:i + 50]
        u = f"https://{sprache}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(dict(action="query", titles="|".join(teil), redirects=1, format="json", formatversion=2))
        for v in range(5):
            try:
                q = urllib.request.Request(u, headers={"User-Agent": "sapa-karte (github.com/kidkodama/schutzgebiete-vietnam)"})
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
            # Titel, die mit dem Gattungsnamen beginnen, sind keine Trivialnamen (z. B. Umleitung auf Nachbarart)
            if w in da and ti and ti.lower() != n.lower() and ti.split()[0].lower() != n.split()[0].lower(): aus[n] = ti
        time.sleep(1)
    print(" Wikipedia", sprache, len(aus))
    return aus
RAUM = dict(decimalLatitude="22.15,22.55", decimalLongitude="103.60,104.05", hasCoordinate="true", hasGeospatialIssue="false", occurrenceStatus="PRESENT")
def schluessel(name, rang):
    m = hole("/species/match", name=name, rank=rang, strict="true") or {}
    if m.get("usageKey") and m.get("matchType") == "EXACT" and m.get("rank") == rang: return m["usageKey"]
    sys.exit(f"ABBRUCH: {name} ({rang}) nicht eindeutig: {m.get('matchType')} {m.get('rank')}")
def art(c):
    k = int(c["name"]); s = hole(f"/species/{k}") or {}
    if s.get("rank") != "SPECIES": return None
    vn = (hole(f"/species/{k}/vernacularNames", limit=200) or {}).get("results", [])
    def nm(sprachen):
        z = collections.Counter(v["vernacularName"].strip() for v in vn if v.get("language") in sprachen and v.get("vernacularName"))
        return next((n for n, a in z.most_common(1) if a >= 2 and not n.isupper()), None)
    i = hole(f"/species/{k}/iucnRedListCategory") or {}
    return dict(k=k, sci=s.get("canonicalName") or s.get("species"), p=s.get("phylum"), c=s.get("class"), o=s.get("order"), f=s.get("family"), g=s.get("genus"),
                de=nm(("deu", "de")), en=nm(("eng", "en")), vi=nm(("vie", "vi")), iucn=i.get("category") or "NE", n=c["count"])
def arten_fuer(schl, grenze):
    antw = hole("/occurrence/search", taxonKey=schl, **RAUM, limit=0, facet="speciesKey", facetLimit=grenze)
    zahlen = antw["facets"][0]["counts"] if antw["facets"] else []
    with ThreadPoolExecutor(8) as pool: aus = [a for a in pool.map(art, zahlen) if a and a["sci"]]
    return aus, antw["count"]
def namen(arten):
    n = [a["sci"] for a in arten]
    for sprache in ("de", "en", "vi"):
        titel = wiki_titel(sprache, n)
        for a in arten:
            if a["sci"] in titel: a[sprache] = titel[a["sci"]]
GRUPPEN = [
 ("schlangen", [("Elapidae", "FAMILY"), ("Viperidae", "FAMILY"), ("Rhabdophis", "GENUS")]),
 ("hornissen", [("Vespa", "GENUS")]),
 ("bienen", [("Apis", "GENUS")]),
 ("skorpione", [("Scorpiones", "ORDER")]),
 ("hundertfuesser", [("Scolopendromorpha", "ORDER")]),
 ("raupen", [("Limacodidae", "FAMILY")]),
 ("spinnen", [("Theraphosidae", "FAMILY"), ("Latrodectus", "GENUS")]),
 ("kaefer", [("Paederus", "GENUS"), ("Meloidae", "FAMILY")]),
 ("amphibien", [("Bufonidae", "FAMILY"), ("Tylototriton", "GENUS")]),
]
gift = []
for gid, taxa in GRUPPEN:
    schl = [schluessel(n, r) for n, r in taxa]
    a, n = arten_fuer(schl, 300)
    print("Gruppe", gid, "Arten", len(a), "Nachweise", n)
    for x in a: x["gruppe"] = gid
    gift += a
namen(gift); gift.sort(key=lambda a: -a["n"])
with open("sapa/daten/gifttiere.json", "w", encoding="utf-8") as f:
    json.dump(dict(stand=time.strftime("%Y-%m-%d"), arten=gift), f, ensure_ascii=False, separators=(",", ":"))
pfl, n = arten_fuer([6], 6000)
print("Pflanzen", len(pfl), "Nachweise", n)
namen(pfl); pfl.sort(key=lambda a: -a["n"])
with open("sapa/daten/pflanzen.json", "w", encoding="utf-8") as f:
    json.dump(dict(stand=time.strftime("%Y-%m-%d"), nachweise=n, arten=pfl), f, ensure_ascii=False, separators=(",", ":"))
for a in gift: print(" ", a["gruppe"], "|", a["sci"], "|", a["de"], "|", a["en"], "|", a["n"])
