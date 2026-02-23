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

### vpd-add-subtitles/

Adiciona legendas palavra-por-palavra ao VPD a partir do audio enhanced, com estilo OpusClip: palavra atual destacada com cor + tamanho diferente. Transcreve com Whisper (GPU), carrega estilo do VideoProc Vlogger, cada palavra e um bloco editavel na timeline.

Documentacao completa: [vpd-add-subtitles/CLAUDE.md](vpd-add-subtitles/CLAUDE.md)

### vpd-pipeline.py

Script pai que encadeia `vpd-enhance-audio` + `vpd-add-subtitles` em um unico comando. Requer conda env `pt-gpu` ativado.

```bash
conda activate pt-gpu
python3 vpd-pipeline.py projeto.vpd                    # enhance + subtitles
python3 vpd-pipeline.py projeto.vpd --skip-enhance      # so subtitles
python3 vpd-pipeline.py projeto.vpd --skip-subtitles    # so enhance
```

---

## Infraestrutura Compartilhada

### playwright/

Dependencias Node.js/Playwright compartilhadas por funcionalidades que usam automacao web. Contem `package.json`, `package-lock.json` e `node_modules/`.

Setup: `cd playwright && npm install && npx playwright install chromium`

Documentacao: [docs/playwright-setup.md](docs/playwright-setup.md)

---

## Credenciais

As credenciais de sudo/admin do WSL estao no arquivo `.env` na raiz do projeto. Use `echo $SUDO_PASS | sudo -S <comando>` quando precisar de permissoes elevadas. Para carregar: `source .env` ou leia diretamente do arquivo.

## Ambiente GPU (Whisper)

- **Miniforge**: `~/miniforge3`
- **Conda env**: `pt-gpu` (Python 3.12) — ativar com `conda activate pt-gpu`
- **PyTorch**: 2.6.0+cu124
- **GPU**: NVIDIA RTX 3060 Ti 8GB, CUDA 12.6
- **openai-whisper**: instalado no env `pt-gpu`
- **Modelos**: symlink `~/.cache/whisper` → `/mnt/c/Users/vinia/.cache/whisper` (base.pt, medium.pt, large-v3-turbo.pt)
- **ffmpeg**: nativo Linux (apt)

## Dependencias

- **Python 3** (incluso no Ubuntu 24.04)
- **ffmpeg** (nativo Linux via apt + `.exe` Windows acessivel via PATH)
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
  vpd-add-subtitles/               # Funcionalidade: legendas palavra-por-palavra
    vpd-add-subtitles.py            # Script principal
    CLAUDE.md                       # Documentacao completa
  vpd-pipeline.py                  # Script pai: enhance + subtitles
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
