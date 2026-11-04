#!/usr/bin/env python3
"""Holt die Schutzgebiete Vietnams aus der WDPA (UNEP-WCMC, ArcGIS) und legt sie
als Dateien neben die Karte. Die Karte lädt zuerst diese Dateien und fragt die
WDPA nur noch, wenn sie fehlen. Scheitert der Abruf, bleibt die alte Datei stehen."""
import json, sys, time, urllib.parse, urllib.request
S = "https://services5.arcgis.com/Mj0hjvkNtV7NRhA7/arcgis/rest/services/WDPA_v0/FeatureServer"
W = urllib.parse.quote("iso3='VNM'")
TEILE = {
  "wdpa-flaechen": f"{S}/1/query?where={W}&outFields=*&returnGeometry=true&outSR=4326&geometryPrecision=5&maxAllowableOffset=0.002&resultRecordCount=2000&f=geojson",
  "wdpa-punkte":   f"{S}/0/query?where={W}&outFields=*&returnGeometry=true&outSR=4326&geometryPrecision=5&resultRecordCount=2000&f=geojson",
}
fehler = 0
for name, url in TEILE.items():
    for runde in range(3):
        t0 = time.time()
        try:
            q = urllib.request.Request(url, headers={"User-Agent": "schutzgebiete-vietnam (github.com/kidkodama/schutzgebiete-vietnam)"})
            roh = urllib.request.urlopen(q, timeout=240).read()
            d = json.loads(roh)
            if d.get("error"): raise RuntimeError(d["error"])
            n = len(d.get("features") or [])
            print(f"{name}: {n} Einträge, {len(roh)//1024} KB, {time.time()-t0:.1f} s")
            if n == 0 and name == "wdpa-flaechen": raise RuntimeError("keine Flächen")
            d["abgerufen"] = time.strftime("%Y-%m-%d")
            with open(f"daten/{name}.geojson", "w", encoding="utf-8") as fh:
                json.dump(d, fh, ensure_ascii=False, separators=(",", ":"))
            break
        except Exception as e:
            print(f"{name}: Versuch {runde+1} fehlgeschlagen nach {time.time()-t0:.1f} s: {e}")
            time.sleep(20)
    else:
        fehler += 1
sys.exit(1 if fehler else 0)
