# vpd-enhance-audio — Audio limpo + enhance para projetos VPD

## Sobre

Script Python que gera audio limpo (sem cliques/ruidos nos pontos de corte) a partir de projetos VideoProc Vlogger (.vpd), e opcionalmente aplica Adobe Podcast Enhance para melhorar a qualidade do audio.

**Problema que resolve:** Ao fazer cortes de video no VideoProc Vlogger, surgem cliques audiveis nos pontos de corte. Isso acontece porque o corte abrupto da forma de onda cria descontinuidades. O script aplica micro-fades (fade-in/fade-out) em cada ponto de corte, eliminando os cliques.

## Como Funciona

1. **Parse do VPD** — Le o JSON do projeto e extrai todos os clips do VideoTrack e AudioTrack, incluindo timing, velocidade e estado de mute
2. **Extracao de audio** — Usa ffmpeg para extrair o audio completo de cada arquivo fonte referenciado
3. **Processamento por clip** — Para cada clip do VideoTrack:
   - Extrai o segmento de audio correspondente (`fileCuttedStart` + `fileCuttedDuration`)
   - Se o clip tem speed != 1.0x, aplica `atempo` (preserva pitch) para ajustar a duracao
   - Se o clip esta mutado, gera silencio
   - Aplica fade-in e fade-out de N milissegundos nas bordas
   - Ajusta a duracao exata para match perfeito com a timeline
4. **Concatenacao** — Junta todos os segmentos em ordem, inserindo silencio em gaps
5. **AudioTrack** — Processa os clips do AudioTrack e mixa com o audio do VideoTrack nas posicoes corretas
6. **Salva audio clean** — Gera `{projeto}-clean.wav` na mesma pasta do .vpd
7. **Adobe Podcast Enhance** (padrao) — Envia o audio clean ao Adobe Enhance via Playwright, aguarda processamento, e baixa o audio melhorado como `{projeto}-enhanced.wav`. Se falhar, o script para e avisa o usuario
8. **Modificacao do VPD** — Cria backup do .vpd original, insere o audio enhanced (ou clean com `--skip-enhance`) em um novo AudioTrack chamado "Audio Enhanced", e muta o MainVideoTrack e AudioTracks existentes (track-level)
9. **Verificacao** — Confere que a duracao final corresponde exatamente ao `context` da timeline

## Adobe Podcast Enhance

O enhance via Adobe Podcast e o **comportamento padrao**. Apos gerar o audio clean, o script:

1. Abre o browser (headed, Chromium via Playwright) com sessao salva
2. Remove arquivo existente na fila (plano gratuito so permite um)
3. Faz upload do audio clean via fileChooser
4. Aguarda processamento (timeout 10 min)
5. Baixa o audio enhanced

**Requisitos:**
- Node.js instalado
- Playwright com Chromium (`cd playwright && npm install && npx playwright install chromium`)
- Sessao Adobe salva: `cd vpd-enhance-audio && node save-session.js` (login manual unico)
- Modo headed obrigatorio (headless nao funciona — SPA da Adobe nao renderiza)

**Se o enhance falhar**, o script para e mostra opcoes:
1. Fazer enhance manualmente em https://podcast.adobe.com/en/enhance
2. Rodar novamente com `--skip-enhance` para usar o audio clean

**Exit codes do adobe-enhance.js:** 0=sucesso, 1=erro generico, 2=auth missing, 3=auth expired

## Sistema de Timing do VPD

- `tstart` e `tduration` estao em **milissegundos**
- `fileCuttedStart` e `fileCuttedDuration` estao em **segundos**
- `handledCuttedDuration` esta em **segundos** (duracao apos speed)
- Relacao: `tduration = handledCuttedDuration * 1000`
- Speed factor: `fileCuttedDuration / handledCuttedDuration`

Documentacao completa do formato VPD: `docs/vpd-format.md`

## Compatibilidade WSL

O script detecta automaticamente se o ffmpeg disponivel e o nativo do Linux ou o `.exe` do Windows. Quando usa `ffmpeg.exe`, converte caminhos WSL (`/mnt/c/...`) para Windows (`C:/...`) automaticamente. O diretorio temporario e criado na mesma particao do projeto para garantir acesso pelo ffmpeg Windows.

## Uso

```bash
# Fluxo completo: clean + enhance (padrao)
python3 vpd-enhance-audio/vpd-enhance-audio.py projeto.vpd

# Sem enhance (usa audio clean direto)
python3 vpd-enhance-audio/vpd-enhance-audio.py projeto.vpd --skip-enhance

# Gerar M4A com fade de 10ms
python3 vpd-enhance-audio/vpd-enhance-audio.py projeto.vpd -f m4a --fade 10

# Especificar arquivo de saida
python3 vpd-enhance-audio/vpd-enhance-audio.py projeto.vpd -o /caminho/saida.wav
```

| Opcao | Descricao | Padrao |
|-------|-----------|--------|
| `-f`, `--format` | Formato de saida: `wav`, `m4a`, `flac` | `wav` |
| `--fade` | Duracao do fade em milissegundos | `5` |
| `-o`, `--output` | Caminho personalizado para o arquivo de saida | `<projeto>-clean.<formato>` |
| `--skip-enhance` | Pula Adobe Enhance, usa audio clean direto no VPD | desativado |

## O que o Script Faz no VPD

Alem de gerar o audio, o script modifica o `.vpd`:

1. **Backup** — Cria `projeto.vpd.bak` antes de qualquer alteracao
2. **Muta MainVideoTrack** — Define `mute = true` no nivel da track
3. **Muta AudioTracks existentes** — Define `mute = true` no nivel da track
4. **Insere novo AudioTrack** — Adiciona uma track "Audio Enhanced" com o arquivo enhanced (ou clean) cobrindo toda a timeline
5. **Adiciona recurso** — Registra o arquivo de audio na `audiolist` do projeto

Para reverter: basta renomear `projeto.vpd.bak` de volta para `projeto.vpd`.

## Scripts Incluidos

| Script | Descricao |
|--------|-----------|
| `vpd-enhance-audio.py` | Script principal — gera audio clean, enhance, modifica VPD |
| `adobe-enhance.js` | Upload/download automatico no Adobe Podcast Enhance |
| `save-session.js` | Salva sessao Adobe (login manual unico) |
| `debug-enhance.js` | Debug do fluxo de enhance (testa modos headless) |

Os scripts JS usam Playwright (node_modules compartilhado em `playwright/` na raiz do projeto). O script Python configura `NODE_PATH` automaticamente ao invoca-los.

## Arquivos Gerados (nao commitados)

- `adobe-auth.json` — Sessao Adobe salva (expira apos dias/semanas)
- `debug-upload-fail.png` — Screenshot de debug em caso de falha no upload
