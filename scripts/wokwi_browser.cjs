// Use the documented Wokwi custom-firmware UI with a fresh browser context.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright-core');

async function run() {
  const [binary, diagram, done, screenshot, dashboard, device, expectedModel] = process.argv.slice(2);
  if (dashboard) return captureDashboard(dashboard, screenshot, device, expectedModel);
  const browser = await chromium.launch({executablePath: process.env.E2_BROWSER || undefined});
  try {
    const context = await browser.newContext({viewport:{width:1440,height:1000},
      permissions:['clipboard-read','clipboard-write']});
    const assets = process.env.E2_WOKWI_STATIC_CACHE;
    if (assets) {
      const root = path.resolve(assets);
      const templateFile = path.join(root, "template.html");
      if (fs.existsSync(templateFile)) {
        await context.route('https://wokwi.com/projects/305457271083631168?mode=code',
          route => route.fulfill({path:templateFile, contentType:'text/html; charset=utf-8'}));
      }
      await context.route(/^https:\/\/wokwi\.com\/(?:_next\/static|cdn\/monaco-editor)\//, async route => {
        const name = new URL(route.request().url()).pathname;
        const file = path.resolve(root, "." + name);
        if (file.startsWith(root + path.sep) && fs.existsSync(file) && fs.statSync(file).isFile()) {
          await route.fulfill({path:file});
        } else {
          await route.continue();
        }
      });
    }
    const page = await context.newPage();
    const template = 'https://wokwi.com/projects/305457271083631168?mode=code';
    for (let attempt=0; ; ++attempt) {
      try {
        await page.goto(template, {waitUntil:'domcontentloaded',timeout:25000});
        await page.locator('.monaco-editor').first().waitFor({timeout:15000});
        break;
      } catch (error) {
        if (attempt >= 3) throw error;
      }
    }
    if (diagram !== '-') {
      await page.getByRole('button',{name:'diagram.json',exact:true}).click({position:{x:36,y:12}, force:true});
      const editor = page.locator('.monaco-editor:visible').first();
      const expected = fs.readFileSync(diagram, 'utf8').trim();
      const parsed = JSON.stringify(JSON.parse(expected));
      for (let attempt=0; ; ++attempt) {
        await editor.click({position:{x:220,y:125},force:true});
        await page.evaluate(value => navigator.clipboard.writeText(value), expected);
        await page.keyboard.press('Control+a');
        await page.keyboard.press('Control+v');
        const confirmation = page.getByRole('button',{name:/^replace$/i});
        if (await confirmation.isVisible()) await confirmation.click();
        await editor.click({position:{x:220,y:125},force:true});
        await page.evaluate(() => navigator.clipboard.writeText(''));
        await page.keyboard.press('Control+a');
        await page.keyboard.press('Control+c');
        const actual = await page.evaluate(() => navigator.clipboard.readText());
        try {
          if (JSON.stringify(JSON.parse(actual)) === parsed) break;
        } catch {}
        if (attempt >= 2) throw new Error('Wokwi diagram readback differs from the supplied file');
      }
    }
    await page.locator('.monaco-editor:visible').first().click({position:{x:220,y:125},force:true});
    await page.keyboard.press('F1');
    await page.keyboard.type('Upload Firmware');
    const choice = page.getByText('Upload Firmware and Start Simulation');
    const upload = page.waitForEvent('filechooser');
    await choice.click();
    await (await upload).setFiles(binary);
    await page.setViewportSize({width:1900,height:1000});
    let last = 0, lastPress = "";
    const fftLines = process.env.E2_EXPECT_SPECTRUM === "1";
    const baseLine = /E2_WINDOW,(\d+),\d+,\w+,-?\d+,\d+\.\d+,\d+\.\d+,[01]/.source;
    const spectrum = /,\d+\.\d+,\d+\.\d+,\d+,[01]/.source;
    const rows = new RegExp(baseLine + (fftLines ? spectrum : "(?:"+spectrum+")?"), "g");
    while (!fs.existsSync(done)) {
      const body = await page.locator('body').innerText();
      for (const line of body.matchAll(rows)) {
        if (Number(line[1]) > last) { last = Number(line[1]); console.log(line[0]); }
      }
      const parity = body.match(/E2_PARITY,\d+,\d+,[01]/);
      if (parity) { console.log(parity[0]); return; }
      if (body.includes('E2_BENCH_DONE')) {
        for (const line of body.matchAll(/E2_BENCH,[01](?:,\d+){6}/g)) console.log(line[0]);
        return;
      }
      const button = done + '.button';
      if (fs.existsSync(button) && fs.readFileSync(button, 'utf8') !== lastPress) {
        lastPress = fs.readFileSync(button, 'utf8');
        const part = page.locator('wokwi-pushbutton').first();
        const box = await part.boundingBox();
        if (!box) throw new Error('Wokwi pushbutton missing from the verified diagram');
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        await page.mouse.down();
        await new Promise(resolve=>setTimeout(resolve, 650));
        await page.mouse.up();
      }
      await new Promise(resolve=>setTimeout(resolve, 150));
    }
    if (screenshot !== '-') await page.screenshot({path:screenshot});
  } catch (error) {
    if (screenshot !== '-') {
      const failure = browser.contexts()[0]?.pages()[0];
      if (failure) await failure.screenshot({path:screenshot+'.failure.png',timeout:3000}).catch(()=>{});
    }
    throw error;
  } finally { await browser.close(); }
}

async function captureDashboard(url, screenshot, device, expectedModel) {
  const browser = await chromium.launch({executablePath: process.env.E2_BROWSER || undefined});
  try {
    const page = await browser.newPage({viewport:{width:1360,height:950}});
    await page.goto(url);
    await page.locator('#device').selectOption(device);
    await page.waitForFunction(() => !document.querySelector('#apply').disabled, null, {timeout:45000});
    const before = await page.request.get(url+'/api/v1/devices/'+device+'/latest').then(res=>res.json());
    const mode = before.mode === 'imbalance' ? 'loose' : 'imbalance';
    await page.locator('#mode').selectOption(mode);
    const commandResponse = page.waitForResponse(res => res.request().method()==='POST' && res.url().endsWith('/commands'));
    await page.locator('#apply').click();
    const command = await (await commandResponse).json();
    const deadline = Date.now()+45000;
    let deviceWindow, ack;
    do {
      [ack, deviceWindow] = await Promise.all([
        page.request.get(url+'/api/v1/commands/'+command.command_id).then(res=>res.json()),
        page.request.get(url+'/api/v1/devices/'+device+'/latest').then(res=>res.json())
      ]);
      if (ack.state !== 'pending' && ack.state !== 'done') throw new Error('Browser command '+ack.state);
      if (ack.state==='done' && ack.result==='done' && deviceWindow.boot_id===before.boot_id &&
          deviceWindow.window_id>before.window_id && deviceWindow.mode===mode &&
          deviceWindow.model_ready && deviceWindow.prediction===mode &&
          (!expectedModel || deviceWindow.model_variant===expectedModel && deviceWindow.spectrum)) break;
      if (Date.now()>=deadline) throw new Error('No correlated browser ACK and matching window');
      await new Promise(resolve=>setTimeout(resolve,200));
    } while (true);
    await page.waitForFunction(label =>
      document.querySelector('#commandState').textContent.startsWith('Command done') &&
      document.querySelector('#prediction').textContent.trim()===label &&
      !document.querySelector('#chart').hidden, mode==='loose'?'Loose mounting':'Imbalance', {timeout:10000});
    if (expectedModel) {
      await page.locator('#field').selectOption('p2x');
      const now = Date.now()/1000;
      const history = await page.request.get(url+'/api/v1/devices/'+device+'/telemetry',
        {params:{field:'p2x',from:now-300,to:now}}).then(res=>res.json());
      if (!Array.isArray(history) || !history.some(point=>Math.abs(point.v-deviceWindow.spectrum.p2x)<1e-8))
        throw new Error('Spectral history is missing the correlated window');
      await page.waitForFunction(() => !document.querySelector('#chart').hidden &&
        document.querySelector('#spectrum').textContent.includes('FFT runtime'));
    }
    await page.screenshot({path:screenshot,fullPage:true});
    console.log(JSON.stringify({id:command.command_id,mode,before:before.window_id,boot:before.boot_id,window:deviceWindow.window_id,
      prediction:deviceWindow.prediction,ack:ack.state,latency_ms:1000*(ack.updated-ack.created),
      model_variant:deviceWindow.model_variant,spectrum:deviceWindow.spectrum}));
  } finally { await browser.close(); }
}

run().catch(error=>{ console.error(error.message); process.exit(1); });
