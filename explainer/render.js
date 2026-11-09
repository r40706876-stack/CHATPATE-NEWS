// spec.json (scenes with start/end seconds) → frames/%05d.jpg at 30 fps, by seeking CSS animations frame-accurately.
const {chromium} = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const [specPath, outDir] = process.argv.slice(2);
  const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  fs.mkdirSync(outDir, {recursive: true});
  const browser = await chromium.launch();
  const page = await browser.newPage({viewport: {width: 1080, height: 1920}});
  await page.goto('file://' + path.resolve(__dirname, 'scenes.html'));
  await page.evaluate(s => window.load(s), spec);
  await page.evaluate(() => document.fonts.ready);
  const fps = 30, total = Math.ceil(spec.scenes[spec.scenes.length - 1].end * fps);
  const t0 = Date.now();
  for (let i = 0; i < total; i++) {
    await page.evaluate(t => window.seek(t), i / fps);
    await page.screenshot({path: path.join(outDir, String(i).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: 88});
  }
  console.log(`frames: ${total} in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  await browser.close();
})();
