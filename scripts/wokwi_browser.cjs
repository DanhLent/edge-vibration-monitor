// Use the documented Wokwi custom-firmware UI with a fresh browser context.
const fs = require('node:fs');
const { chromium } = require('playwright-core');

async function run() {
  const [binary, diagram, done, screenshot, dashboard, device] = process.argv.slice(2);
  if (dashboard) return captureDashboard(dashboard, screenshot, device);
  const browser = await chromium.launch({executablePath: process.env.E2_BROWSER || undefined});
  try {
    const context = await browser.newContext({viewport:{width:1440,height:1000},
      permissions:['clipboard-read','clipboard-write']});
    const page = await context.newPage();
    await page.goto('https://wokwi.com/projects/305457271083631168', {waitUntil:'domcontentloaded'});
    if (diagram !== '-') {
      await page.getByRole('button',{name:'diagram.json',exact:true}).click();
      const editor = page.locator('.monaco-editor:visible');
      await editor.click();
      const expected = fs.readFileSync(diagram, 'utf8').trim();
      await page.evaluate(value => navigator.clipboard.writeText(value), expected);
      await page.keyboard.press('Control+a');
      await page.keyboard.press('Control+v');
      const confirmation = page.getByRole('button',{name:/^replace$/i});
      if (await confirmation.isVisible()) await confirmation.click();
      await editor.click();
      await page.keyboard.press('Control+a');
      await page.keyboard.press('Control+c');
      if ((await page.evaluate(() => navigator.clipboard.readText())).trim() !== expected) {
        throw new Error('Wokwi diagram readback differs from the supplied file');
      }
    }
    await page.locator('.monaco-editor:visible').click();
    await page.keyboard.press('F1');
    await page.keyboard.type('Upload Firmware');
    const choice = page.getByText('Upload Firmware and Start Simulation');
    const upload = page.waitForEvent('filechooser');
    await choice.click();
    await (await upload).setFiles(binary);
    let last = 0, lastPress = "";
    while (!fs.existsSync(done)) {
      const body = await page.locator('body').innerText();
      for (const line of body.matchAll(/(?:E2_WINDOW,(\d+),\d+,\w+,-?\d+,\d+\.\d+,\d+\.\d+,[01]|E2_PARITY,\d+,\d+,[01])/g)) {
        if (!line[1]) { console.log(line[0]); return; }
        if (Number(line[1]) > last) { last = Number(line[1]); console.log(line[0]); }
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
  } finally { await browser.close(); }
}

async function captureDashboard(url, screenshot, device) {
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
          deviceWindow.model_ready && deviceWindow.prediction===mode) break;
      if (Date.now()>=deadline) throw new Error('No correlated browser ACK and matching window');
      await new Promise(resolve=>setTimeout(resolve,200));
    } while (true);
    await page.waitForFunction(label =>
      document.querySelector('#commandState').textContent.startsWith('Command done') &&
      document.querySelector('#prediction').textContent.trim()===label &&
      !document.querySelector('#chart').hidden, mode==='loose'?'Loose mounting':'Imbalance', {timeout:10000});
    await page.screenshot({path:screenshot,fullPage:true});
    console.log(JSON.stringify({id:command.command_id,mode,before:before.window_id,boot:before.boot_id,window:deviceWindow.window_id,
      prediction:deviceWindow.prediction,ack:ack.state}));
  } finally { await browser.close(); }
}

run().catch(error=>{ console.error(error.message); process.exit(1); });
