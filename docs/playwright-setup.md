# Automacao Web com Playwright

Este projeto usa **Playwright** (Node.js) para automatizar operacoes em websites que exigem login (ex: Adobe Podcast Enhance). O ambiente roda em WSL2 com WSLg (suporte a GUI).

## Dependencias ja instaladas

- Node.js + npm
- `playwright` (npm package)
- Chromium para Playwright (`npx playwright install chromium`)
- Dependencias de sistema (`npx playwright install-deps chromium`)

## Fluxo de autenticacao com storageState

Sites que exigem login (Google, Adobe, etc) usam o padrao **storageState** do Playwright:

### Passo 1 — Salvar sessao (login manual, uma unica vez)

Existe um script pronto em `vpd-enhance-audio/save-session.js`. Para criar um novo para outro site, siga o modelo:

```js
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto('https://URL-DO-SITE');

  // Pausa - o usuario faz login manualmente no browser que abriu
  await page.pause();

  // Apos login, usuario clica "Resume" no Playwright Inspector
  await context.storageState({ path: 'NOME-auth.json' });
  console.log('Sessao salva!');
  await browser.close();
})();
```

Rodar com: `node script.js`

- O browser abre via WSLg (headed mode)
- O usuario faz login manualmente
- Clica "Resume" no Playwright Inspector (janela de controle)
- Cookies/sessao ficam salvos em um arquivo `.json`

**IMPORTANTE:** Este passo requer interacao do usuario. Avise o usuario que ele precisa:
1. Fazer login manualmente no browser que vai abrir
2. Clicar "Resume" no Playwright Inspector apos logar

### Passo 2 — Usar sessao salva (automatizado, headless)

```js
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    storageState: 'NOME-auth.json'  // sessao salva no passo 1
  });
  const page = await context.newPage();

  await page.goto('https://URL-DO-SITE');
  // ... automacao aqui ...

  await browser.close();
})();
```

## Sessoes disponiveis

| Arquivo | Site | Observacao |
|---------|------|------------|
| `adobe-auth.json` | podcast.adobe.com | Login Adobe/Google, expira apos dias/semanas |

Quando uma sessao expirar, basta rodar novamente o script do Passo 1 para renovar.

## Dicas para o Claude

- Antes de automatizar, verifique se o arquivo `*-auth.json` existe. Se nao existir, rode o Passo 1 e avise o usuario.
- Use `headless: true` no Passo 2 (automacao). So use `headless: false` quando precisar de login manual.
- Para sudo, leia `.env` e use `echo $SUDO_PASS | sudo -S <comando>`.
- Dependencias Playwright ficam em `playwright/` (compartilhado).
- Scripts especificos ficam na pasta de cada funcionalidade (ex: `vpd-enhance-audio/`).
- Rodar scripts com: `node vpd-enhance-audio/save-session.js`
- Instalar dependencias com: `cd playwright && npm install`

## Estrutura

```
audvid/
  .env                         # Credenciais sudo (NAO commitar)
  playwright/                  # Infra compartilhada
    package.json               # Dependencias Node.js
    package-lock.json          # Lock de versoes
    node_modules/              # Pacotes instalados
  vpd-enhance-audio/           # Funcionalidade com scripts Playwright
    save-session.js            # Login manual Adobe (Passo 1)
    adobe-auth.json            # Sessao Adobe (gerada pelo Passo 1)
```
