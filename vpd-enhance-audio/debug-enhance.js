const { chromium } = require('playwright');
const path = require('path');
(async () => {
  // Test 1: headless true (new headless mode)
  console.log('=== Test: headless: true ===');
  {
    const browser = await chromium.launch({
      headless: true,
      args: ['--disable-blink-features=AutomationControlled']
    });
    const context = await browser.newContext({
      storageState: path.join(__dirname, 'adobe-auth.json'),
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      viewport: { width: 1280, height: 720 }
    });
    const page = await context.newPage();
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => false });
    });

    await page.goto('https://podcast.adobe.com/en/enhance', { waitUntil: 'domcontentloaded', timeout: 30000 });

    // Wait up to 20s for Choose files button
    const btn = await page.waitForSelector('sp-button:has-text("Choose files")', { timeout: 20000 }).catch(() => null);
    const elCount = await page.evaluate(() => document.querySelectorAll('*').length);
    console.log(`  Elements: ${elCount}, Choose files button: ${btn ? 'FOUND' : 'NOT FOUND'}`);
    await page.screenshot({ path: '/tmp/headless-true.png' });
    await browser.close();
  }

  // Test 2: headless "shell" (old headless)
  console.log('\n=== Test: headless: "shell" ===');
  {
    const browser = await chromium.launch({
      headless: "shell",
      args: ['--disable-blink-features=AutomationControlled']
    });
    const context = await browser.newContext({
      storageState: path.join(__dirname, 'adobe-auth.json'),
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      viewport: { width: 1280, height: 720 }
    });
    const page = await context.newPage();
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => false });
    });

    await page.goto('https://podcast.adobe.com/en/enhance', { waitUntil: 'domcontentloaded', timeout: 30000 });

    const btn = await page.waitForSelector('sp-button:has-text("Choose files")', { timeout: 20000 }).catch(() => null);
    const elCount = await page.evaluate(() => document.querySelectorAll('*').length);
    console.log(`  Elements: ${elCount}, Choose files button: ${btn ? 'FOUND' : 'NOT FOUND'}`);
    await page.screenshot({ path: '/tmp/headless-shell.png' });
    await browser.close();
  }

  console.log('\nDone.');
})();
