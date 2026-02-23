# .vpd File Format — VideoProc Vlogger

Internal structure documentation for VideoProc Vlogger `.vpd` project files, obtained through reverse engineering from real projects.

## Overview

A `.vpd` file is **plain JSON** (UTF-8) with 4-space indentation. A typical project generates a 400KB-2.5MB file depending on complexity.

## Table of Contents

- [Root Structure](#root-structure)
- [projinfo — Project Information](#projinfo--project-information)
- [timeline — Main Timeline](#timeline--main-timeline)
- [Tracks — Types and Hierarchy](#tracks--types-and-hierarchy)
- [Block Types on the Timeline](#block-types-on-the-timeline)
- [MediaFileBlock — Audio/Video Clips](#mediafileblock--audiovideo-clips)
- [ImageFileBlock — Images on the Timeline](#imagefileblock--images-on-the-timeline)
- [TransitionBlock — Transitions Between Clips](#transitionblock--transitions-between-clips)
- [TextEffectBlock — Subtitles/Text](#texteffectblock--subtitlestext)
- [VideoEffectBlock — Visual Effects](#videoeffectblock--visual-effects)
- [VideoAttribute — Video Effects Pipeline](#videoattribute--video-effects-pipeline)
- [AudioAttribute — Audio Attributes](#audioattribute--audio-attributes)
- [SpeedAttribute — Speed and Curves](#speedattribute--speed-and-curves)
- [connect — Effect Connection Graph](#connect--effect-connection-graph)
- [Block Grouping](#block-grouping)
- [status Field — Flag Bitmask](#status-field--flag-bitmask)
- [Resource Lists — Resource Pools](#resource-lists--resource-pools)
- [Project Auxiliary Files](#project-auxiliary-files)

---

## Root Structure

```json
{
    "timeline":      {},   // Main timeline with all tracks and clips
    "projinfo":      {},   // Project metadata (name, resolution, fps)
    "videolist":     {},   // Video resource pool
    "audiolist":     {},   // Audio resource pool
    "imagelist":     {},   // Image resource pool
    "subtitlelist":  {}    // Subtitle resource pool
}
```

---

## projinfo — Project Information

```json
"projinfo": {
    "name": "project-name",
    "projectfile": "C:/Users/.../project.vpd",
    "savetime": {
        "year": 2026, "month": 2, "day": 22,
        "hour": 21, "minute": 59, "second": 1
    },
    "player": {
        "version": 0,
        "frameRateNum": 30,          // Frame rate numerator
        "frameRateDen": 1,           // Frame rate denominator (30/1 = 30fps)
        "resolutionW": 1080,         // Width in pixels
        "resolutionH": 1920,         // Height in pixels
        "clearR": 0.0,               // Background color R (0.0-1.0)
        "clearG": 0.0,               // Background color G
        "clearB": 0.0,               // Background color B
        "clearA": 1.0,               // Background color Alpha
        "showRefline": true,         // Show guide lines
        "lockRefline": false,        // Lock guide lines
        "refLines": [],              // Custom guide lines
        "volume": 1.0                // Master volume
    }
}
```

---

## timeline — Main Timeline

### MainTimeline (root)

```json
"timeline": {
    "title": "MainTimeline",
    "type": "MainTimeline",
    "status": 0,
    "subitems": [ /* array of tracks */ ],
    "tstart": 0.0,
    "tduration": 1.7976931348623157e308,  // Float max = no limit
    "context": 61397.33,                   // Actual content duration (ms)
    "connect": {},                         // Effect connection graph (see Connect section)
    "bookmarks": []                        // Timeline markers (see Bookmarks section)
}
```

### Bookmarks

The `bookmarks` array at the timeline root contains user-placed markers:

```json
"bookmarks": [
    {
        "title": "",
        "type": "Bookmark",
        "status": 0,
        "starttime": 29700.0     // Position on the timeline (ms)
    }
]
```

The `title` field is typically empty. `starttime` is in milliseconds.

### Timing System

| Field | Unit | Description |
|-------|------|-------------|
| `tstart` | milliseconds | Start position on the timeline |
| `tduration` | milliseconds | Duration on the timeline |
| `context` | milliseconds | Last clip endpoint on the track (`tstart + tduration` of last clip) |
| `fileCuttedStart` | seconds | Start point in the source file |
| `fileCuttedDuration` | seconds | Trimmed duration from the source file |
| `handledCuttedDuration` | seconds | Duration after applying speed |

**Fundamental relation:** `tduration = handledCuttedDuration * 1000` (always)

**Speed factor:** `fileCuttedDuration / handledCuttedDuration`

---

## Tracks — Types and Hierarchy

The timeline contains 5+ tracks in the following order (there can be multiple of each type except MainVideoTrack and VideoEffectTrack):

| # | Type | Description | Content |
|---|------|-------------|---------|
| 1 | `MainVideoTrack` | Main video track | `MediaFileBlock` / `ImageFileBlock` + `transitions` |
| 2+ | `OverlayTrack` | Video/image overlays | `MediaFileBlock` / `ImageFileBlock` |
| 3 | `VideoEffectTrack` | Visual effects | `VideoEffectBlock` |
| 4+ | `AudioTrack` | Audio tracks | `MediaFileBlock` |
| 5+ | `SubtitleTrack` | Subtitles/text | `TextEffectBlock` |

### Multiple Track Naming

Track titles are free-form strings. The default naming pattern uses the base name for the first track (e.g., `"Audio Track"`) and appends a numeric suffix without space for additional tracks: `"Audio Track1"`, `"Audio Track2"`, etc. However, tracks can be renamed to any title by the user.

### Common Properties for All Tracks

```json
{
    "title": "Audio Track",
    "type": "AudioTrack",
    "status": 0,                   // 0=normal, 1=disabled
    "subitems": [],                // Present only if the track has clips
    "tstart": 0.0,
    "tduration": 1.7976931348623157e308,
    "context": 0.0,               // 0.0 if empty
    "opacity": 100,                // 0-100
    "mute": false                  // Mutes the entire track
}
```

**Note:** `MainVideoTrack` has the same properties (`tstart`, `tduration`, `context`, `opacity`, `mute`) AFTER the `subitems` and `transitions` arrays. Empty tracks do not include the `subitems` field.

---

## Block Types on the Timeline

Five block types can appear on tracks:

| Type | Track | `restype` | `resid` |
|------|-------|-----------|---------|
| `MediaFileBlock` | MainVideoTrack, OverlayTrack, AudioTrack | `MediaFileResource` | MD5 hex hash |
| `ImageFileBlock` | MainVideoTrack, OverlayTrack | `MediaFileResource` | UUID with braces `{...}` |
| `VideoEffectBlock` | VideoEffectTrack | `VideoEffectResource` | Preset ID (e.g., `basic_mask`) |
| `TextEffectBlock` | SubtitleTrack | `TextEffectResource` | Preset ID (e.g., `title_001`) |
| `TransitionBlock` | MainVideoTrack (`transitions`) | `VideoTransiResource` | Preset ID (e.g., `basic_Fade`) |

---

## MediaFileBlock — Audio/Video Clips

```json
{
    "title": "filename",
    "type": "MediaFileBlock",
    "background": 4232007423,          // RGBA color (integer)
    "foreground": 1216461823,          // RGBA color (integer)
    "status": 0,                        // See status table
    "uuid": "{BB7DC41C-E7DF-4D7D-BFF9-2C1D5DB1CBC5}",
    "tstart": 0.0,                      // Position on the timeline (ms)
    "tduration": 1333.0,               // Duration on the timeline (ms)
    "restype": "MediaFileResource",
    "resid": "9A24C29B00426678DF1A82D751895A31",  // Resource hash
    "attribute": { /* see below */ }
}
```

### attribute — Clip Attributes

```json
"attribute": {
    "version": 0,
    "type": 3,                // 0=image, 1=video-only, 2=audio-only, 3=video+audio
    "videoIndex": 0,          // Video stream index (-1 if no video)
    "audioIndex": 1,          // Audio stream index (-1 if no audio)
    "videoEnabled": true,
    "audioEnabled": true,
    "VideoAttribute": {},     // null when type=2 (audio-only)
    "AudioAttribute": {},
    "SpeedAttribute": {}
}
```

**`attribute.type` values:**

| Value | Description | `videoEnabled` | `audioEnabled` |
|-------|-------------|----------------|----------------|
| `0` | Image (ImageFileBlock) | true | false |
| `1` | Video without audio | true | false |
| `2` | Audio without video | false | — |
| `3` | Video + audio | true | true |

---

## ImageFileBlock — Images on the Timeline

Used in `OverlayTrack` and `MainVideoTrack` for static images (PNG, JPG):

```json
{
    "title": "image",
    "type": "ImageFileBlock",
    "background": 4181064959,
    "foreground": 1216461823,
    "status": 0,
    "uuid": "{FD9BD321-3393-48AF-8C2B-446676096500}",
    "tstart": 0.0,
    "tduration": 5000.0,
    "restype": "MediaFileResource",
    "resid": "{A465C61F-FC2D-4208-A7CB-6BEA719D9C0C}",
    "attribute": {
        "version": 0,
        "type": 0,                    // Always 0 for images
        "videoIndex": 0,
        "audioIndex": -1,             // Always -1 (no audio)
        "videoEnabled": true,
        "audioEnabled": false,
        "VideoAttribute": {},         // Full 11 sub-modules (same as MediaFileBlock)
        "AudioAttribute": null,       // Always null for images
        "SpeedAttribute": {}
    }
}
```

Differences vs `MediaFileBlock`:
- `attribute.type` = `0`
- `AudioAttribute` = `null` (explicitly null, not absent)
- `VideoCropper.isPic` = `true`
- `VideoTransformer.rectData` includes `centerPosX/Y`, `sizeX/Y`, `angle` even on MainVideoTrack (images need position/scale since their resolution differs from the project)
- `resid` uses UUID format with braces `{...}`
- `SpeedAttribute.Speed` has no `baseData` wrapper — fields are directly in the `Speed` object (no `curve`). Also, `extraSpeed` and `audioSpeedRate` are at the `SpeedAttribute` level (siblings of `Speed`), not inside `Speed`

---

## TransitionBlock — Transitions Between Clips

The `transitions` array on `MainVideoTrack` (sibling of `subitems`):

```json
{
    "title": "Video Track",
    "type": "MainVideoTrack",
    "subitems": [ /* clips */ ],
    "transitions": [
        {
            "title": "Fade",
            "type": "TransitionBlock",
            "status": 0,
            "uuid": "{B7B610B3-...}",
            "tstart": 73800.0,               // Position at the cut point (ms)
            "tduration": 200.0,              // Transition duration (ms)
            "restype": "VideoTransiResource",
            "resid": "basic_Fade",           // Preset ID (not a UUID)
            "attribute": {
                "version": 0,
                "duration": 0.2,             // Duration in seconds (= tduration/1000)
                "Transition type": {         // Note: key with space
                    "version": 0,
                    "value": 0.0,
                    "value2": 0.0,
                    "r": 0, "g": 0, "b": 0,  // Transition color
                    "transi_type": 1,
                    "pic_path": ""            // Path for custom transition
                }
            }
        }
    ]
}
```

**Observed transition presets:**

| `resid` | `title` |
|---------|---------|
| `basic_Fade` | Fade |
| `basic_FadeColor` | Fade to Black |
| `basic_Fadegrayscale` | Fade to Gray |
| `basic_Ripple` | Ripple |
| `basic_WipeLeft` | Wipe Left |
| `basic_WipeRight` | Wipe Right |

All 124 available transition/effect IDs follow the `basic_<Name>` pattern. See [vpd-vlogger-reference.md](vpd-vlogger-reference.md) for the full catalog.

---

## TextEffectBlock — Subtitles/Text

Used in `SubtitleTrack`:

```json
{
    "title": "Title 1",
    "type": "TextEffectBlock",
    "background": 4229689855,
    "foreground": 1216461823,
    "status": 0,
    "uuid": "{23BFC5C1-...}",
    "tstart": 2700.0,
    "tduration": 1500.0,
    "restype": "TextEffectResource",
    "resid": "title_001",                // Title preset
    "attribute": {
        "version": 1,
        "width": 1920,
        "height": 1080,
        "leftTimestamp": -0.1,
        "rightTimestamp": 1.4,
        "dialogues": [ /* see below */ ],
        "styles": [ /* see below */ ]
    }
}
```

### Preset IDs (`resid`)

| `resid` | Category | Default duration |
|---------|----------|-----------------|
| `title_001` – `title_006` | Titles (6 presets) | 5000ms |
| `subtitle_001` – `subtitle_004` | Subtitles (4 presets) | 5000ms |
| `credit_001` – `credit_005` | Credits (5 presets) | 7000ms |
| `opener_006` | Opener (1 preset) | 7000ms |
| `text_001` | Text editor (1 preset) | 5000ms |

See [vpd-vlogger-reference.md](vpd-vlogger-reference.md) for preset internals (configure.json, Lua scripts, style files).

### Title vs Subtitle Patterns

| Property | Title presets | Subtitle presets |
|----------|-------------|-----------------|
| Font size | 120–220pt | 30–48pt |
| Position (posY) | 0.5 (center) | 0.72–0.95 (bottom) |
| Shadow | Typically disabled | Typically enabled |
| Outline | Varies (0–6) | Consistent (2) |
| style.outline | 0.0–6.0 | 2.0 |
| style.shadow | 0.0 | 2.0 |

### Attribute Fields

- `width`/`height`: Canvas resolution (matches project resolution)
- `leftTimestamp`/`rightTimestamp`: Editor viewport artifacts in seconds — **not clip timing**. Reflect the editor's visible range when the block was last edited. Ignore for parsing/generation.
- `version`: Always `1` for TextEffectBlock attributes (unlike `0` for other attribute types)

### dialogues — Text Entries

Each entry in `dialogues` defines a text element. A single block can contain **multiple dialogues** for sequential text segments (each with its own `start`/`end` within the block):

```json
{
    "idx": 0,
    "layer": 0,
    "start": 0,                    // Start within block (ms)
    "end": 1499,                   // End within block (ms)
    "style": "style1",            // Reference to name in styles[]
    "name": "",
    "ml": 0, "mr": 0, "mv": 0,   // Margins (left, right, vertical)
    "effect": "",
    "text": "TEXT HERE",
    "animation": 13,              // Animation type ID (see table)
    "has_default": false,          // true = text not edited from preset default
    "animation_delay": 0,
    "animation_time": 300,        // Animation duration (ms)
    "fontname": "PalatinoLinotype-Bold",
    "fontsize": 120.0,
    "bold": 0,                    // 0 or 1 (int, not bool — unlike styles where it's bool)
    "italic": false,
    "underline": false,
    "textAlign": 1,
    "alignment": 5,               // ASS alignment numpad (see table)
    "space": 0.0,
    "rotation": 0.0,
    "scale": 100.0,
    "posX": 0.5,                  // Normalized position (0.0-1.0)
    "posY": 0.8,
    "blendMode": 0,
    "blendOpacity": 100,
    "color_mode": 0,              // 0=solid, 1=gradient
    "fColor": 4294967295,         // Fill color (ARGB uint32)
    "fOpacity": 95,               // Fill opacity (%)
    "gStart": 4294967295,         // Gradient start color
    "gStop": 4294967295,          // Gradient end color
    "gOpacity": 100,
    "gAngle": 0,                  // Gradient angle (degrees)
    "bdEnable": true,             // Border/outline enabled
    "bdColor": 4278190080,
    "bdSize": 6,
    "bdOpacity": 61,
    "bdBlur": 7,
    "sdEnable": false,            // Shadow enabled
    "sdType": 7,
    "sdColor": 4286611584,
    "sdOpacity": 57,
    "sdDist": 6
}
```

**Animation type IDs (observed values):**

| Value | Description |
|-------|-------------|
| `0` | No animation |
| `1` | Fade-in left-to-right |
| `2` | Slide right-to-left |
| `5` | Animation variant |
| `11` | Text entrance |
| `12` | Rise/scroll |
| `13` | Entrance bottom-up with fade |
| `16` | Subtitle entrance |

Gaps in numbering (3, 4, 6–10, 14–15) suggest additional animation types exist.

**ASS alignment numpad:**

```
7 (top-left)      8 (top-center)      9 (top-right)
4 (mid-left)      5 (mid-center)      6 (mid-right)
1 (bottom-left)   2 (bottom-center)   3 (bottom-right)
```

**Color format:** Colors are stored as ARGB unsigned 32-bit integers. Common values: `4294967295` = `0xFFFFFFFF` (white), `4278190080` = `0xFF000000` (black).

### Multiple Dialogues and Multiline Text

A single TextEffectBlock can display text in two ways:

1. **Multiple dialogues** — sequential segments with different `start`/`end` within the block:
   - Dialogue 0: `start: 0, end: 2500` — "First line"
   - Dialogue 1: `start: 2500, end: 5000` — "Second line"

2. **`\N` hard newline** (ASS convention) — multiline within a single dialogue:
   - `"text": "First line\\NSecond line"`

### styles — Style Definitions (ASS format)

The `styles` array always contains exactly one entry named `"style1"` serving as the ASS base style. **Dialogue-level fields override these values** for actual rendering.

```json
{
    "idx": 0,
    "name": "style1",
    "fname": "Arial",
    "fsize": 20.0,
    "c1": 4294967295,             // Primary color (ARGB)
    "c2": 3690987520,             // Secondary color
    "c3": 4278190080,             // Outline color
    "c4": 3690987520,             // Background color
    "bold": false,
    "italic": false,
    "underline": false,
    "strikeOut": false,
    "scalex": 100, "scaley": 100,
    "spacing": 0,
    "angle": 0,
    "borderStyle": 1,
    "outline": 0.0,               // Title: 0.0-6.0, Subtitle: 2.0
    "shadow": 0.0,                // Title: 0.0, Subtitle: 2.0
    "alignment": 2,               // ASS alignment numpad
    "ml": 10, "mr": 10, "mv": 10,
    "encoding": 1
}
```

---

## VideoEffectBlock — Visual Effects

Used in `VideoEffectTrack`. Each block applies a visual effect (mask, filter, etc.) to the timeline region it covers. Connected to target clips via the `connect` graph (see [connect section](#connect--effect-connection-graph)).

```json
{
    "title": "Mask",
    "type": "VideoEffectBlock",
    "background": 4232007423,
    "foreground": 1216461823,
    "status": 0,
    "uuid": "{F4F8F801-70CF-4DA3-8743-F05EF6164318}",
    "tstart": 0.0,
    "tduration": 8333.0,
    "restype": "VideoEffectResource",
    "resid": "basic_mask",
    "attribute": {
        "version": 0,
        "duration": 8.333,                  // Duration in seconds (= tduration/1000)
        "Radius": {                          // Effect-specific parameter block
            "version": 0,
            "value": 0.62,
            "value2": 0.0,
            "r": 0, "g": 0, "b": 0,
            "transi_type": 1,
            "pic_path": ""
        }
    }
}
```

The `attribute` structure varies by effect type. The parameter block name (e.g., `"Radius"`) is effect-specific. Its internal structure follows the same pattern as `"Transition type"` in TransitionBlock.

The effect is linked to target clips via `VIDEO_EFFECT_CONNECT` entries in the `connect` object, where the effect block's UUID appears as one of the `relate` pair members.

See [vpd-vlogger-reference.md](vpd-vlogger-reference.md) for the full catalog of 124 available effects.

---

## VideoAttribute — Video Effects Pipeline

### Top-Level Fields

```json
"VideoAttribute": {
    "version": 0,
    "streamIndex": 0,          // Video stream index in the source file
    "trackDuration": 286.656,  // Total track duration (s)
    "deinterlace": false,      // Deinterlace filter enabled
    "baseInfoInited": true,    // Base info initialized flag
    "LensCorrection": { ... },
    "VideoCropper": { ... },
    // ... 11 sub-modules follow
}
```

### Sub-Module baseData

Each of the 11 sub-modules has a `version` field and a `baseData` with activation flags:

```json
"LensCorrection": {
    "version": 0,
    "baseData": {
        "version": 0,
        "valid": false,                    // true = effect active
        "fileTotalDuration": 68.5058,      // Total file duration (s)
        "fileCuttedStart": 0.8,            // Trim start (s)
        "fileCuttedDuration": 1.333,       // Trimmed duration (s)
        "blockDuration": 1.333             // Block duration on the timeline (s)
    },
    // ... module-specific fields
}
```

**Note:** Every sub-module and every `rectData` object contains a `version: 0` field (omitted from examples below for brevity).

### 1. LensCorrection — Lens Correction

```json
"LensCorrection": {
    "baseData": { "valid": false, ... },
    "valid": false,                    // Standalone activation flag (separate from baseData.valid)
    "focalPosX": 0.5, "focalPosY": 0.5,
    "hDeg": 118.2, "vDeg": 69.5, "dDeg": 133.6,
    "k2": 0.022,
    "cameraID": "custom", "fovID": "custom"
}
```

### 2. VideoCropper — Crop and Pan

```json
"VideoCropper": {
    "rectData": {
        "srcWidth": 1080, "srcHeight": 1920,
        "targetWidth": 1080, "targetHeight": 1920
    },
    "isPic": false,                // true for ImageFileBlock
    "staticNode": {
        "time": 0.0, "duration": 0.0,
        "posX": 0.5, "posY": 0.5,
        "sizeX": 1.0, "sizeY": 1.0,
        "ratioMode": 10, "angle": 0.0,
        "smoothness": true, "smoothType": 0, "pod": 0.0
    },
    "dynamicNodes": []    // Animation keyframes (same structure as staticNode)
}
```

See [vpd-vlogger-reference.md](vpd-vlogger-reference.md) for motion preset definitions that populate `dynamicNodes`.

### 3. BaseTransform — Rotation and Flip

```json
"BaseTransform": {
    "angle": 0,           // Rotation in degrees
    "vFlip": true          // Vertical flip (per-clip, no hFlip exists)
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

### 5. VideoLUT — Color Lookup Table (LUT)

```json
"VideoLUT": {
    "LutName": "",         // .cube/.3dl file name
    "strength": 1.0        // Intensity (0.0-1.0)
}
```

90+ LUT presets are available. See [vpd-vlogger-reference.md](vpd-vlogger-reference.md) for the full LUT catalog.

### 6. ColorEditor — Color Correction

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

### 7. Sharpen — Sharpness

```json
"Sharpen": {
    "amount": 500,     // 0-1000
    "radius": 2,
    "threshold": 0
}
```

### 8. Denoise — Noise Reduction

```json
"Denoise": {
    "enableDenoise": false,
    "deviation": 5.0, "coefficient": 2.0,
    "edgeThreshold": 0.3,
    "enableAutoLevel": false, "autoLevelK1": 0.5
}
```

### 9. VignetteEditor — Vignette

```json
"VignetteEditor": {
    "VIGNETTE_AMOUNT": 0,       // Intensity
    "VIGNETTE_SIZE": 100,        // Size
    "VIGNETTE_ROUNDNESS": 0,     // Roundness
    "VIGNETTE_FEATHER": 50,      // Edge softness
    "VIGNETTE_INNER_LIGHT": 0    // Inner light
}
```

### 10. VideoTransformer — Position, Scale, Fade

```json
"VideoTransformer": {
    "rectData": {
        "srcWidth": 1080, "srcHeight": 1920,
        "targetWidth": 1080, "targetHeight": 1920,
        "centerPosX": 0.5, "centerPosY": 0.5,     // Position (overlay only)
        "sizeX": 1.0, "sizeY": 1.0,               // Scale (overlay only)
        "angle": 0.0                                // Rotation (overlay only)
    },
    "overlay": false,              // true for OverlayTrack clips
    "fadeInDuration": 0.2,         // Fade-in duration (s)
    "fadeOutDuration": 0.0,        // Fade-out duration (s)
    "fadeInDirect": 255,           // Fade-in direction (255=normal)
    "fadeOutDirect": 255,          // Fade-out direction
    "baseInfoInited": true
}
```

**Note:** In `MainVideoTrack` `MediaFileBlock` clips, `rectData` only contains `srcWidth/Height` and `targetWidth/Height`. The fields `centerPosX/Y`, `sizeX/Y`, and `angle` appear in `OverlayTrack` clips and in `ImageFileBlock` on any track (images need explicit positioning since their resolution may differ from the project).

### 11. Compositing — Blending and Opacity

```json
"Compositing": {
    "mode": 0,                // Blending mode (see table)
    "opacity": 1.0,           // 0.0-1.0
    "fadeInDuration": 0.2,
    "fadeOutDuration": 0.0,
    "fadeInEnabeld": false,    // Note: original typo ("Enabeld")
    "fadeOutEnabled": false
}
```

**Blend modes:** `mode: 0` = normal. Additional blend modes exist (known names from the program: color_burn, color_dodge, hard_light, hard_mix, linear_burn, linear_dodge, linear_light, pin_light, soft_light, vivid_light) but the integer-to-name mapping beyond 0=normal is not yet confirmed.

---

## AudioAttribute — Audio Attributes

```json
"AudioAttribute": {
    "version": 0,
    "mute": false,
    "fadeInDuration": 0.0,     // Fade-in duration (s)
    "fadeOutDuration": 0.0,    // Fade-out duration (s)
    "multiple": 1.0,           // Volume multiplier
    "pitch": 1.0,              // Pitch adjustment
    "pitchType": 1             // Pitch algorithm type
}
```

---

## SpeedAttribute — Speed and Curves

```json
"SpeedAttribute": {
    "version": 0,
    "reversePlay": false,          // Reverse playback
    "Speed": {
        "version": 0,
        "baseData": {
            "version": 0,
            "fileTotalDuration": 68.5058,       // Total source file duration (s)
            "fileCuttedStart": 0.8,             // Trim start in source (s)
            "fileCuttedDuration": 1.333,        // Original trimmed duration (s)
            "handledTotalDuration": 68.5058,    // Total duration after speed
            "handledCuttedStart": 0.8,          // Trimmed start after speed (s)
            "handledCuttedDuration": 1.333      // Trimmed duration after speed (s)
        },
        "curve": "TmM0AQQ...",   // Speed curve (base64)
        "extraSpeed": 1.0,        // Global speed multiplier
        "audioSpeedRate": false    // Whether pitch is preserved during speed change
    }
}
```

**Note:** `Speed.baseData` does not have a `valid` field (unlike VideoAttribute `baseData` objects). For `ImageFileBlock`, `Speed` has no `baseData` wrapper — fields are directly in the `Speed` object, and there is no `curve`.

### Speed Curve Format

The `curve` field contains binary data encoded in Base64:
- **Magic bytes:** `4e633401` (ASCII: "Nc4" + version byte)
- **Content:** Keyframes defining variable speed along the clip
- **Typical size:** 500-700 bytes per curve

For constant speed, the ratio `fileCuttedDuration / handledCuttedDuration` gives the speed factor directly, without needing to interpret the curve.

---

## connect — Effect Connection Graph

The `connect` object at the `timeline` root maps directed connections between effect blocks. Usually empty (`{}`), but when populated:

```json
"connect": {
    "VIDEO_EFFECT_CONNECT": [
        {
            "type": "VIDEO_EFFECT_CONNECT",
            "relate": [
                "{2848EF0F-C0D2-404F-891E-4A18454E80E5}",   // Source UUID
                "{0BA409F2-EBFA-4370-AC32-CFD3CFCE79F8}"    // Destination UUID
            ],
            "disable": false,       // Connection disabled
            "check": false          // Connection selected/active
        }
    ]
}
```

Forms a directed acyclic graph (DAG) of effect nodes, where each `relate` contains exactly 2 UUIDs (`[source, destination]`). A central "hub" UUID with many inbound/outbound connections acts as the compositor/mixer node.

---

## Block Grouping

**No native grouping mechanism exists in the VPD format.** The `connect` object (`VIDEO_EFFECT_CONNECT`) is exclusively for the video effect graph DAG — it does not support arbitrary block grouping.

Blocks on different tracks are fully independent. There is no way to link a video clip to its associated audio clip, or group multiple subtitle blocks together. Temporal alignment between tracks is entirely manual.

The only cross-reference between blocks and resources is `resid` → resource pool `uuid`, which is a one-to-many relationship (multiple blocks can reference the same source file). To "group" blocks programmatically, you must track their UUIDs and timing positions externally.

---

## `status` Field — Flag Bitmask

The `status` field appears on tracks, blocks, and resources. It is a bitmask:

| Value | Hex | Context | Meaning |
|-------|-----|---------|---------|
| `0` | `0x0` | Any | Normal/active |
| `1` | `0x1` | Tracks, blocks | Disabled/hidden |
| `512` | `0x200` | Blocks | Locked |
| `513` | `0x201` | Blocks | Locked + disabled (`512 \| 1`) |
| `34359738880` | `0x800000200` | audiolist resources | Exported/generated audio flag |

---

## Resource Lists — Resource Pools

Four resource lists at the JSON root:

### videolist

```json
"videolist": {
    "title": "Video",
    "type": "ResourceLists",
    "status": 0,
    "subitems": [
        {
            "title": "video-name",
            "type": "MediaFileResource",
            "status": 0,
            "uuid": "9A24C29B00426678DF1A82D751895A31",
            "path": "C:/Users/.../video.mp4",       // Absolute path
            "duration": 68.5058                      // Duration in seconds
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
            "status": 34359738880,                   // Generated audio flag
            "uuid": "F6AC9619932279D49D8FC537E3100FA9",
            "path": "audio-export-0.wav",            // Can be relative to project
            "duration": 1.833
        }
    ]
}
```

**Note:** Imported audio resources (e.g., MP3 music) use `status: 1` (disabled) or `status: 0`.

### imagelist

The `imagelist` has two sub-structures: `subitems` for organization (links and folders) and `scapegoat` for the actual resources.

```json
"imagelist": {
    "title": "Picture",
    "type": "ResourceLists",
    "status": 0,
    "subitems": [
        { "type": "link", "resid": "HASH...", "uuid": "{...}" },
        {
            "title": "New list",
            "type": "ResourceList",
            "status": 0,
            "subitems": [
                { "type": "link", "resid": "HASH...", "uuid": "{...}" }
            ],
            "orientation": 2           // 2=horizontal(?), 3=vertical(?)
        }
    ],
    "scapegoat": [
        {
            "title": "image",
            "type": "MediaFileResource",
            "status": 0,
            "uuid": "E0D10E54A73EFF53196334C06C317BD7",
            "path": "C:/Users/.../image.png",
            "duration": 0.0             // PNG=0.0, JPG=0.04
        }
    ]
}
```

When empty, `imagelist` may have `"scapegoat": []` without `subitems`, or vice versa.

### subtitlelist

```json
"subtitlelist": {
    "title": "Subtitle",
    "type": "ResourceLists",
    "status": 0
    // No "subitems" when empty
}
```

### Resource References

Timeline clips reference resources via `resid` -> `uuid`:
- `MediaFileBlock.resid` = `ResourceItem.uuid` (MD5 hex hash without braces)
- `ImageFileBlock.resid` = `ResourceItem.uuid` (with braces `{...}`)
- UUIDs in timeline blocks **have** braces `{}`
- UUIDs in resource pools **do not** have braces `{}`

---

## Project Auxiliary Files

Each `.vpd` project folder contains:

| File | Description |
|------|-------------|
| `project.vpd` | Main project file (JSON) |
| `project.png` | Project thumbnail |
| `project.userdata` | Editor state (zoom, position, paths) |
| `EncoderOption.json` | Selected video/audio codec |
| `EncoderProfile.json` | Encoding preset (bitrate, sample rate) |
| `ico.ico` | Folder icon |
| `desktop.ini` | Windows icon configuration |
| `*.wav` | Exported/imported audio files |

### userdata

```json
{
    "environment": {
        "audoSnap": 1,
        "blockMovable": 1,
        "timelinePercent": 40.0,
        "timelinePlayPos": 124166.0,
        "mediaIconSize": 1,
        "mediaSortType": 0,
        "timelineVisibleStart": 0.0,
        "timelineVisibleDuration": 14630.97,
        "Adsorbed": true,                      // Snap to grid/edges
        "AllTrackLocked": false,
        "expFormat": "MP4",
        "expHigQua": false,                    // High quality export toggle
        "expQuality": -1,                      // -1=default
        "expVCodec": "",                       // Video codec override (""=use EncoderOption)
        "expFPSNum": 30, "expFPSDen": 1,
        "expBitTyps": -1,                      // Bitrate type (-1=default)
        "expACodec": "",                       // Audio codec override (""=use EncoderOption)
        "expAChannel": "",                     // Audio channel override (""=default)
        "expSample": -1,                       // Sample rate (-1=default)
        "expABitrate": -1,                     // Audio bitrate (-1=default)
        "playerRuler": false,                  // Show ruler in player
        "General Movie path": "C:/Users/.../Videos",
        "General Music path": "C:/Users/.../Music",
        "General Image path": "C:/Users/.../Images",
        "General Subtitle path": "C:/Users/.../Videos",
        "SortInfo": [                          // Media panel sort state per tab
            { "PageIndex": 0, "Sorttype": 2, "Sortorder": false }
        ]
    }
}
```

**`expFormat` observed values:** `"MP4"` (most common), `"M4A"` (audio-only export), `""` (default/unset).

**`expFPSNum` observed values:** `15`, `24`, `25`, `30` (most common).

**`-1` and `""` values** indicate "use default from EncoderOption/EncoderProfile" — the userdata only stores overrides.

### EncoderOption.json

Defines which codecs are selected for export:

```json
{
    "video_options": {
        "h264_nvenc": { "recently": {} },
        "chosen": "recently"
    },
    "audio_options": {
        "aac": { "recently": {} },
        "chosen": ""
    },
    "version": 1
}
```

**Video codec keys observed:** `h264_nvenc` (H.264 NVIDIA, most common), `hevc_nvenc` (H.265/HEVC NVIDIA). The program also supports `h264_amf` (AMD), `h264_qsv` (Intel), `hevc_amf`, `hevc_qsv` via its bundled FFmpeg.

**Audio codec keys observed:** `aac` (universal in all analyzed projects).

**`chosen` field:** `"recently"` = use the settings from the `recently` sub-object. `""` = default/auto.

Example with H.265/HEVC:

```json
{
    "video_options": {
        "hevc_nvenc": { "recently": {} },
        "chosen": "recently"
    },
    "audio_options": {
        "aac": { "recently": {} },
        "chosen": ""
    },
    "version": 1
}
```

### EncoderProfile.json

Defines encoding parameters per format. Can contain multiple profiles (`mp4`, `m4a`, `mp3`):

```json
{
    "profiles": {
        "mp4": {
            "recently": {
                "video": {
                    "videoEnabled": true,
                    "vCodec": 1,
                    "framerateNum": 30,
                    "framerateDen": 1,
                    "bestQuality": false,
                    "quality": 3,
                    "brMode": 0,
                    "bitrate": 3600000,
                    "crf": ""
                },
                "audio": {
                    "audioEnabled": true,
                    "aCodec": 2,
                    "audioCodec": "",
                    "audioSampleRate": 44100,
                    "audioBitrate": 128000,
                    "audioChannel": 2,
                    "audioChannelLayout": 3,
                    "audioBtMode": 1,
                    "audioCompressionLevel": 0,
                    "audioQuality": 0
                }
            }
        },
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

**Video fields:**

| Field | Description |
|-------|-------------|
| `vCodec` | Video codec: `0`=H.264/AVC, `1`=H.265/HEVC |
| `framerateNum`/`framerateDen` | Frame rate as fraction (30/1 = 30fps) |
| `bitrate` | Video bitrate in bps (observed range: 875,000 – 5,250,000) |
| `quality` | Quality level: `2` (low), `3` (medium), `4` (high), `5` (highest) |
| `bestQuality` | Enable best quality encoding (slower) |
| `brMode` | Bitrate mode: `0` = CBR (only observed value) |
| `crf` | CRF value (empty string = not used) |

**Audio fields:**

| Field | Description |
|-------|-------------|
| `aCodec` | Audio codec: `1`=MP3, `2`=AAC |
| `audioCodec` | Audio codec override (empty = use aCodec) |
| `audioSampleRate` | Sample rate in Hz (44100 universal) |
| `audioBitrate` | Bitrate in bps: 64,000 / 128,000 (common) / 256,000 |
| `audioChannel` | Number of channels (2 = stereo) |
| `audioChannelLayout` | Channel layout (3 = stereo) |
| `audioBtMode` | Bitrate mode (1 = default) |
| `audioCompressionLevel` | Compression level (0 = default) |
| `audioQuality` | Audio quality (0 = default) |

**Note:** Older projects may use `videoBitrate` instead of `bitrate`, and may omit `framerateNum`/`framerateDen`, `crf`, `audioCodec`, `audioCompressionLevel`, `audioQuality`. The format evolved across program versions.

See [vpd-vlogger-reference.md](vpd-vlogger-reference.md) for the full list of supported codecs and formats.
