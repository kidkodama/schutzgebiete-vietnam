// Öffnet die veröffentlichte Sa-Pa-Karte mit echten Daten und zeichnet auf, was passiert.
const { webkit, devices } = require('playwright');
const URL_ = 'https://kidkodama.github.io/schutzgebiete-vietnam/sapa/?t=' + Date.now();
(async () => {
  for (const [nm, opt] of [['sapa-ipad', devices['iPad Pro 11 landscape']], ['sapa-iphone', devices['iPhone 14']]]) {
    console.log('=== ' + nm);
    const b = await webkit.launch(); const c = await b.newContext({ ...opt, acceptDownloads: true }); const p = await c.newPage();
    const fehl = {};
    p.on('pageerror', e => console.log('SEITENFEHLER', e.message));
    p.on('response', r => { if (r.status() >= 400) { const h = new URL(r.url()).host + ' ' + r.status(); fehl[h] = (fehl[h] || 0) + 1; } });
    p.on('requestfailed', q => { const h = new URL(q.url()).host + ' FEHL'; fehl[h] = (fehl[h] || 0) + 1; });
    await p.goto(URL_, { timeout: 60000 });
    try { await p.waitForFunction(() => /Wegst/.test(document.querySelector('#a-wandern .vsub')?.textContent || '') && /an \d/.test(document.getElementById('st-schlangen').textContent), { timeout: 60000 }); } catch (e) { console.log('Frist abgelaufen'); }
    await p.waitForTimeout(6000);
    for (const i of ['st-natur', 'st-voegel', 'st-schlangen', 'st-wdpa', 'st-stadt', 'st-orte']) console.log(i, (await p.textContent('#' + i)).slice(0, 150));
    console.log('Zähler', JSON.stringify(await p.evaluate(() => zaehler)));
    await p.screenshot({ path: `test-bilder/${nm}-1-karte.png` });
    await p.evaluate(() => { const r = records.find(x => /Phan Xi/.test(x.name)); if (r) { map.setView(r.layer.getLatLng(), 14, { animate: false }); r.layer.openPopup(); } });
    await p.waitForTimeout(3500);
    console.log('Fansipan', (await p.locator('.leaflet-popup-content').textContent().catch(() => 'KEIN POPUP')).replace(/\s+/g, ' ').slice(0, 300));
    await p.screenshot({ path: `test-bilder/${nm}-2-fansipan.png` });
    await p.evaluate(() => map.closePopup());
    await p.locator('#ansichten .tab[data-a=wandern]').click(); await p.waitForTimeout(500);
    console.log('Wandern', await p.textContent('#a-wandern .vsub'));
    await p.screenshot({ path: `test-bilder/${nm}-3-wandern.png` });
    await p.locator('#a-wandern .va').first().click(); await p.waitForTimeout(4000);
    console.log('Banner', await p.locator('.vbanner').textContent().catch(() => 'KEIN BANNER'));
    await p.screenshot({ path: `test-bilder/${nm}-4-route.png` });
    console.log('Fehlgeschlagene Abrufe', JSON.stringify(fehl));
    await b.close();
  }
})().catch(e => { console.log('ABBRUCH', e.message); process.exit(0); });
