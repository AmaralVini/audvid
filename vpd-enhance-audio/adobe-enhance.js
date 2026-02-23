/**
 * adobe-enhance.js — Upload audio to Adobe Podcast Enhance, wait, download result
 *
 * Usage:
 *   node adobe-enhance.js --input /path/clean.wav --output /path/enhanced.wav
 *
 * Exit codes:
 *   0 = success
 *   1 = generic error
 *   2 = auth file missing
 *   3 = auth expired (redirected to login)
 *
 * Notes:
 *   - Requires headed mode (headless: false) — Adobe's SPA doesn't render in headless
 *   - Uses Spectrum Web Components (sp-button, sp-action-button)
 *   - Upload via fileChooser event on "Choose files" button
 *   - Download via button[aria-label="Download"] in footer bar
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ENHANCE_URL = 'https://podcast.adobe.com/en/enhance';
const AUTH_FILE = path.join(__dirname, 'adobe-auth.json');
const PROCESSING_TIMEOUT = 10 * 60 * 1000; // 10 minutes
const DOWNLOAD_TIMEOUT = 5 * 60 * 1000; // 5 minutes

function parseArgs() {
  const args = process.argv.slice(2);
  const result = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--input' && args[i + 1]) result.input = args[++i];
    else if (args[i] === '--output' && args[i + 1]) result.output = args[++i];
  }
  if (!result.input || !result.output) {
    console.error(JSON.stringify({ error: 'args', message: 'Usage: node adobe-enhance.js --input <file> --output <file>' }));
    process.exit(1);
  }
  return result;
}

function output(obj) {
  console.log(JSON.stringify(obj));
}

(async () => {
  const args = parseArgs();

  // Check input file exists
  if (!fs.existsSync(args.input)) {
    output({ error: 'input_missing', message: `Input file not found: ${args.input}` });
    process.exit(1);
  }

  // Check auth file
  if (!fs.existsSync(AUTH_FILE)) {
    output({ error: 'auth_missing', message: `Auth file not found: ${AUTH_FILE}. Run: node save-session.js` });
    process.exit(2);
  }

  let browser;
  try {
    // Must use headed mode — Adobe's SPA doesn't render in headless
    browser = await chromium.launch({
      headless: false,
      args: ['--disable-blink-features=AutomationControlled']
    });
    const context = await browser.newContext({
      storageState: AUTH_FILE,
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      viewport: { width: 1280, height: 720 }
    });
    const page = await context.newPage();

    // Remove webdriver flag
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => false });
    });

    // Navigate to enhance page
    console.error('[1/5] Navigating to Adobe Enhance...');
    await page.goto(ENHANCE_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });

    // Wait for SPA to render — "Choose files" button indicates page is ready
    console.error('[2/5] Waiting for page to render...');
    const chooseBtn = await page.waitForSelector('sp-button:has-text("Choose files")', { timeout: 30000 }).catch(() => null);

    if (!chooseBtn) {
      // Check if redirected to login (auth expired)
      const currentUrl = page.url();
      console.error('  Page URL:', currentUrl);
      const elCount = await page.evaluate(() => document.querySelectorAll('*').length);
      console.error('  DOM elements:', elCount);
      if (currentUrl.includes('login') || currentUrl.includes('signin') || currentUrl.includes('auth.services.adobe.com')) {
        output({ error: 'auth_expired', message: 'Session expired. Run: node save-session.js' });
        process.exit(3);
      }
      output({ error: 'no_upload', message: 'Could not find upload button on the page' });
      process.exit(1);
    }

    // Remove any existing file in the queue (free tier only allows one)
    const deleteBtn = await page.$('sp-action-button[aria-label="Delete"]');
    if (deleteBtn) {
      console.error('  Removing existing file from queue...');
      await deleteBtn.click();
      await page.waitForTimeout(2000);
    }

    // Upload file via fileChooser
    console.error('[3/5] Uploading file...');
    const [fileChooser] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 10000 }),
      chooseBtn.click()
    ]);
    await fileChooser.setFiles(args.input);
    console.error('  File sent to browser.');

    // Verify upload started — our filename should appear in the page within 10s
    const inputBasename = path.basename(args.input);
    console.error('  Verifying upload started...');
    let uploadConfirmed = false;
    for (let i = 0; i < 10; i++) {
      await page.waitForTimeout(1000);
      const bodyText = await page.evaluate(() => document.body.innerText);
      if (bodyText.includes(inputBasename)) {
        console.error(`  Upload confirmed: "${inputBasename}" found on page (${i+1}s)`);
        uploadConfirmed = true;
        break;
      }
    }
    if (!uploadConfirmed) {
      // Take screenshot for debug
      await page.screenshot({ path: path.join(__dirname, 'debug-upload-fail.png') });
      console.error('  Upload NOT confirmed after 10s. Screenshot saved: debug-upload-fail.png');
      output({ error: 'upload_failed', message: `File "${inputBasename}" not found on page after 10s. Upload may have failed.` });
      process.exit(1);
    }

    // Wait for Download button to appear (indicates processing is complete)
    console.error('[4/5] Waiting for Adobe to process (up to 10 min)...');
    const downloadButton = await page.waitForSelector(
      'button[aria-label="Download"]',
      { timeout: PROCESSING_TIMEOUT }
    ).catch(() => null);

    if (!downloadButton) {
      output({ error: 'timeout', message: 'Processing timed out (10 min). Download button not found.' });
      process.exit(1);
    }

    // Download the enhanced file
    console.error('[5/5] Downloading enhanced file...');
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: DOWNLOAD_TIMEOUT }),
      downloadButton.click()
    ]);

    // Save to output path
    await download.saveAs(args.output);

    // Verify output exists
    if (!fs.existsSync(args.output)) {
      output({ error: 'download_failed', message: 'Download completed but file not found' });
      process.exit(1);
    }

    output({ success: true });
    await browser.close();
    process.exit(0);

  } catch (err) {
    output({ error: 'generic', message: err.message });
    if (browser) await browser.close().catch(() => {});
    process.exit(1);
  }
})();
