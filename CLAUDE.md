# audvid — Audio & Video Tools

## About

Collection of tools for audio and video processing, focused on editing workflow automation. Runs on **WSL2 (Ubuntu 24.04)** with ffmpeg.

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

Parent script that chains `vpd-enhance-audio` + `vpd-add-subtitles` in a single command. Requires conda env `pt-gpu` activated.

```bash
conda activate pt-gpu
python3 vpd-pipeline.py project.vpd                    # enhance + subtitles
python3 vpd-pipeline.py project.vpd --skip-enhance      # subtitles only
python3 vpd-pipeline.py project.vpd --skip-subtitles    # enhance only
```

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

## Credentials

WSL sudo/admin credentials are in the `.env` file at project root. Use `echo $SUDO_PASS | sudo -S <command>` when elevated permissions are needed. To load: `source .env` or read directly from the file.

## GPU Environment (Whisper)

- **Miniforge**: `~/miniforge3`
- **Conda env**: `pt-gpu` (Python 3.12) — activate with `conda activate pt-gpu`
- **PyTorch**: 2.6.0+cu124
- **GPU**: NVIDIA RTX 3060 Ti 8GB, CUDA 12.6
- **openai-whisper**: installed in `pt-gpu` env
- **Models**: symlink `~/.cache/whisper` → `/mnt/c/Users/vinia/.cache/whisper` (base.pt, medium.pt, large-v3-turbo.pt)
- **ffmpeg**: native Linux (apt)

## Dependencies

- **Python 3** (included in Ubuntu 24.04)
- **ffmpeg** (native Linux via apt + Windows `.exe` accessible via PATH)
- **Node.js** (for web automation via Playwright)
- **Playwright** (`cd playwright && npm install`)
- No additional Python packages required (stdlib only)

## Documentation

- `docs/vpd-format.md` — .vpd file format: complete JSON structure (reverse engineering)
- `docs/vpd-vlogger-reference.md` — VideoProc Vlogger program reference: presets, styles, effects, Lua API, codecs
- `docs/playwright-setup.md` — Playwright setup and authentication flow (storageState)

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
