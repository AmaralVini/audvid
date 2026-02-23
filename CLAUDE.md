# audvid — Ferramentas de Audio e Video

## Sobre o Projeto

Colecao de ferramentas para processamento de audio e video, focada em automacao de fluxos de edicao. Roda em **WSL2 (Ubuntu 24.04)** com ffmpeg do Windows.

**Convencoes:**
- Cada funcionalidade fica em sua propria pasta com um `CLAUDE.md` detalhado
- Infraestrutura compartilhada (Playwright) fica em `playwright/`
- Documentacao geral fica em `docs/`

---

## Funcionalidades

### vpd-enhance-audio/

Gera audio limpo (sem cliques nos cortes) a partir de projetos VideoProc Vlogger (.vpd), com enhance automatico via Adobe Podcast.

Documentacao completa: [vpd-enhance-audio/CLAUDE.md](vpd-enhance-audio/CLAUDE.md)

---

## Infraestrutura Compartilhada

### playwright/

Dependencias Node.js/Playwright compartilhadas por funcionalidades que usam automacao web. Contem `package.json`, `package-lock.json` e `node_modules/`.

Setup: `cd playwright && npm install && npx playwright install chromium`

Documentacao: [docs/playwright-setup.md](docs/playwright-setup.md)

---

## Credenciais

As credenciais de sudo/admin do WSL estao no arquivo `.env` na raiz do projeto. Use `echo $SUDO_PASS | sudo -S <comando>` quando precisar de permissoes elevadas. Para carregar: `source .env` ou leia diretamente do arquivo.

## Dependencias

- **Python 3** (incluso no Ubuntu 24.04)
- **ffmpeg** (nativo Linux ou `.exe` Windows acessivel via PATH)
- **Node.js** (para automacao web via Playwright)
- **Playwright** (`cd playwright && npm install`)
- Nenhum pacote Python adicional necessario (usa apenas stdlib)

## Documentacao

- `docs/vpd-format.md` — .vpd file format: complete JSON structure (reverse engineering)
- `docs/vpd-vlogger-reference.md` — VideoProc Vlogger program reference: presets, styles, effects, Lua API, codecs
- `docs/playwright-setup.md` — Setup e fluxo de autenticacao com Playwright (storageState)

## Estrutura de Arquivos

```
audvid/
  vpd-enhance-audio/               # Funcionalidade: audio limpo + enhance
    vpd-enhance-audio.py            # Script principal
    adobe-enhance.js                # Automacao Adobe Enhance
    save-session.js                 # Salvar sessao Adobe
    debug-enhance.js                # Debug do enhance
    CLAUDE.md                       # Documentacao completa
  playwright/                       # Infra Playwright compartilhada
    package.json                    # Dependencias Node
    package-lock.json
  docs/                             # Documentacao geral
    vpd-format.md                   # .vpd file format (reverse engineering)
    vpd-vlogger-reference.md        # VideoProc Vlogger program reference
    playwright-setup.md             # Setup Playwright + Adobe
  CLAUDE.md                         # Este arquivo
  .env                              # Credenciais (nao commitado)
  .gitignore
```
