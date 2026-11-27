// Use the documented Wokwi custom-firmware UI with a fresh browser context.
const fs = require('node:fs');
const { chromium } = require('playwright-core');

async function run() {
  const [binary, diagram, done, screenshot, dashboard] = process.argv.slice(2);
  if (dashboard) return captureDashboard(dashboard, screenshot);
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
      await page.getByRole('button',{name:'sketch.ino',exact:true}).click();
    }
    await page.locator('.monaco-editor:visible').click();
    await page.keyboard.press('F1');
    await page.keyboard.type('Upload Firmware');
    const choice = page.getByText('Upload Firmware and Start Simulation');
    const upload = page.waitForEvent('filechooser');
    await choice.click();
    await (await upload).setFiles(binary);
    let last = 0;
    while (!fs.existsSync(done)) {
      const body = await page.locator('body').innerText();
      for (const line of body.matchAll(/(?:E2_WINDOW,(\d+),\d+,\w+,-?\d+,\d+\.\d+,\d+\.\d+,[01]|E2_PARITY,\d+,\d+,[01])/g)) {
        if (!line[1]) { console.log(line[0]); return; }
        if (Number(line[1]) > last) { last = Number(line[1]); console.log(line[0]); }
      }
      const button = done + '.button';
      if (fs.existsSync(button) && !fs.existsSync(button + '.pressed')) {
        const part = page.locator('wokwi-pushbutton').first();
        const box = await part.boundingBox();
        if (!box) throw new Error('Wokwi pushbutton missing from the verified diagram');
        await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
        await page.mouse.down();
        await new Promise(resolve=>setTimeout(resolve, 650));
        await page.mouse.up();
        fs.writeFileSync(button + '.pressed', '');
      }
      await new Promise(resolve=>setTimeout(resolve, 150));
    }
    if (screenshot !== '-') await page.screenshot({path:screenshot});
  } finally { await browser.close(); }
}

async function captureDashboard(url, screenshot) {
  const browser = await chromium.launch({executablePath: process.env.E2_BROWSER || undefined});
  try {
    const page = await browser.newPage({viewport:{width:1360,height:950}});
    await page.goto(url);
    await page.waitForFunction(() => !document.querySelector('#apply').disabled, null, {timeout:45000});
    const before = await page.request.get(url+'/api/v1/devices/esp32-01/latest').then(res=>res.json());
    const mode = before.mode === 'imbalance' ? 'loose' : 'imbalance';
    await page.locator('#mode').selectOption(mode);
    const commandResponse = page.waitForResponse(res => res.request().method()==='POST' && res.url().endsWith('/commands'));
    await page.locator('#apply').click();
    const command = await (await commandResponse).json();
    await page.waitForFunction(async ({command, before, mode}) => {
      const [ack, latest] = await Promise.all([
        fetch('/api/v1/commands/'+command.command_id).then(res=>res.json()),
        fetch('/api/v1/devices/esp32-01/latest').then(res=>res.json())
      ]);
      return ack.state==='done' && ack.result==='done' && latest.boot_id===before.boot_id &&
        latest.window_id>before.window_id && latest.mode===mode && latest.model_ready &&
        latest.prediction===mode && document.querySelector('#commandState').textContent.startsWith('Command done') &&
        document.querySelector('#prediction').textContent.trim()===(mode==='loose'?'Loose mounting':'Imbalance') &&
        !document.querySelector('#chart').hidden;
    }, {command,before,mode}, {timeout:45000});
    await page.screenshot({path:screenshot,fullPage:true});
    console.log(JSON.stringify({id:command.command_id,mode,before:before.window_id,boot:before.boot_id}));
  } finally { await browser.close(); }
}

run().catch(error=>{ console.error(error.message); process.exit(1); });
