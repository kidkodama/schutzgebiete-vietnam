// Öffnet die veröffentlichte Schutzgebiete-Karte wie ein iPad (WebKit) und schreibt auf, was passiert.
const { webkit, chromium, devices } = require('playwright');
const URL_ = 'https://kidkodama.github.io/schutzgebiete-vietnam/?t=' + Date.now();
(async () => {
  for (const [nm, typ, opt] of [['ipad', webkit, devices['iPad Pro 11 landscape']], ['chrome', chromium, { viewport: { width: 1280, height: 800 } }]]) {
    console.log('=== ' + nm);
    const b = await typ.launch(); const c = await b.newContext(opt); const p = await c.newPage();
    const akt = {};
    p.on('pageerror', e => console.log('SEITENFEHLER', e.message));
    p.on('console', m => { if (m.type() === 'error') console.log('KONSOLE', m.text().slice(0, 200)); });
    p.on('requestfailed', q => { const k = new URL(q.url()).host + ' FEHL ' + (q.failure() || {}).errorText; akt[k] = (akt[k] || 0) + 1; });
    p.on('response', r => { const u = new URL(r.url()); const k = u.host + (u.pathname.includes('daten/') ? u.pathname : '') + ' ' + r.status(); akt[k] = (akt[k] || 0) + 1; });
    const t0 = Date.now();
    await p.goto(URL_, { timeout: 60000 });
    try { await p.waitForFunction(() => !document.getElementById('ovl') || /nicht geladen/.test(document.getElementById('ovl').textContent), { timeout: 120000 }); } catch (e) { console.log('Frist 120 s abgelaufen'); }
    console.log('nach', Math.round((Date.now() - t0) / 1000), 's:', (await p.evaluate(() => document.getElementById('ovl') ? document.getElementById('ovl').innerText : 'geladen: ' + document.getElementById('s-n').innerText + ' Gebiete · ' + document.getElementById('method').innerText)).replace(/\s+/g, ' ').slice(0, 400));
    await p.screenshot({ path: `test-bilder/schutz-${nm}.png` });
    console.log('Abrufe', JSON.stringify(akt));
    await b.close();
  }
})().catch(e => { console.log('ABBRUCH', e.message); process.exit(0); });
