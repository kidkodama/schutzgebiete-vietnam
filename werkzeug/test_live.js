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
    await p.waitForTimeout(3000);
    console.log('Sichtungen', await p.textContent('#st-voegel'), JSON.stringify(await p.evaluate(() => ({ auf: map.hasLayer(groups.voegel), n: groups.voegel.getLayers().length }))));
    const pkt = await p.evaluate(() => { let best; groups.voegel.eachLayer(l => { const q = map.latLngToContainerPoint(l.getLatLng()), s = map.getSize(); if (q.x > 60 && q.y > 60 && q.x < s.x - 60 && q.y < s.y - 60 && (!best || l.getRadius() > best.getRadius())) best = l; }); const q = map.latLngToContainerPoint(best.getLatLng()), a = map.getContainer().getBoundingClientRect(); return [a.left + q.x, a.top + q.y]; });
    await p.screenshot({ path: `test-bilder/${nm}-0-sichtungen.png` });
    await p.mouse.click(pkt[0], pkt[1]); await p.waitForTimeout(700);
    console.log('Popup', (await p.locator('.leaflet-popup-content').textContent().catch(() => 'KEIN POPUP')).replace(/\s+/g, ' ').slice(0, 300));
    await p.screenshot({ path: `test-bilder/${nm}-1-felder.png` });
    await p.evaluate(() => { map.closePopup(); });
    await p.screenshot({ path: `test-bilder/${nm}-1-felder.png` });
    for (const [id, suche] of [['voegel', 'eisvogel'], ['schlangen', 'kobra']]) {
      await tipp(`#ansichten .tab[data-a=${id}]`); await p.waitForSelector(`#a-${id} .vliste details`, { timeout: 30000 });
      console.log(id, await p.textContent(`#a-${id} .vsub`));
      console.log(' Gruppen', JSON.stringify(await p.$$eval(`#a-${id} .vliste summary`, x => x.map(y => y.textContent))));
      await p.screenshot({ path: `test-bilder/${nm}-${id}-liste.png` });
      await p.fill(`#a-${id} .vq`, suche); await p.waitForTimeout(300); await tipp(`#a-${id} .va`); await p.waitForSelector(`#a-${id} .vk`, { timeout: 30000 });
      await p.waitForTimeout(1500); await tipp(`#a-${id} .vk`);
      try { await p.waitForFunction(() => /Stellen|Keine Sichtungen|nicht geladen/.test(document.querySelector('.vbanner')?.textContent || ''), { timeout: 60000 }); } catch (e) { console.log('Banner-Frist abgelaufen'); }
      await p.waitForTimeout(2500);
      console.log(' Banner', await p.locator('.vbanner').textContent().catch(() => 'KEIN BANNER'));
      await p.screenshot({ path: `test-bilder/${nm}-${id}-punkte.png` });
      await p.locator('.vbanner button').click({ force: true }).catch(() => {});
      await p.evaluate(() => { document.querySelectorAll('#g-natur label input').forEach(i => { if (!i.checked) i.click(); }); });
      await tipp('#ansichten .tab[data-a=karte]');
    }
    await p.waitForTimeout(800);
    console.log('Sichtungen', JSON.stringify(await p.evaluate(() => ({ v: groups.voegel.getLayers().length, s: groups.schlangen.getLayers().length, auf: map.hasLayer(groups.schlangen) }))), await p.textContent('#st-schlangen'));
    await p.evaluate(() => { map.setView([21.03, 105.85], 12, { animate: false }); }); await p.waitForTimeout(2500);
    await p.screenshot({ path: `test-bilder/${nm}-4-alle.png` });
    delete akt.gezeigt; console.log('Abrufe', JSON.stringify(akt));
    await b.close();
  }
})().catch(e => { console.log('ABBRUCH', e.message); process.exit(0); });
