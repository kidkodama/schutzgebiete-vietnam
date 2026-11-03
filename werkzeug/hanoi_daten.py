#!/usr/bin/env python3
"""Holt die OpenStreetMap-Daten der Hanoi-Karte und legt sie als Dateien ab.
Bricht nie vorhandene Daten ab: scheitert ein Teil, bleibt die alte Datei stehen."""
import json, sys, time, urllib.parse, urllib.request
SERVER = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
          "https://overpass.private.coffee/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
G = "20.55,105.25,21.40,106.05"; K = "20.85,105.60,21.20,106.05"
TEILE = {
 "natur": f'(nwr["leisure"~"^(park|garden|nature_reserve)$"]["name"]({G});nwr["tourism"="zoo"]["name"]({G});nwr["natural"="water"]["name"]({G}););out geom;',
 "strassen": f'way["highway"~"^(motorway|trunk|primary)$"]({K});out tags geom;',
 "orte-sehen": f'(nwr["tourism"~"^(museum|attraction|viewpoint|gallery)$"]["name"]({G});nwr["historic"]["name"]({G});nwr["amenity"="place_of_worship"]["name"]["wikidata"]({G}););out tags center;',
 "orte-alltag": f'(nwr["amenity"~"^(hospital|clinic|marketplace|embassy)$"]["name"]({G});nwr["shop"~"^(supermarket|mall)$"]["name"]({G});nwr["office"~"^(diplomatic|government)$"]["name"]({G}););out tags center;',
 "orte-stadt": f'(node["place"~"^(suburb|quarter|neighbourhood)$"]["name"]({K});nwr["railway"="station"]["name"]({G});nwr["amenity"="bus_station"]["name"]({G});nwr["aeroway"="aerodrome"]["name"]({G}););out tags center;',
}
def hole(abfrage):
    koerper = urllib.parse.urlencode({"data": "[out:json][timeout:170];" + abfrage}).encode()
    for runde in range(3):
        for u in SERVER:
            try:
                q = urllib.request.Request(u, koerper, {"User-Agent": "hanoi-karte (github.com/kidkodama/schutzgebiete-vietnam)"})
                d = json.load(urllib.request.urlopen(q, timeout=180))
                if d.get("elements"): return d, u
                print("  leer:", u, d.get("remark", ""))
            except Exception as e:
                print("  fehlgeschlagen:", u, e)
            time.sleep(10)
    return None, None
def runde(o):
    if isinstance(o, float): return round(o, 6)
    if isinstance(o, list): return [runde(x) for x in o]
    if isinstance(o, dict): return {k: runde(v) for k, v in o.items() if k not in ("bounds", "nodes")}
    return o
fehler = 0
for name, abfrage in TEILE.items():
    d, u = hole(abfrage)
    if not d:
        print("NICHT GELADEN:", name); fehler += 1; continue
    aus = {"elements": [runde(e) for e in d["elements"]], "osm3s": d.get("osm3s", {}), "server": u}
    open(f"hanoi/daten/{name}.json", "w", encoding="utf-8").write(json.dumps(aus, ensure_ascii=False, separators=(",", ":")))
    print(name, len(aus["elements"]), "von", u)
    time.sleep(10)
print("Fehler:", fehler)
