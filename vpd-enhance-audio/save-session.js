const { chromium } = require('playwright');
const path = require('path');

(async () => {
  console.log('Abrindo browser... Faça login manualmente na Adobe.');
  console.log('Depois de logado, feche o inspector do Playwright (botão Resume ou feche a janela).\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto('https://podcast.adobe.com/en/enhance');

  // Pausa - faça login manualmente
  await page.pause();

  // Salvar sessão
  await context.storageState({ path: path.join(__dirname, 'adobe-auth.json') });
  console.log('\nSessão salva em adobe-auth.json');

  await browser.close();
})();
