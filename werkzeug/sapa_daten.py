#!/usr/bin/env python3
"""Holt die OpenStreetMap-Daten der Sa-Pa-Karte und legt sie als Dateien ab.
Bricht nie vorhandene Daten ab: scheitert ein Teil, bleibt die alte Datei stehen."""
import json, sys, time, urllib.parse, urllib.request
SERVER = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
          "https://overpass.private.coffee/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
G = "22.15,103.60,22.55,104.05"; K = G
TEILE = {
 "natur": f'(nwr["leisure"~"^(park|garden|nature_reserve)$"]["name"]({G});nwr["boundary"~"^(protected_area|national_park)$"]["name"]({G});nwr["natural"="water"]["name"]({G}););out geom;',
 "strassen": f'way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]({K});out tags geom;',
 "orte-sehen": f'(nwr["tourism"~"^(museum|attraction|viewpoint|gallery)$"]["name"]({G});nwr["historic"]["name"]({G});nwr["natural"~"^(peak|waterfall|cave_entrance|saddle)$"]["name"]({G});nwr["aerialway"="station"]["name"]({G});nwr["amenity"="place_of_worship"]["name"]({G}););out tags center;',
 "orte-alltag": f'(nwr["amenity"~"^(hospital|clinic|pharmacy|marketplace|police)$"]["name"]({G});nwr["shop"~"^(supermarket|mall)$"]["name"]({G});nwr["office"~"^(government)$"]["name"]({G});nwr["tourism"~"^(guest_house|hostel|alpine_hut|camp_site)$"]["name"]({G}););out tags center;',
 "orte-stadt": f'(node["place"~"^(town|village|hamlet|suburb|quarter|neighbourhood)$"]["name"]({K});nwr["railway"="station"]["name"]({G});nwr["amenity"="bus_station"]["name"]({G}););out tags center;',
 "wege": f'way["highway"~"^(path|track|footway|steps|bridleway)$"]({G});out tags geom;',
 "routen": f'relation["route"~"^(hiking|foot|walking)$"]({G});out geom;',
}
def hole(abfrage):
    koerper = urllib.parse.urlencode({"data": "[out:json][timeout:170];" + abfrage}).encode()
    for runde in range(3):
        for u in SERVER:
            try:
                q = urllib.request.Request(u, koerper, {"User-Agent": "sapa-karte (github.com/kidkodama/schutzgebiete-vietnam)"})
                d = json.load(urllib.request.urlopen(q, timeout=180))
                if d.get("elements"): return d, u
                print("  leer:", u, d.get("remark", ""))
            except Exception as e:
                print("  fehlgeschlagen:", u, e)
            time.sleep(10)
    return None, None
BEHALTEN = {"name","name:en","leisure","natural","tourism","amenity","shop","office","railway","station","aeroway","historic","place","ele","boundary","protect_class","aerialway","sac_scale","trail_visibility","surface","highway","route","distance","ascent","descent","from","to","description","operator","network","ref",
            "wikidata","wikipedia","website","contact:website","phone","contact:phone","opening_hours","addr:housenumber","addr:street","addr:district","addr:city"}
def punkt(p): return {"lat": round(p["lat"], 5), "lon": round(p["lon"], 5)}
def duenn(e, name):
    aus = {"type": e["type"], "id": e["id"]}
    behalte = {"name", "ref"} if name == "strassen" else {"name","name:en","highway","sac_scale","trail_visibility","surface"} if name == "wege" else BEHALTEN
    aus["tags"] = {k: v for k, v in e.get("tags", {}).items() if k in behalte}
    if "lat" in e: aus.update(punkt(e))
    if "center" in e: aus["center"] = punkt(e["center"])
    if "geometry" in e: aus["geometry"] = [punkt(p) for p in e["geometry"] if p]
    if "members" in e:
        aus["members"] = [{"type": m["type"], "role": m.get("role", ""), "geometry": [punkt(p) for p in m["geometry"] if p]}
                          for m in e["members"] if m["type"] == "way" and m.get("geometry")]
    return aus
def schreibe(name, elemente, stand):
    aus = {"elements": [duenn(e, name) for e in elemente], "osm3s": stand}
    with open(f"sapa/daten/{name}.json", "w", encoding="utf-8") as f:
        json.dump(aus, f, ensure_ascii=False, separators=(",", ":"))
    return len(aus["elements"])
if len(sys.argv) > 1 and sys.argv[1] == "--nur-duennen":
    for name in TEILE:
        d = json.load(open(f"sapa/daten/{name}.json", encoding="utf-8"))
        print(name, schreibe(name, d["elements"], d.get("osm3s", {})))
    sys.exit(0)
fehler = 0
for name, abfrage in TEILE.items():
    d, u = hole(abfrage)
    if not d:
        print("NICHT GELADEN:", name); fehler += 1; continue
    print(name, schreibe(name, d["elements"], d.get("osm3s", {})), "von", u)
    time.sleep(10)
print("Fehler:", fehler)
