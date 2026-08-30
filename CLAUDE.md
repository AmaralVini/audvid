## Language

- **Conversation:** Always respond in Portuguese (pt-BR)
- **Code:** English (variable names, function names, comments, docstrings)
- **Prompts for AI APIs:** English (Gemini, Veo, etc.)

# audvid — Audio & Video Tools

## About

Collection of tools for audio and video processing, focused on editing workflow automation. Runs on **Windows 11** with ffmpeg.

**Conventions:**
- Each feature lives in its own folder with a detailed `CLAUDE.md`
- Shared infrastructure (Playwright) lives in `playwright/`
- General documentation lives in `docs/`

---

## Features

### vpd-enhance-audio/

Generates clean audio (no click artifacts at cuts) from VideoProc Vlogger projects (.vpd), with automatic enhance via Adobe Podcast.

Full documentation: [vpd-enhance-audio/CLAUDE.md](vpd-enhance-audio/CLAUDE.md)

### vpd-add-subtitles/

Adds word-by-word subtitles to VPD from enhanced audio, with OpusClip style: current word highlighted with different color + size. Transcribes with Whisper (GPU), loads style from VideoProc Vlogger, each word is an editable block on the timeline.

Full documentation: [vpd-add-subtitles/CLAUDE.md](vpd-add-subtitles/CLAUDE.md)

### vpd-pipeline.py

Parent script that chains `vpd-enhance-audio` + `vpd-add-subtitles` in a single command. Runs with the `torch-gpu` venv interpreter directly (uv-managed venv, no "activate" step):

```bash
~/CODE/torch-gpu/.venv/Scripts/python.exe vpd-pipeline.py project.vpd                    # enhance + subtitles
~/CODE/torch-gpu/.venv/Scripts/python.exe vpd-pipeline.py project.vpd --skip-enhance      # subtitles only
~/CODE/torch-gpu/.venv/Scripts/python.exe vpd-pipeline.py project.vpd --skip-subtitles    # enhance only
```

> **Pending:** transcription is migrating from a directly-loaded `openai-whisper` to the `/transcrever` skill (faster-whisper via the `torch-gpu` venv). `vpd-pipeline.py` and `vpd-add-subtitles` still need to be adapted to call the skill instead of loading whisper on their own.

### ai-video/

Video and image generation using Google Gemini API (Veo + Imagen). Supports text-to-video, image-to-video, frame interpolation, video extension, and image generation.

Full documentation: [ai-video/CLAUDE.md](ai-video/CLAUDE.md)

---

## Shared Infrastructure

### playwright/

Node.js/Playwright dependencies shared by features that use web automation. Contains `package.json`, `package-lock.json` and `node_modules/`.

Setup: `cd playwright && npm install && npx playwright install chromium`

Documentation: [docs/playwright-setup.md](docs/playwright-setup.md)

---

## Running Python

**IMPORTANT:** `python3` on Windows triggers the Microsoft Store alias and fails. Always use the full venv path (`torch-gpu`, uv-managed — there is no "activate" step, call the interpreter directly):

```bash
~/CODE/torch-gpu/.venv/Scripts/python.exe script.py
```

## GPU Environment (Transcription)

- **venv**: `torch-gpu` (`~/CODE/torch-gpu/.venv`), managed by uv — call `~/CODE/torch-gpu/.venv/Scripts/python.exe` directly, no "activate" step
- **Python**: 3.12
- **GPU**: NVIDIA RTX 3060 Ti 8GB
- **Transcription**: via the `/transcrever` skill (faster-whisper / CTranslate2, GPU), replacing the old direct `openai-whisper` load — see the pending item under `vpd-pipeline.py` above
- **ffmpeg**: from PATH (winget `Gyan.FFmpeg` 9.0.1)

## Dependencies

- **Python 3.12** (via the `torch-gpu` venv, managed by uv)
- **ffmpeg** (from PATH, winget `Gyan.FFmpeg` 9.0.1)
- **Node.js v24.11.0** (`C:\Program Files\nodejs\node.exe`)
- **Playwright** (`cd playwright && npm install`)
- No additional Python packages required (stdlib only)

## Git/GitHub

- GitHub SSH is **NOT configured** on Windows (was configured on WSL2)
- Use HTTPS for git remotes

## Documentation

- `docs/vpd-format.md` — .vpd file format: complete JSON structure (reverse engineering)
- `docs/vpd-vlogger-reference.md` — VideoProc Vlogger program reference: presets, styles, effects, Lua API, codecs
- `docs/playwright-setup.md` — Playwright setup and authentication flow (storageState)
- `docs/linux-environment.md` — Previous WSL2/Linux environment configuration (archive)

## File Structure

```
audvid/
  vpd-enhance-audio/               # Feature: clean audio + enhance
    vpd-enhance-audio.py            # Main script
    adobe-enhance.js                # Adobe Enhance automation
    save-session.js                 # Save Adobe session
    debug-enhance.js                # Enhance debug
    CLAUDE.md                       # Full documentation
  vpd-add-subtitles/               # Feature: word-by-word subtitles
    vpd-add-subtitles.py            # Main script
    CLAUDE.md                       # Full documentation
  vpd-pipeline.py                  # Parent script: enhance + subtitles
  ai-video/                         # Feature: AI video/image generation
    .env                            # Gemini API key (not committed)
    veo-generate.py                 # Video generation CLI
    CLAUDE.md                       # Full documentation
    scripts/                        # One-off/batch generation scripts
  playwright/                       # Shared Playwright infra
    package.json                    # Node dependencies
    package-lock.json
  docs/                             # General documentation
    vpd-format.md                   # .vpd file format (reverse engineering)
    vpd-vlogger-reference.md        # VideoProc Vlogger program reference
    playwright-setup.md             # Playwright + Adobe setup
  CLAUDE.md                         # This file
  .env                              # Credentials (not committed)
  .gitignore
```
