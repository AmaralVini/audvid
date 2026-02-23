# Formato de Arquivo .vpd — VideoProc Vlogger

Documentacao da estrutura interna dos arquivos de projeto `.vpd` do VideoProc Vlogger, obtida por engenharia reversa a partir de projetos reais.

## Visao Geral

O `.vpd` e um arquivo **JSON puro** (UTF-8) com indentacao de 4 espacos. Um projeto tipico gera um arquivo de 400-500KB.

## Estrutura Raiz

```json
{
    "timeline":      {},   // Timeline principal com todas as tracks e clips
    "projinfo":      {},   // Metadados do projeto (nome, resolucao, fps)
    "videolist":     {},   // Pool de recursos de video
    "audiolist":     {},   // Pool de recursos de audio
    "imagelist":     {},   // Pool de recursos de imagens
    "subtitlelist":  {}    // Pool de recursos de legendas
}
```

---

## projinfo — Informacoes do Projeto

```json
"projinfo": {
    "name": "nome-do-projeto",
    "projectfile": "C:/Users/.../projeto.vpd",
    "savetime": {
        "year": 2026, "month": 2, "day": 22,
        "hour": 21, "minute": 59, "second": 1
    },
    "player": {
        "version": 0,
        "frameRateNum": 30,          // Numerador do frame rate
        "frameRateDen": 1,           // Denominador do frame rate (30/1 = 30fps)
        "resolutionW": 1080,         // Largura em pixels
        "resolutionH": 1920,         // Altura em pixels
        "clearR": 0.0,               // Cor de fundo R (0.0-1.0)
        "clearG": 0.0,               // Cor de fundo G
        "clearB": 0.0,               // Cor de fundo B
        "clearA": 1.0,               // Cor de fundo Alpha
        "showRefline": true,         // Mostrar linhas guia
        "lockRefline": false,        // Travar linhas guia
        "refLines": [],              // Linhas guia customizadas
        "volume": 1.0                // Volume master
    }
}
```

---

## timeline — Timeline Principal

### MainTimeline (raiz)

```json
"timeline": {
    "title": "MainTimeline",
    "type": "MainTimeline",
    "status": 0,
    "subitems": [ /* array de tracks */ ],
    "tstart": 0.0,
    "tduration": 1.7976931348623157e308,  // Float max = sem limite
    "context": 61397.33,                   // Duracao real do conteudo (ms)
    "connect": {}                          // Objeto de conectividade (geralmente vazio)
}
```

### Sistema de Timing

| Campo | Unidade | Descricao |
|-------|---------|-----------|
| `tstart` | milissegundos | Posicao inicial na timeline |
| `tduration` | milissegundos | Duracao na timeline |
| `context` | milissegundos | Duracao real do conteudo na track |
| `fileCuttedStart` | segundos | Ponto de inicio no arquivo fonte |
| `fileCuttedDuration` | segundos | Duracao recortada do arquivo fonte |
| `handledCuttedDuration` | segundos | Duracao apos aplicar velocidade |

**Relacao fundamental:** `tduration = handledCuttedDuration * 1000` (sempre)

**Speed factor:** `fileCuttedDuration / handledCuttedDuration`

---

## Tracks — Tipos e Hierarquia

A timeline contem 5+ tracks na seguinte ordem:

| # | Tipo | Descricao | Possui subitems |
|---|------|-----------|-----------------|
| 1 | `MainVideoTrack` | Track principal de video | Sim (MediaFileBlock) |
| 2 | `OverlayTrack` | Sobreposicoes de video | Nao, se vazia |
| 3 | `VideoEffectTrack` | Efeitos visuais | Nao, se vazia |
| 4 | `AudioTrack` | Tracks de audio (pode haver multiplas) | Sim (MediaFileBlock) |
| 5 | `SubtitleTrack` | Legendas/textos | Nao, se vazia |

### Propriedades comuns a todas as tracks (exceto MainVideoTrack)

```json
{
    "title": "Audio Track",
    "type": "AudioTrack",
    "status": 0,
    "subitems": [],            // Presente apenas se a track tem clips
    "tstart": 0.0,
    "tduration": 1.7976931348623157e308,
    "context": 0.0,           // 0.0 se vazia
    "opacity": 100,            // 0-100
    "mute": false              // Muta a track inteira
}
```

**Nota:** `MainVideoTrack` possui as mesmas propriedades (`tstart`, `tduration`, `context`, `opacity`, `mute`) APOS o array `subitems`. Tracks vazias nao incluem o campo `subitems`.

---

## MediaFileBlock — Clips na Timeline

Cada clip em qualquer track e um `MediaFileBlock`:

```json
{
    "title": "nome-do-arquivo",
    "type": "MediaFileBlock",
    "background": 4232007423,          // Cor RGBA (inteiro)
    "foreground": 1216461823,          // Cor RGBA (inteiro)
    "status": 0,                        // 0=normal, 512=locked
    "uuid": "{BB7DC41C-E7DF-4D7D-BFF9-2C1D5DB1CBC5}",
    "tstart": 0.0,                      // Posicao na timeline (ms)
    "tduration": 1333.0,               // Duracao na timeline (ms)
    "restype": "MediaFileResource",
    "resid": "9A24C29B00426678DF1A82D751895A31",  // UUID do recurso
    "attribute": { /* ver abaixo */ }
}
```

### attribute — Atributos do Clip

```json
"attribute": {
    "version": 0,
    "type": 3,                // 2=audio-only, 3=video+audio
    "videoIndex": 0,          // Indice do stream de video (-1 se desabilitado)
    "audioIndex": 1,          // Indice do stream de audio (-1 se desabilitado)
    "videoEnabled": true,
    "audioEnabled": true,
    "VideoAttribute": {},     // null para clips audio-only
    "AudioAttribute": {},
    "SpeedAttribute": {}
}
```

---

## VideoAttribute — Pipeline de Efeitos de Video

Contem 11 sub-modulos de processamento. Cada um possui um `baseData` com flags de ativacao:

```json
"baseData": {
    "version": 0,
    "valid": false,                    // true = efeito ativo
    "fileTotalDuration": 68.5058,      // Duracao total do arquivo (s)
    "fileCuttedStart": 0.8,            // Inicio do recorte (s)
    "fileCuttedDuration": 1.333,       // Duracao do recorte (s)
    "blockDuration": 1.333             // Duracao do bloco na timeline (s)
}
```

### 1. LensCorrection — Correcao de Lente

```json
"LensCorrection": {
    "valid": false,
    "focalPosX": 0.5, "focalPosY": 0.5,
    "hDeg": 118.2, "vDeg": 69.5, "dDeg": 133.6,
    "k2": 0.022,
    "cameraID": "custom", "fovID": "custom"
}
```

### 2. VideoCropper — Recorte e Pan

```json
"VideoCropper": {
    "rectData": {
        "srcWidth": 1080, "srcHeight": 1920,
        "targetWidth": 1080, "targetHeight": 1920
    },
    "isPic": false,
    "staticNode": {
        "time": 0.0, "duration": 0.0,
        "posX": 0.5, "posY": 0.5,
        "sizeX": 1.0, "sizeY": 1.0,
        "ratioMode": 10, "angle": 0.0,
        "smoothness": true, "smoothType": 0, "pod": 0.0
    },
    "dynamicNodes": []    // Keyframes de animacao
}
```

### 3. BaseTransform — Rotacao e Flip

```json
"BaseTransform": {
    "angle": 0,           // Rotacao em graus
    "vFlip": true          // Flip vertical
}
```

### 4. ChromaKey — Chroma Key

```json
"ChromaKey": {
    "red": 0, "green": 255, "blue": 0,
    "CHROMAKEY_TOLERANCE": 26,
    "CHROMAKEY_SMOOTHNESS": 23,
    "CHROMAKEY_EDGE_THICKNESS": 0,
    "CHROMAKEY_EDGE_FEATHER": 0
}
```

### 5. VideoLUT — Tabela de Cor (LUT)

```json
"VideoLUT": {
    "LutName": "",         // Nome do arquivo .cube/.3dl
    "strength": 1.0        // Intensidade (0.0-1.0)
}
```

### 6. ColorEditor — Correcao de Cor

```json
"ColorEditor": {
    "COLOR_TEMPERATURE": 0.0, "COLOR_TINT": 0.0,
    "COLOR_EXPOSURE": 0.0, "COLOR_BRIGHTNESS": 0.0,
    "COLOR_CONTRAST": 0.0, "COLOR_SATURATION": 0.0,
    "COLOR_VIBRANCE": 0.0, "COLOR_HIGHLIGHTS": 0.0,
    "COLOR_SHADOWS": 0.0, "COLOR_WHITES": 0.0, "COLOR_BLACKS": 0.0,
    "HSL_RED":    { "HSL_HUE": 0, "HSL_SAT": 0, "HSL_LUM": 0 },
    "HSL_ORANGE": { "HSL_HUE": 0, "HSL_SAT": 0, "HSL_LUM": 0 },
    "HSL_YELLOW": { "HSL_HUE": 0, "HSL_SAT": 0, "HSL_LUM": 0 },
    "HSL_GREEN":  { "HSL_HUE": 0, "HSL_SAT": 0, "HSL_LUM": 0 },
    "HSL_CYAN":   { "HSL_HUE": 0, "HSL_SAT": 0, "HSL_LUM": 0 },
    "HSL_BLUE":   { "HSL_HUE": 0, "HSL_SAT": 0, "HSL_LUM": 0 },
    "HSL_PURPLE": { "HSL_HUE": 0, "HSL_SAT": 0, "HSL_LUM": 0 }
}
```

### 7. Sharpen — Nitidez

```json
"Sharpen": {
    "amount": 500,     // 0-1000
    "radius": 2,
    "threshold": 0
}
```

### 8. Denoise — Reducao de Ruido

```json
"Denoise": {
    "enableDenoise": false,
    "deviation": 5.0, "coefficient": 2.0,
    "edgeThreshold": 0.3,
    "enableAutoLevel": false, "autoLevelK1": 0.5
}
```

### 9. VignetteEditor — Vinheta

```json
"VignetteEditor": {
    "VIGNETTE_AMOUNT": 0,       // Intensidade
    "VIGNETTE_SIZE": 100,        // Tamanho
    "VIGNETTE_ROUNDNESS": 0,     // Arredondamento
    "VIGNETTE_FEATHER": 50,      // Suavidade da borda
    "VIGNETTE_INNER_LIGHT": 0    // Luz interna
}
```

### 10. VideoTransformer — Posicao, Escala, Fade

```json
"VideoTransformer": {
    "rectData": {
        "srcWidth": 1080, "srcHeight": 1920,
        "targetWidth": 1080, "targetHeight": 1920,
        "centerPosX": 0.5, "centerPosY": 0.5,
        "sizeX": 1.0, "sizeY": 1.0,
        "angle": 0.0
    },
    "overlay": false,
    "fadeInDuration": 0.2,        // Duracao do fade-in (s)
    "fadeOutDuration": 0.0,       // Duracao do fade-out (s)
    "fadeInDirect": 255,          // Direcao do fade-in (255=normal)
    "fadeOutDirect": 255,         // Direcao do fade-out
    "baseInfoInited": true
}
```

### 11. Compositing — Blending e Opacidade

```json
"Compositing": {
    "mode": 0,                // Modo de blending (0=normal)
    "opacity": 1.0,           // 0.0-1.0
    "fadeInDuration": 0.2,
    "fadeOutDuration": 0.0,
    "fadeInEnabeld": false,    // Nota: typo original ("Enabeld")
    "fadeOutEnabled": false
}
```

---

## AudioAttribute — Atributos de Audio

```json
"AudioAttribute": {
    "version": 0,
    "mute": false,
    "fadeInDuration": 0.0,     // Duracao do fade-in (s)
    "fadeOutDuration": 0.0,    // Duracao do fade-out (s)
    "multiple": 1.0,           // Multiplicador de volume
    "pitch": 1.0,              // Ajuste de pitch
    "pitchType": 1             // Tipo de algoritmo de pitch
}
```

---

## SpeedAttribute — Velocidade e Curvas

```json
"SpeedAttribute": {
    "version": 0,
    "reversePlay": false,          // Reproducao reversa
    "Speed": {
        "version": 0,
        "baseData": {
            "version": 0,
            "fileTotalDuration": 68.5058,       // Duracao total do arquivo (s)
            "fileCuttedStart": 0.8,             // Inicio do recorte no fonte (s)
            "fileCuttedDuration": 1.333,        // Duracao original recortada (s)
            "handledTotalDuration": 68.5058,    // Duracao total apos speed
            "handledCuttedStart": 0.8,          // Inicio recortado apos speed (s)
            "handledCuttedDuration": 1.333      // Duracao recortada apos speed (s)
        },
        "curve": "TmM0AQQ...",   // Curva de velocidade (base64)
        "extraSpeed": 1.0,        // Multiplicador global de velocidade
        "audioSpeedRate": false    // Se o pitch e preservado na mudanca de velocidade
    }
}
```

### Formato da Curva de Velocidade

O campo `curve` contem dados binarios codificados em Base64:
- **Magic bytes:** `4e633401` (ASCII: "Nc4" + byte de versao)
- **Conteudo:** Keyframes definindo velocidade variavel ao longo do clip
- **Tamanho tipico:** 500-700 bytes por curva

Para velocidade constante, a relacao `fileCuttedDuration / handledCuttedDuration` da o fator de velocidade diretamente, sem necessidade de interpretar a curva.

---

## Resource Lists — Pools de Recursos

Quatro listas de recursos na raiz do JSON:

### videolist

```json
"videolist": {
    "title": "Video",
    "type": "ResourceLists",
    "status": 0,
    "subitems": [
        {
            "title": "nome-do-video",
            "type": "MediaFileResource",
            "status": 0,
            "uuid": "9A24C29B00426678DF1A82D751895A31",
            "path": "C:/Users/.../video.mp4",       // Caminho absoluto
            "duration": 68.5058                      // Duracao em segundos
        }
    ]
}
```

### audiolist

```json
"audiolist": {
    "title": "Music",
    "type": "ResourceLists",
    "status": 0,
    "subitems": [
        {
            "title": "audio-export-0",
            "type": "MediaFileResource",
            "status": 34359738880,                   // Flag especial para audio
            "uuid": "F6AC9619932279D49D8FC537E3100FA9",
            "path": "audio-export-0.wav",            // Pode ser relativo ao projeto
            "duration": 1.833
        }
    ]
}
```

### imagelist

```json
"imagelist": {
    "title": "Picture",
    "type": "ResourceLists",
    "status": 0,
    "scapegoat": []    // Usa "scapegoat" em vez de "subitems"
}
```

### subtitlelist

```json
"subtitlelist": {
    "title": "Subtitle",
    "type": "ResourceLists",
    "status": 0
    // Nao possui "subitems" quando vazia
}
```

### Referencia de Recursos

Os clips na timeline referenciam recursos via `resid` → `uuid`:
- `MediaFileBlock.resid` = `ResourceItem.uuid`
- Os UUIDs em recursos **nao** possuem chaves `{}`
- Os UUIDs em blocos da timeline **possuem** chaves `{}`

---

## Arquivos Auxiliares do Projeto

Cada pasta de projeto `.vpd` contem:

| Arquivo | Descricao |
|---------|-----------|
| `projeto.vpd` | Arquivo principal do projeto (JSON) |
| `projeto.png` | Thumbnail do projeto |
| `projeto.userdata` | Estado do editor (zoom, posicao, paths) |
| `EncoderOption.json` | Codec de video/audio selecionado |
| `EncoderProfile.json` | Preset de encoding (bitrate, sample rate) |
| `ico.ico` | Icone da pasta |
| `desktop.ini` | Configuracao de icone do Windows |
| `*.wav` | Arquivos de audio exportados/importados |

### userdata

```json
{
    "environment": {
        "audoSnap": 1,
        "blockMovable": 1,
        "timelinePercent": 40.0,
        "timelinePlayPos": 58500.0,
        "timelineVisibleStart": 0.0,
        "timelineVisibleDuration": 14630.97,
        "expFormat": "M4A",
        "expFPSNum": 30, "expFPSDen": 1,
        "General Movie path": "C:/Users/.../Videos",
        "General Music path": "C:/Users/.../Music",
        "General Image path": "C:/Users/.../Imagens",
        "General Subtitle path": "C:/Users/.../Videos"
    }
}
```

### EncoderProfile.json

```json
{
    "profiles": {
        "m4a": {
            "recently": {
                "audio": {
                    "audioEnabled": true,
                    "aCodec": 2,
                    "audioSampleRate": 44100,
                    "audioBitrate": 128000,
                    "audioChannel": 2,
                    "audioChannelLayout": 3,
                    "audioBtMode": 1
                }
            }
        }
    },
    "version": 1
}
```

### EncoderOption.json

```json
{
    "video_options": { "h264_nvenc": { "recently": {} }, "chosen": "recently" },
    "audio_options": { "aac": { "recently": {} }, "chosen": "" },
    "version": 1
}
```
