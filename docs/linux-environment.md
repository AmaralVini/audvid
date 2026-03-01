# Linux (WSL2) Environment — Archive

Previous environment configuration when running on WSL2 (Ubuntu 24.04).

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

## Git/GitHub

- GitHub SSH configured and working
