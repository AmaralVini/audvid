# ai-video — Video & Image Generation with Gemini API

## About

Tools for generating videos and images using the Google Gemini API (Veo + Imagen). Credentials in `.env`.

**Default for video generation:** `veo-3.1-fast-generate-preview`, 720p, `durationSeconds: "4"` ($0.15/sec = **$0.60 per video**). Use other models/settings only when explicitly requested.

## Credentials

```bash
source .env  # loads GEMINI_API_KEY
```

- **Project**: 232914662253
- **Key name**: Gemini API Key - claude code

---

## Available Models

### Video (Veo)

| Model ID | Audio | Resolution | Price/sec |
|---|---|---|---|
| `veo-3.1-generate-preview` | Yes | 720p/1080p/4K | $0.40 (720p/1080p), $0.60 (4K) |
| `veo-3.1-fast-generate-preview` | Yes | 720p/1080p/4K | $0.15 (720p/1080p), $0.35 (4K) |
| `veo-3.0-generate-001` | Yes | 720p/1080p/4K | $0.40 |
| `veo-3.0-fast-generate-001` | Yes | 720p/1080p/4K | $0.15 |
| `veo-2.0-generate-001` | No | 720p only | $0.35 |

### Image (Imagen 4)

| Model ID | Price/image |
|---|---|
| `imagen-4.0-generate-001` (Standard) | $0.04 |
| `imagen-4.0-ultra-generate-001` (Ultra) | $0.06 |
| `imagen-4.0-fast-generate-001` (Fast) | $0.02 |

### Image (Gemini Native)

| Model ID | Notes |
|---|---|
| `gemini-2.5-flash-image` | Fast, image editing, multi-turn |
| `gemini-3-pro-image-preview` | 4K, advanced reasoning, editing |

**No free tier** for any video/image model.

---

## Video API (Veo)

### Endpoint

```
POST https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:predictLongRunning
```

### Headers

```
x-goog-api-key: $GEMINI_API_KEY
Content-Type: application/json
```

### Complete Parameters

**Inside `instances[0]`:**

| Parameter | Type | Description |
|---|---|---|
| `prompt` | string | **Required.** Video description |
| `negativePrompt` | string | Elements to exclude |
| `image` | object | First frame (image-to-video). `{"inlineData": {"mimeType": "image/png", "data": "BASE64"}}` |
| `lastFrame` | object | Last frame (interpolation, Veo 3.1 only). Same format as image |
| `video` | object | Previous video for extension (Veo 3.1 only). `{"inlineData": {"mimeType": "video/mp4", "data": "BASE64"}}` |

**Inside `parameters`:**

| Parameter | Type | Default | Values | Notes |
|---|---|---|---|---|
| `aspectRatio` | string | `"16:9"` | `"16:9"`, `"9:16"` | Only 2 options |
| `resolution` | string | `"720p"` | `"720p"`, `"1080p"`, `"4k"` | Veo 3+ only (Veo 2 does not support) |
| `durationSeconds` | integer | varies | see table below | **Must be a number, not string.** `8` required for extension, ref images, 1080p, 4K. 720p accepts `4`, `6`, `8` |
| `personGeneration` | string | varies | `"allow_all"`, `"allow_adult"`, `"dont_allow"` | See details below |
| `numberOfVideos` | integer | 1 | — | Number of videos per request |
| `seed` | integer | — | any int | Veo 3 and 2 only, not fully deterministic |
| `referenceImages` | array | — | up to 3 objects | Veo 3.1 only, requires `durationSeconds: 8` |

### Valid Durations by Model and Resolution

**Note:** `durationSeconds` must be an integer (number), not a string.

| Model | 720p | 1080p | 4K |
|---|---|---|---|
| Veo 3.1 / 3.1 Fast | `4`, `6`, `8` | `8` only | `8` only |
| Veo 3 / 3 Fast | `4`, `6`, `8` | `8` only | `8` only |
| Veo 2 | `5`, `6`, `8` | — | — |

### personGeneration by Model

| Model | Text-to-video | Image-to-video |
|---|---|---|
| Veo 3.1 | `"allow_all"` only | `"allow_adult"` only |
| Veo 3 | `"allow_all"` only | `"allow_adult"` only |
| Veo 2 | `"allow_all"`, `"allow_adult"`, `"dont_allow"` | `"allow_adult"`, `"dont_allow"` |

### Async Flow (predictLongRunning)

**1. Submit request** — returns operation name:
```json
{"name": "models/{MODEL}/operations/{OP_ID}"}
```

**2. Poll every ~10s:**
```
GET https://generativelanguage.googleapis.com/v1beta/{operation_name}
Header: x-goog-api-key: $GEMINI_API_KEY
```

**3. When `done: true`**, extract video URI:
```json
{
  "done": true,
  "response": {
    "generateVideoResponse": {
      "generatedSamples": [{
        "video": {"uri": "https://..."}
      }]
    }
  }
}
```

**4. Download** (auth header required):
```bash
curl -L -o output.mp4 -H "x-goog-api-key: $GEMINI_API_KEY" "${video_uri}"
```

**Latency:** 11 seconds to 6 minutes (peak hours).

### Native Audio (Veo 3 and 3.1)

Veo 3+ generates synchronized audio automatically. Prompt techniques:
- **Dialogue:** use quotes: `"This must be it," he murmurs`
- **Sound effects:** describe explicitly: `tires screeching loudly`
- **Ambient noise:** describe environment: `eerie hum in background`
- **Music:** describe style: `upbeat electronic music with a rhythmical beat`

---

## Advanced Features (Veo 3.1 Only)

### Reference Images (up to 3)

Preserves subject appearance throughout the video. Requires `durationSeconds: "8"`.

```json
{
  "parameters": {
    "referenceImages": [
      {
        "image": {"inlineData": {"mimeType": "image/png", "data": "BASE64"}},
        "referenceType": "asset"
      }
    ]
  }
}
```

### Frame Interpolation

Generates smooth transition between first and last frame. Requires `durationSeconds: "8"`.
- `image` in `instances[0]` — first frame
- `lastFrame` in `parameters` — last frame

### Video Extension (Veo 3.1 only)

Extends a previous Veo video by ~7 seconds.
- Input: 720p, max 141 seconds
- Max output: 148 seconds total
- Requires `resolution: "720p"`
- Max 20 extensions per original video
- `video` in `instances[0]` with base64 video

---

## Image API (Imagen 4)

### Endpoint (synchronous)

```
POST https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:predict
```

### Parameters

| Parameter | Type | Default | Values |
|---|---|---|---|
| `prompt` | string | required | Free text, max 480 tokens, **English only** |
| `sampleCount` | integer | 4 | 1-4 |
| `aspectRatio` | string | `"1:1"` | `"1:1"`, `"3:4"`, `"4:3"`, `"9:16"`, `"16:9"` |
| `imageSize` | string | `"1K"` | `"1K"`, `"2K"` (Standard/Ultra only, Fast does not support) |
| `personGeneration` | string | `"allow_adult"` | `"dont_allow"`, `"allow_adult"`, `"allow_all"` |

### Request/Response

```json
// Request
{
  "instances": [{"prompt": "Robot holding a red skateboard"}],
  "parameters": {"sampleCount": 2, "aspectRatio": "16:9"}
}

// Response (synchronous, no polling)
{
  "predictions": [
    {"bytesBase64Encoded": "BASE64_IMAGE_DATA", "mimeType": "image/png"}
  ]
}
```

### Imagen Limitations

- Prompts in **English only**
- Text in images: max ~25 characters for best results
- No image editing (use Gemini Native for that)
- SynthID watermark on all images

---

## Image API (Gemini Native)

Alternative to Imagen with editing and multi-turn support.

### Endpoint

```
POST https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent
```

### Request

```json
{
  "contents": [{
    "parts": [
      {"text": "Generate an image of a sunset over mountains"},
      {"inline_data": {"mime_type": "image/png", "data": "BASE64_FOR_EDITING"}}
    ]
  }],
  "generationConfig": {
    "responseModalities": ["TEXT", "IMAGE"],
    "imageConfig": {
      "aspectRatio": "16:9",
      "imageSize": "2K"
    }
  }
}
```

### Advantages over Imagen

- Image editing (add/remove/modify elements)
- Multi-turn (iterative refinement)
- Up to 14 reference images (6 objects + 5 humans)
- Gemini 3 Pro supports **4K**
- More aspect ratios: `"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"4:5"`, `"5:4"`, `"9:16"`, `"16:9"`, `"21:9"`
- `imageSize`: `"1K"`, `"2K"`, `"4K"` (uppercase K required)

---

## File Upload API (free)

For uploading large images/videos for use in Veo image-to-video.

### Upload (2 steps)

**1. Start upload:**
```bash
curl -X POST "https://generativelanguage.googleapis.com/upload/v1beta/files" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Command: start" \
  -H "X-Goog-Upload-Header-Content-Length: BYTES" \
  -H "X-Goog-Upload-Header-Content-Type: image/png" \
  -H "Content-Type: application/json" \
  -d '{"file": {"display_name": "my_image"}}'
```

**2. Upload bytes** (use URI returned in step 1):
```bash
curl -X PUT "${UPLOAD_URI}" \
  -H "X-Goog-Upload-Command: upload, finalize" \
  -H "X-Goog-Upload-Offset: 0" \
  --data-binary @file.png
```

### Operations

- **List:** `GET /v1beta/files`
- **Metadata:** `GET /v1beta/files/{file_name}`
- **Delete:** `DELETE /v1beta/files/{file_name}`

### Limits

- Max per file: 2 GB
- Total storage: 20 GB per project
- Retention: **48 hours** (auto-delete)

### Referencing files in API calls

```json
{"file_data": {"mime_type": "image/png", "file_uri": "files/abc123"}}
```

---

## General Notes

- All videos include **SynthID watermark** (invisible)
- Videos are stored on Google servers for **2 days**, then deleted
- Only charged for successfully generated videos (safety filter block = no charge)
- Generation latency: 11s to 6min depending on load

## veo-generate.py — Video Generation CLI

Script that handles the full Veo workflow: submit, poll, and download.

### Usage

```bash
# Basic (720p, 4s, 16:9)
python3 ai-video/veo-generate.py "prompt here" -o output.mp4

# Custom resolution and duration
python3 ai-video/veo-generate.py "prompt" -o video.mp4 --resolution 1080p --duration 8 --aspect-ratio 9:16

# Specific model
python3 ai-video/veo-generate.py "prompt" -o video.mp4 -m veo-3.1-generate-preview

# Image-to-video (first frame)
python3 ai-video/veo-generate.py "prompt" -o video.mp4 --image frame.png

# Frame interpolation (first + last frame, Veo 3.1 only)
python3 ai-video/veo-generate.py "prompt" -o video.mp4 --image first.png --last-frame last.png --duration 8

# Video extension (Veo 3.1 only)
python3 ai-video/veo-generate.py "prompt" -o video.mp4 --video original.mp4 --duration 8

# Reference images for subject consistency (up to 3, Veo 3.1 only)
python3 ai-video/veo-generate.py "prompt" -o video.mp4 --ref-images ref1.png ref2.png --duration 8

# Multiple videos + seed
python3 ai-video/veo-generate.py "prompt" -o video.mp4 --num-videos 2 --seed 42

# Negative prompt
python3 ai-video/veo-generate.py "prompt" -o video.mp4 --negative-prompt "blurry, low quality"
```

### All Parameters

| Flag | Default | Description |
|---|---|---|
| `prompt` (positional) | — | Video description (required) |
| `-o`, `--output` | `output.mp4` | Output file path |
| `-m`, `--model` | `veo-3.1-fast-generate-preview` | Model ID |
| `--negative-prompt` | — | Elements to exclude |
| `--aspect-ratio` | `16:9` | `16:9` or `9:16` |
| `--resolution` | `720p` | `720p`, `1080p`, `4k` |
| `--duration` | `4` | Duration in seconds |
| `--person-generation` | `allow_all` | `allow_all`, `allow_adult`, `dont_allow` |
| `--num-videos` | `1` | Number of videos per request |
| `--seed` | — | Seed for reproducibility (Veo 2/3 only) |
| `--image` | — | First frame image path (image-to-video) |
| `--last-frame` | — | Last frame image path (interpolation) |
| `--video` | — | Previous video for extension |
| `--ref-images` | — | Reference image paths (up to 3) |
| `--poll-interval` | `10` | Polling interval in seconds |

API key is loaded from `GEMINI_API_KEY` env var or from `.env` file in the script directory.

---

## File Structure

```
ai-video/
  .env              # GEMINI_API_KEY (not committed)
  .gitignore        # ignores .env and *.mp4
  veo-generate.py   # Video generation CLI (submit + poll + download)
  CLAUDE.md         # This file
```
