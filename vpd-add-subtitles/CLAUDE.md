# vpd-add-subtitles — Legendas palavra-por-palavra para projetos VPD

## Sobre

Script Python que adiciona legendas estilo OpusClip (palavra-por-palavra com highlight) a projetos VideoProc Vlogger (.vpd). Transcreve o audio com Whisper, agrupa palavras em telas, e insere TextEffectBlocks no SubtitleTrack com destaque por cor + tamanho via ASS override tags.

**Estilo visual:** Carregado de um estilo salvo no VideoProc Vlogger (`--style my-style-1`). Palavra atual destacada com cor e tamanho maior (`\fs`). Cada palavra e um bloco independente na timeline, editavel individualmente na GUI. Blocos intercalados em 2 SubtitleTracks (A e B) para facilitar edicao.

## Como Funciona

1. **Detectar audio** — Procura `{projeto}-enhanced.wav` ou `{projeto}-clean.wav` na pasta do projeto (ou usa `--audio`)
2. **Transcrever com Whisper** — Roda `whisper` CLI com word_timestamps para obter timing por palavra. Salva o JSON como `{audio}-whisper.json` na pasta do projeto. Se o JSON ja existir, reutiliza sem rodar o Whisper novamente
3. **Agrupar palavras em telas** — Respeita max_chars (28), max_lines (2), e gap_threshold (1.5s) para quebrar telas. Calcula ponto de quebra considerando o pior caso (maior palavra da linha destacada a highlight_scale), inserindo `\N` explicito para manter quebra consistente entre blocos
4. **Carregar estilo** — Le o estilo do VideoProc Vlogger em `AppData/Roaming/Digiarty/VideoProc Vlogger/sub_styles/{nome}.json` e aplica todas as propriedades (fonte, cor, borda, sombra, etc.)
5. **Gerar TextEffectBlocks** — Um bloco por palavra. Cada bloco mostra o texto completo da tela com ASS override tags na palavra atual (cor + tamanho). 1 bloco = 1 item editavel na timeline
6. **Inserir no VPD** — Remove SubtitleTracks existentes, cria 2 tracks ("Subtitle A" e "Subtitle B") com blocos intercalados (palavras pares em A, impares em B) para facilitar edicao na GUI
7. **Backup** — Cria `projeto.vpd.bak` antes de modificar (se nao existir)
8. **Reset playhead** — Posiciona o playhead no inicio do projeto (via `.userdata`)

## Tecnica: ASS Override Tags

O VPD usa convencoes ASS internamente. O script usa `\c` (cor) e `\fs` (font size) inline no campo `text` dos dialogues:

```
{\c&HFF559B&\fs120}PALAVRA{\c&HFFFFFF&\fs100} resto do texto
```

- `\c&HFF559B&` — cor do destaque (formato ASS BGR)
- `\fs120` — tamanho maior para destaque
- `{\c&HFFFFFF&\fs100}` — reset explicito para cor/tamanho base

**Limitacoes descobertas no Vlogger:**
- `{\r}` (reset ASS) causa tachado — usar reset explicito em vez disso
- `\t()` (animacao ASS) aplica globalmente, nao por palavra — usar tamanho estatico
- O `styles[]` do bloco deve usar valores padrao do Vlogger (bold=false, fsize=20, outline=1, alignment=2) para evitar tachado — o dialogue sobrescreve tudo

## Uso

```bash
# Ativar conda env (whisper precisa de GPU)
conda activate pt-gpu

# Fluxo padrao (detecta audio, usa estilo my-style-1)
python3 vpd-add-subtitles/vpd-add-subtitles.py projeto.vpd

# Especificar estilo e cor de destaque
python3 vpd-add-subtitles/vpd-add-subtitles.py projeto.vpd --style my-style-1 --highlight-color "#00FF00"

# Usar 1 track em vez de 2
python3 vpd-add-subtitles/vpd-add-subtitles.py projeto.vpd --tracks 1

# Especificar audio manualmente
python3 vpd-add-subtitles/vpd-add-subtitles.py projeto.vpd --audio meu-audio.wav

# Forcar nova transcricao (apagar o JSON cache)
rm pasta-do-projeto/*-whisper.json
python3 vpd-add-subtitles/vpd-add-subtitles.py projeto.vpd

# Teste de ASS tags (inserir bloco de teste)
python3 vpd-add-subtitles/vpd-add-subtitles.py projeto.vpd --test-ass
```

## Opcoes

### Audio

| Opcao | Descricao | Padrao |
|-------|-----------|--------|
| `--audio PATH` | Audio para transcrever | detecta `*-enhanced.wav` |
| `--whisper-model MODEL` | tiny/base/small/medium/large | medium |
| `--language LANG` | Codigo do idioma | pt |

### Layout

| Opcao | Descricao | Padrao |
|-------|-----------|--------|
| `--max-lines N` | Max linhas por tela (1 ou 2) | 2 |
| `--max-chars N` | Max caracteres por linha | 28 |
| `--gap-threshold FLOAT` | Pausa minima (s) para quebrar tela | 1.5 |
| `--tracks N` | Numero de SubtitleTracks (1 ou 2) | 2 |

### Estilo

| Opcao | Descricao | Padrao |
|-------|-----------|--------|
| `--style NAME` | Nome do estilo do VideoProc Vlogger | my-style-1 |
| `--highlight-color HEX` | Cor da palavra em destaque | #9B55FF (roxo) |
| `--highlight-scale N` | Escala da palavra em destaque % | 120 |
| `--position-y FLOAT` | Posicao vertical 0.0-1.0 | 0.70 |
| `--margin N` | Margem lateral em pixels | 100 |

O estilo base (fonte, cor, borda, sombra) e carregado do arquivo JSON do VideoProc Vlogger em:
`/mnt/c/Users/vinia/AppData/Roaming/Digiarty/VideoProc Vlogger/sub_styles/{nome}.json`

### Teste

| Opcao | Descricao |
|-------|-----------|
| `--test-ass` | Inserir bloco de teste com ASS tags e sair |

## Cache de Transcricao

O Whisper salva o resultado como `{audio}-whisper.json` na pasta do projeto. Execucoes subsequentes reutilizam este arquivo automaticamente, pulando o Whisper. Para forcar nova transcricao, apague o arquivo JSON.

## Dependencias

- **Python 3** (stdlib apenas)
- **whisper** CLI — conda env `pt-gpu` (`conda activate pt-gpu`)

## Arquivos

| Arquivo | Descricao |
|---------|-----------|
| `vpd-add-subtitles.py` | Script principal |
| `CLAUDE.md` | Esta documentacao |

## Arquivos Gerados (nao commitados)

- `{audio}-whisper.json` — Cache da transcricao Whisper (na pasta do projeto VPD)
