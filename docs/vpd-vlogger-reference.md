# VideoProc Vlogger — Program Reference

Documentation of the VideoProc Vlogger internal program structure, including presets, styles, Lua scripting API, effects catalog, and supported codecs. Based on analysis of the installation folder at `C:\Program Files (x86)\Digiarty\VideoProc Vlogger`.

For the `.vpd` project file format (JSON structure), see [vpd-format.md](vpd-format.md).

## Table of Contents

- [Subtitle Effect Presets](#subtitle-effect-presets)
- [Subtitle Styles](#subtitle-styles)
- [Lua Scripting API](#lua-scripting-api)
- [Text Editor Template](#text-editor-template)
- [Video Effects Catalog](#video-effects-catalog)
- [Motion Presets](#motion-presets)
- [LUT Presets](#lut-presets)
- [Blend Modes](#blend-modes)
- [Supported Codecs and Formats](#supported-codecs-and-formats)

---

## Subtitle Effect Presets

**Location:** `subtitle_effects/`

17 presets organized into 5 categories, each in its own subfolder.

### Preset Catalog

| ID | Folder | Category | Type | Default Duration | Resolution |
|----|--------|----------|------|-----------------|------------|
| `title_001` | `title1/` | Title | text | 5000ms | resize |
| `title_002` | `title2/` | Title | text | 5000ms | resize |
| `title_003` | `title3/` | Title | text | 5000ms | resize |
| `title_004` | `title4/` | Title | text | 5000ms | resize |
| `title_005` | `title5/` | Title | text | 5000ms | resize |
| `title_006` | `title6/` | Title | text | 5000ms | resize |
| `subtitle_001` | `subtitle1/` | Subtitle | text | 5000ms | resize |
| `subtitle_002` | `subtitle2/` | Subtitle | text | 5000ms | resize |
| `subtitle_003` | `subtitle3/` | Subtitle | text | 5000ms | resize |
| `subtitle_004` | `subtitle4/` | Subtitle | text | 5000ms | resize |
| `credit_001` | `credit1/` | Credits Title | opener | 7000ms | force 1920x1080 |
| `credit_002` | `credit2/` | Credits Title | opener | 7000ms | force 1920x1080 |
| `credit_003` | `credit3/` | Credits Title | opener | 7000ms | force 1920x1080 |
| `credit_004` | `credit4/` | Credits Title | opener | 7000ms | force 1920x1080 |
| `credit_005` | `credit5/` | Credits Title | opener | 7000ms | force 1920x1080 |
| `opener_006` | `opener7/` | Credits Title | opener | 7000ms | force 1920x1080 |
| `text_001` | `text/` | Text | editor | 5000ms | resize |

### Files per Preset Folder

| File | Purpose |
|------|---------|
| `configure.json` | Metadata and properties |
| `init.lua` | Initialization script (creates styles and dialogues) |
| `process.lua` | Processing script (applies formatting and animation) |
| `*.png` | Thumbnail preview |
| `*.mp4` | Video template (opener/credit presets only) |
| `template.json` | Editor template (`text_001` only, replaces Lua scripts) |

### configure.json Schema

```json
{
    "id": "title_001",
    "title": {
        "en": "Title 1",
        "ja": "タイトル 1",
        "zh-hant": "文字 1",
        "zh-hans": "文字 1",
        "fr": "Titre 1",
        "de": "Titel 1",
        "es": "Título 1",
        "it": "Titolo 1",
        "ko": "제목 1"
    },
    "group": "Title",
    "thumb": "Title1.png",
    "sort": "text",
    "init": "init.lua",
    "script": "process.lua",
    "type": "text",
    "initdur": 5000,
    "resize": true,
    "def": "time,fade,pos,alpha,border,font,color,bold,italic,underline",
    "files": []
}
```

| Field | Description |
|-------|-------------|
| `id` | Unique preset identifier (matches `resid` in VPD) |
| `title` | Multilingual display names (9 languages) |
| `group` | Category: `"Title"`, `"Subtitle"`, `"Credits Title"` |
| `thumb` | Thumbnail PNG filename |
| `sort` | Sort type: `"text"` (titles/subtitles), `"video"` (openers/credits) |
| `init` | Initialization Lua script filename |
| `script` | Processing Lua script filename (empty for editor type) |
| `type` | Effect type: `"text"` (Lua-based), `"editor"` (template-based), `"opener"` (video) |
| `initdur` | Initial duration in milliseconds |
| `resize` | Whether the effect resizes to project resolution |
| `def` | Comma-separated list of editable properties |
| `force` | Forced resolution (opener presets only, e.g., `"1920x1080"`) |
| `files` | Additional resource files (empty for built-in presets) |

**Editable properties (`def` field):**
- Title presets: `time,fade,pos,alpha,border,font,color,bold,italic,underline`
- Subtitle presets: `time,fade,pos,alpha,border,shadow,font,color,bold,italic,underline,add,rm`
- Credit/opener presets: `fade,pos,alpha,border,font,color,bold,italic,underline`

### group.json

Maps category names to multilingual labels:

```json
{
    "Credits Title": { "en": "Credit Titles", "ja": "オープニング", ... },
    "Subtitle": { "en": "Subtitles", "ja": "字幕", ... },
    "Title": { "en": "Titles", "ja": "タイトル", ... }
}
```

---

## Subtitle Styles

**Location:** `sub_styles/`

16 predefined subtitle style files (`style 1.json` through `style 16.json`). These are applied from the VideoProc Vlogger UI and map to dialogue-level fields in the VPD TextEffectBlock.

### Style JSON Fields

| Field | VPD Dialogue Field | Description |
|-------|-------------------|-------------|
| `name` | — | Display name |
| `order` | — | Sort order (1-16) |
| `ffontname` | `fontname` | Font family name |
| `fsize` | `fontsize` | Font size |
| `fblod` | `bold` | Bold (0/1) — note original typo "fblod" |
| `fitalic` | `italic` | Italic |
| `ful` | `underline` | Underline |
| `tspace` | `space` | Text spacing |
| `comp_bm` | `blendMode` | Composition blend mode |
| `comp_op` | `blendOpacity` | Composition opacity (0-100) |
| `cm_type` | `color_mode` | Color mode (0=solid, 1=gradient) |
| `cmf_v` | `fColor` | Fill color (ARGB uint32) |
| `cmf_op` | `fOpacity` | Fill opacity (0-100) |
| `cmg_b` | `gStart` | Gradient start color (ARGB) |
| `cmg_e` | `gStop` | Gradient end color (ARGB) |
| `cmg_op` | `gOpacity` | Gradient opacity (0-100) |
| `cmg_a` | `gAngle` | Gradient angle (degrees) |
| `bd_st` | `bdEnable` | Border/stroke enabled |
| `bd_c` | `bdColor` | Border color (ARGB) |
| `bd_s` | `bdSize` | Border size |
| `bd_op` | `bdOpacity` | Border opacity (0-100) |
| `bd_b` | `bdBlur` | Border blur |
| `sd_st` | `sdEnable` | Shadow enabled |
| `sd_t` | `sdType` | Shadow type |
| `sd_c` | `sdColor` | Shadow color (ARGB) |
| `sd_op` | `sdOpacity` | Shadow opacity (0-100) |
| `sd_d` | `sdDist` | Shadow distance |
| `thumb` | — | Base64-encoded PNG thumbnail |

### Color Format

Colors are stored as ARGB unsigned 32-bit integers:
- `4294967295` = `0xFFFFFFFF` = white
- `4278190080` = `0xFF000000` = black
- `4294940161` = `0xFFFFBD01` = amber/orange

---

## Lua Scripting API

Each text/subtitle preset uses Lua scripts (`init.lua` + `process.lua`) to create and format text objects.

### init.lua — Object Creation

The `execute(duration)` function creates styles and dialogues:

```lua
function execute(duration)
    -- Create base style
    local style = style.new()
    style:set_name("style1")
    style:set_outline(0)
    style:set_shadow(0)

    -- Create text dialogue
    local text1 = dialog.new()
    text1:set_layer(0)
    text1:set_time(0, 5000)        -- start, end (ms)
    text1:set_style("style1")
    text1:set_font("Arial", "Regular", 120)
    text1:set_text("YOUR TITLE HERE")
    text1:set_animation(11)
    text1:set_animation_time(800)
    text1:set_alignment(5)
    text1:set_xy(0.5, 0.5)

    -- Append to document
    local doc = document.get()
    doc:append(style)
    doc:append(text1)
    return true
end
```

### Available Methods

**Style object:**
- `style.new()` — Create new style
- `style:set_name(name)` — Set style name
- `style:set_outline(size)` — Border size (0=none, 1-6)
- `style:set_shadow(size)` — Shadow size (0=none, 1+)

**Dialog object:**
- `dialog.new()` — Create new text dialogue
- `text:set_layer(n)` — Stacking order
- `text:set_time(start, end)` — Timing within block (ms)
- `text:set_style(name)` — Reference style by name
- `text:set_font(family, style, size)` — Font specification
- `text:set_fontname(family, style)` — Font name only
- `text:set_fontsize(size)` — Font size only
- `text:set_text(string)` — Text content
- `text:set_bold(value)` — Bold (0/1 or true/false)
- `text:set_italic(value)` — Italic
- `text:set_underline(value)` — Underline
- `text:set_animation(id)` — Animation type ID
- `text:set_animation_time(ms)` — Animation duration
- `text:set_animation_delay(ms)` — Animation start delay
- `text:set_alignment(n)` — ASS alignment numpad (1-9)
- `text:set_xy(x, y)` — Normalized position (0.0-1.0)
- `text:set_color_mode(mode)` — 0=solid, 1=gradient
- `text:set_fill_color(color)` — Fill color via `util.pack(R, G, B)`
- `text:set_gradient_color(start, end)` — Gradient colors
- `text:set_gradient_angle(degrees)` — Gradient direction

**Document object:**
- `document.get()` — Get current document
- `doc:append(object)` — Add style or dialogue

**Utility:**
- `util.pack(R, G, B)` — Pack RGB into color value

### process.lua — Animation Processing

The `execute(dial)` function applies formatting:

```lua
function execute(dial)
    dial:start_fmt()
    dial:fmt_all()
    dial:animate_fmt()
    dial:end_fmt()
    return true
end
```

---

## Text Editor Template

**Location:** `subtitle_effects/text/template.json`

The `text_001` preset uses a template-based approach instead of Lua scripts, with character-level styling:

```json
{
    "type": "editor",
    "fonts": [
        { "name": "Arial", "path": "/Library/Fonts/Arial Bold.ttf" }
    ],
    "fragments": {
        "chars": [
            {
                "char": 84,           // Unicode code point (T)
                "ffn": "Arial",       // Font name
                "fsize": 148,         // Font size
                "fcolor": 4294967038, // Color (ARGB uint32)
                "bs": 0,              // Border size
                "bc": 4278190080,     // Border color
                "bb": 5,              // Border blur
                "st": 7,              // Shadow type
                "ss": 20,             // Shadow softness
                "sc": 4278207400,     // Shadow color
                "sb": 3               // Shadow blur
            }
        ],
        "lineSpace": 2,
        "charSpace": 0,
        "align": 0,
        "angle": 0.0,
        "x": 0.3, "y": 0.4,          // Normalized position
        "w": 0.4, "h": 0.2           // Normalized size
    }
}
```

---

## Video Effects Catalog

**Location:** `VideoEffect/`

124 effects available, all following the `basic_<Name>` naming convention for `resid`. Effect rendering is handled by `VideoBaseEffect.dll` using GLSL shaders.

### Transition Effects

| `resid` | Name |
|---------|------|
| `basic_Fade` | Fade |
| `basic_FadeColor` | Fade to Black |
| `basic_FadeColorWhite` | Fade to White |
| `basic_Fadegrayscale` | Fade to Grayscale |
| `basic_WipeUp` | Wipe Up |
| `basic_WipeDown` | Wipe Down |
| `basic_WipeLeft` | Wipe Left |
| `basic_WipeRight` | Wipe Right |
| `basic_Circle` | Circle |
| `basic_Circleopen` | Circle Open |
| `basic_CircleZoom` | Circle Zoom |
| `basic_CrossZoom` | Cross Zoom |
| `basic_Ripple` | Ripple |
| `basic_RAngular` | Angular Ripple |
| `basic_Directional` | Directional |
| `basic_Directionalwarp` | Directional Warp |
| `basic_Directionalwipe` | Directional Wipe |
| `basic_DoomScreenTransition` | Doom Screen |
| `basic_Doorway` | Doorway |
| `basic_GridFlip` | Grid Flip |
| `basic_InvertedPageCurl` | Inverted Page Curl |
| `basic_Morph` | Morph |
| `basic_Swap` | Swap |
| `basic_PolkaDotsCurtain` | Polka Dots Curtain |
| `basic_Windowblinds` | Window Blinds |
| `basic_Pinwheel` | Pinwheel |
| `basic_Bounce` | Bounce |
| `basic_BowTieHorizontal` | Bow Tie Horizontal |
| `basic_BowTieVertical` | Bow Tie Vertical |
| `basic_ButterflyWaveScrawler` | Butterfly Wave |
| `basic_Cannabisleaf` | Cannabis Leaf |
| `basic_UndulatingBurnOut` | Undulating Burn Out |

### Distortion/Wave Effects

`basic_WaterWave`, `basic_wave`, `basic_TapeWave`, `basic_Swirl`, `basic_Displacement`

### Blur/Noise Effects

`basic_LinearBlur`, `basic_Mosaic`, `basic_Pixelize`, `basic_Blur`, `basic_bw_noise`, `basic_color_noise`, `basic_denoise`

### Color/Filter Effects

`basic_burn`, `basic_gradient`, `basic_magnifier`, `basic_mask`, `basic_Kaleidoscope`, `basic_kaleidoscope_filter`, `basic_old_photo_filter`, `basic_old_tv_1`, `basic_old_tv_2`, `basic_oled`, `basic_vcr_filter`, `basic_chromatic_aberration_filter`, `basic_chromatic_aberration_red_shift_filter`, `basic_hor_color_filter`, `basic_ver_color_filter`, `basic_negative_blue`

### Artistic/Glitch Effects

`basic_cartton`, `basic_hand_drawing`, `basic_GlitchDisplace`, `basic_GlitchMemories`, `basic_rock_roll`, `basic_matrix_1`, `basic_matrix_2`, `basic_matrix_3`

### Particle/Weather Effects

`basic_meteorite`, `basic_meteor`, `basic_fireworks_1`, `basic_fireworks_2`, `basic_fire`, `basic_smoke`, `basic_snow_1`, `basic_snow_2`, `basic_rain_screen`, `basic_rain_storm`, `basic_glowworm`

### TikTok-Style Effects

`basic_douyin_ghost`, `basic_douyin_illusion`, `basic_douyin_rag`, `basic_douyin_shake`

### Special Effects

`basic_heart_filter`, `basic_Multiply_blend`, `basic_CrazyParametricFun`, `basic_Perlin`, `basic_Polar_function`, `basic_quake`, `basic_aibao`, `basic_digigrid`, `basic_digitime`, `basic_disturb`

---

## Motion Presets

**Location:** `Presets/MotionPresets/`

31 camera motion presets that populate `VideoCropper.dynamicNodes` in the VPD format. Listed in `preset.json` with multilingual titles.

### Available Presets

| ID | Name |
|----|------|
| `PushIn` | Push In |
| `RushPushIn` | Rush Push In |
| `PullAway` | Pull Away |
| `RushPullAway` | Rush Pull Away |
| `MoveRight` | Move Right |
| `MoveLeft` | Move Left |
| `MoveUp` | Move Up |
| `MoveDown` | Move Down |
| `LeftAndRight` | Left and Right |
| `UpAndDown` | Up and Down |
| `Rotate` | Rotate |
| `ReverseRotate` | Reverse Rotate |
| `ZoomRotate` | Zoom Rotate |
| `CinematicOpen` | Cinematic Open |
| `OpeningHorizontal` | Opening Horizontal |
| `EndHorizontal` | End Horizontal |
| `OpeningVertical` | Opening Vertical |
| `EndVertical` | End Vertical |
| `Heartbeat` | Heartbeat |
| `Quake` | Quake |
| `Earthquake` | Earthquake |
| `Jump` | Jump |
| `Multiplepull` | Multiple Pull |
| `Multiple_push` | Multiple Push |
| `Closeup` | Close Up |
| `look_at` | Scan |

### Preset JSON Structure

Each preset defines keyframe nodes:

```json
{
    "id": "MoveRight",
    "nodes": [
        {
            "time": 0,
            "duration": 0,
            "posX": { "type": 65, "value": 0.25 },
            "posY": { "type": 65, "value": 0.5 },
            "width": { "type": 64, "value": 0.5 },
            "height": { "type": 64, "value": 0.5 },
            "ratioMode": 10,
            "smoothType": 0,
            "smoothness": true
        },
        {
            "time": 1,
            "duration": 0,
            "posX": { "type": 65, "value": 0.75 },
            "posY": { "type": 33, "value": 0 },
            "width": { "type": 32, "value": 0 },
            "height": { "type": 32, "value": 0 },
            "ratioMode": 10,
            "smoothType": 0,
            "smoothness": true
        }
    ],
    "totalDuration": 10
}
```

Node `time` is normalized (0.0 = start, 1.0 = end). The `type` field on position/size values indicates the interpolation method.

---

## LUT Presets

**Location:** `OpenColor/lut.json`

90+ color grading presets organized by category. These map to `VideoLUT.LutName` in the VPD format.

### Categories

| Group | Presets |
|-------|---------|
| Group1 | Mono, B&W, Vivid, Warm, Cool, Less Expo, Bright, Dark |
| Group1 (cont.) | Travel 1-9, Food 1-6, Cinematic 1-9, Retro 1-6 |
| Group2 | Portrait Grayscale, Portrait Bright, Portrait Tone, Portrait Lowlight (multiple variants) |
| Group3 | Grassland 1-9, Sea 1-9, Night 1-9, Stylish 1-12 |

Color space management uses OpenColorIO (`config.ocio`) with supported spaces: linear, sRGB, rec709, Cineon, Gamma1.8, Gamma2.2, Gamma2.4.

---

## Blend Modes

Known blend mode names from the program binary. These correspond to the `Compositing.mode` integer in the VPD format:

- `normal` (mode: 0 — confirmed)
- `color_burn`
- `color_dodge`
- `hard_light`
- `hard_mix`
- `linear_burn`
- `linear_dodge`
- `linear_light`
- `pin_light`
- `soft_light`
- `vivid_light`

**Note:** The integer-to-name mapping beyond `0=normal` is not yet confirmed. These names were extracted from the program binary.

---

## Supported Codecs and Formats

VideoProc Vlogger bundles a custom FFmpeg build (N-102461-g8649f5dca6) with hardware acceleration support.

### Video Encoders

| Codec | Software | NVIDIA | AMD | Intel |
|-------|----------|--------|-----|-------|
| H.264/AVC | libx264 | h264_nvenc | h264_amf | h264_qsv |
| H.265/HEVC | libx265 | hevc_nvenc | hevc_amf | hevc_qsv |
| AV1 | libaom-av1, libsvtav1 | — | — | — |
| VP8 | libvpx | — | — | vp8_qsv |
| VP9 | libvpx-vp9 | — | — | vp9_qsv |
| MPEG-4 | libxvid | — | — | — |

### Audio Encoders

| Codec | Library |
|-------|---------|
| AAC | native + aac_mf |
| MP3 | libmp3lame |
| Opus | libopus |
| Vorbis | libvorbis |
| FLAC | native |
| AC-3 | native |
| PCM/WAV | multiple formats |

### Container Formats

**Output:** MP4, MOV, MKV, WebM, AVI, FLV, WAV, M4A, MP3, 3GP, ASF

### Hardware Acceleration

- **NVIDIA:** CUDA + NVENC (encoding), CUVID (decoding)
- **AMD:** AMF (encoding)
- **Intel:** Quick Sync Video (encoding + decoding)
- **Windows:** DXVA2, D3D11 (decoding), MediaFoundation (encoding)

### H.264 Encoding Options

Presets: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow, placebo

Profiles: baseline, main, high

Tune: film, animation, grain, stillimage, fastdecode, zerolatency
