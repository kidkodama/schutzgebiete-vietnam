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
            if w in da and ti and ti.lower() != n.lower(): aus[n] = ti
        time.sleep(1)
    print(" Wikipedia", sprache, len(aus))
    return aus
FAMILIEN = ["Typhlopidae","Gerrhopilidae","Xenopeltidae","Cylindrophiidae","Anomochilidae","Pythonidae","Boidae","Acrochordidae","Xenophidiidae","Xenodermidae","Pareidae","Viperidae","Homalopsidae","Lamprophiidae","Elapidae","Colubridae","Natricidae","Calamariidae","Dipsadidae","Psammophiidae","Sibynophiidae","Ahaetuliidae","Cyclocoridae"]
schluessel = []
for f in FAMILIEN:
    m = hole("/species/match", name=f, rank="FAMILY", **{"class": "Squamata"}) or {}
    if m.get("family") == f and m.get("usageKey"): schluessel.append(m["usageKey"])
    else: print(" Familie nicht gefunden:", f, m.get("matchType"))
print("Familien", len(schluessel))
GID = "rechteck"
GRUND = dict(taxonKey=schluessel, decimalLatitude="22.15,22.55", decimalLongitude="103.60,104.05", hasCoordinate="true", hasGeospatialIssue="false", occurrenceStatus="PRESENT")
antw = hole("/occurrence/search", **GRUND, limit=0, facet="speciesKey", facetLimit=1000)
zahlen = antw["facets"][0]["counts"] if antw["facets"] else []
print("Nachweise", antw["count"], "Artschlüssel", len(zahlen))
if not zahlen: sys.exit("ABBRUCH: keine Arten, Datei bleibt unverändert")
def art(c):
    k = int(c["name"]); s = hole(f"/species/{k}") or {}
    if s.get("rank") != "SPECIES": return None
    vn = (hole(f"/species/{k}/vernacularNames", limit=200) or {}).get("results", [])
    def nm(sprachen):
        z = collections.Counter(v["vernacularName"].strip() for v in vn if v.get("language") in sprachen and v.get("vernacularName"))
        return next((n for n, a in z.most_common(1) if a >= 2 and not n.isupper()), None)
    i = hole(f"/species/{k}/iucnRedListCategory") or {}
    return dict(k=k, sci=s.get("canonicalName") or s.get("species"), o=s.get("order"), f=s.get("family"), de=nm(("deu", "de")), en=nm(("eng", "en")), vi=nm(("vie", "vi")), iucn=i.get("category") or "NE", n=c["count"])
with ThreadPoolExecutor(6) as pool: arten = [a for a in pool.map(art, zahlen) if a and a["sci"]]
namen = [a["sci"] for a in arten]
for sprache in ("de", "en", "vi"):
    titel = wiki_titel(sprache, namen)
    for a in arten:
        if a["sci"] in titel: a[sprache] = titel[a["sci"]]
arten.sort(key=lambda a: -a["n"])
with open("sapa/daten/schlangen.json", "w", encoding="utf-8") as f:
    json.dump(dict(raum=GID, nachweise=antw["count"], stand=time.strftime("%Y-%m-%d"), arten=arten), f, ensure_ascii=False, separators=(",", ":"))
stellen = {}; geholt = 0
for start in range(0, antw["count"] + 300, 300):
    for o in hole("/occurrence/search", **GRUND, limit=300, offset=start).get("results", []):
        la, lo, k = o.get("decimalLatitude"), o.get("decimalLongitude"), o.get("speciesKey")
        if la is None or lo is None or not k: continue
        geholt += 1
        s = stellen.setdefault((round(la / .002), round(lo / .002)), dict(la=[], lo=[], arten=collections.Counter(), quellen=collections.Counter(), zuletzt={}))
        s["la"].append(la); s["lo"].append(lo); s["arten"][k] += 1
        s["quellen"][o.get("datasetName") or o.get("institutionCode") or "ohne Namen"] += 1
        d = (o.get("eventDate") or "")[:10]
        if d > s["zuletzt"].get(k, ""): s["zuletzt"][k] = d
aus = [dict(la=round(sum(s["la"]) / len(s["la"]), 5), lo=round(sum(s["lo"]) / len(s["lo"]), 5), n=len(s["la"]), a=[[k, z, s["zuletzt"].get(k, "")] for k, z in s["arten"].most_common()], q=[[q, z] for q, z in s["quellen"].most_common(5)]) for s in stellen.values()]
with open("sapa/daten/schlangen-sichtungen.json", "w", encoding="utf-8") as f:
    json.dump(dict(stand=time.strftime("%Y-%m-%d"), sichtungen=geholt, gesamt=antw["count"], stellen=aus), f, ensure_ascii=False, separators=(",", ":"))
print("Sichtungen", geholt, "von", antw["count"], "Stellen", len(aus))
print("Arten", len(arten))
for a in arten: print(" ", a["f"], "|", a["sci"], "|", a["de"], "|", a["en"], "|", a["vi"], "|", a["iucn"], a["n"])
