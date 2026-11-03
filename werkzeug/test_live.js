// Öffnet die veröffentlichte Hanoi-Karte mit echten Daten und zeichnet auf, was passiert.
const { webkit, chromium, devices } = require('playwright');
const URL_ = 'https://kidkodama.github.io/schutzgebiete-vietnam/hanoi/?t=' + Date.now();
(async () => {
  for (const [nm, typ, opt] of [['ipad', webkit, devices['iPad Pro 11 landscape']], ['iphone', webkit, devices['iPhone 14']], ['chrome', chromium, { viewport: { width: 1280, height: 800 } }]]) {
    console.log('=== ' + nm);
    const b = await typ.launch(); const c = await b.newContext(opt); const p = await c.newPage();
    const akt = {};
    p.on('pageerror', e => console.log('SEITENFEHLER', e.message));
    p.on('console', m => { if (m.type() === 'error') console.log('KONSOLE', m.text().slice(0, 200)); });
    p.on('requestfailed', q => { const h = new URL(q.url()).host; akt[h + ' FEHL ' + (q.failure() || {}).errorText] = (akt[h + ' FEHL ' + (q.failure() || {}).errorText] || 0) + 1; });
    p.on('response', r => { const h = new URL(r.url()).host; const k = h + ' ' + r.status(); akt[k] = (akt[k] || 0) + 1; if (r.url().includes('v2/map') && r.status() !== 200 && !akt.gezeigt) { akt.gezeigt = 1; console.log('KACHEL', r.status(), r.url()); } });
    const tipp = async s => { await p.locator(s).first().click({ timeout: 15000 }); };
    await p.goto(URL_, { timeout: 60000 }); await p.waitForTimeout(6000);
    console.log('Status', await p.textContent('#st-natur'), '|', await p.textContent('#st-wdpa'), '|', await p.textContent('#st-orte'));
    await p.locator('#g-natur label', { hasText: 'Birdwatching' }).click({ timeout: 15000 }); await p.waitForTimeout(7000);
    await p.screenshot({ path: `test-bilder/${nm}-1-felder.png` });
    await p.locator('#g-natur label', { hasText: 'Birdwatching' }).click(); 
    await tipp('#ansichten .tab[data-a=voegel]'); await p.waitForSelector('#v-liste details', { timeout: 30000 });
    console.log('Liste', await p.textContent('#v-sub'));
    await p.fill('#v-q', 'eisvogel'); await p.waitForTimeout(300); await tipp('.va'); await p.waitForSelector('.vk', { timeout: 30000 });
    await p.waitForTimeout(1500); await p.screenshot({ path: `test-bilder/${nm}-2-art.png` });
    await tipp('.vk');
    try { await p.waitForFunction(() => /Stellen|Keine Sichtungen|nicht geladen/.test(document.querySelector('.vbanner')?.textContent || ''), { timeout: 60000 }); } catch (e) { console.log('Banner-Frist abgelaufen'); }
    await p.waitForTimeout(3000);
    console.log('Banner', await p.locator('.vbanner').textContent().catch(() => 'KEIN BANNER'));
    console.log('Punkte', JSON.stringify(await p.evaluate(() => { let n = 0, ll = null; if (vDichte) vDichte.eachLayer(l => { n++; ll = ll || l.getLatLng(); }); return { n, ll, zoom: map.getZoom(), karte: document.getElementById('map').offsetHeight, an: !!vDichte && map.hasLayer(vDichte) }; })));
    await p.screenshot({ path: `test-bilder/${nm}-3-punkte.png` });
    delete akt.gezeigt; console.log('Abrufe', JSON.stringify(akt));
    await b.close();
  }
})().catch(e => { console.log('ABBRUCH', e.message); process.exit(0); });
