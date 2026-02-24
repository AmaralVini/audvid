# vpd-add-subtitles — Word-by-word subtitles for VPD projects

## About

Python script that adds OpusClip-style subtitles (word-by-word with highlight) to VideoProc Vlogger (.vpd) projects. Transcribes audio with Whisper, groups words into screens, and inserts TextEffectBlocks into SubtitleTrack with color + size highlight via ASS override tags.

**Visual style:** Loaded from a style saved in VideoProc Vlogger (`--style my-style-1`). Current word highlighted with different color and larger size (`\fs`). Each word is an independent block on the timeline, individually editable in the GUI. Blocks interleaved across 2 SubtitleTracks (A and B) for easier editing.

## How It Works

1. **Detect audio** — Looks for `{project}-enhanced.wav` or `{project}-clean.wav` in the project folder (or uses `--audio`)
2. **Transcribe with Whisper** — Runs `whisper` CLI with word_timestamps to get per-word timing. Saves JSON as `{audio}-whisper.json` in the project folder. If the JSON already exists, reuses it without running Whisper again
3. **Group words into screens** — Respects max_chars (28), max_lines (2), and gap_threshold (1.5s) for screen breaks. Calculates break point considering worst case (largest word on line highlighted at highlight_scale), inserting explicit `\N` to keep line breaks consistent across blocks
4. **Load style** — Reads the VideoProc Vlogger style from `AppData/Roaming/Digiarty/VideoProc Vlogger/sub_styles/{name}.json` and applies all properties (font, color, border, shadow, etc.)
5. **Generate TextEffectBlocks** — One block per word. Each block shows the full screen text with ASS override tags on the current word (color + size). 1 block = 1 editable item on the timeline
6. **Insert into VPD** — Removes existing SubtitleTracks, creates 2 tracks ("Subtitle A" and "Subtitle B") with interleaved blocks (even words in A, odd words in B) for easier GUI editing
7. **Backup** — Creates `project.vpd.bak` before modifying (if it doesn't exist)
8. **Reset playhead** — Positions the playhead at the beginning of the project (via `.userdata`)

## Technique: ASS Override Tags

VPD uses ASS conventions internally. The script uses `\c` (color) and `\fs` (font size) inline in the dialogue `text` field:

```
{\c&HFF559B&\fs120}WORD{\c&HFFFFFF&\fs100} rest of the text
```

- `\c&HFF559B&` — highlight color (ASS BGR format)
- `\fs120` — larger size for highlight
- `{\c&HFFFFFF&\fs100}` — explicit reset for base color/size

**Limitations discovered in Vlogger:**
- `{\r}` (ASS reset) causes strikethrough — use explicit reset instead
- `\t()` (ASS animation) applies globally, not per word — use static size
- Block `styles[]` must use Vlogger defaults (bold=false, fsize=20, outline=1, alignment=2) to avoid strikethrough — the dialogue overrides everything

## Usage

```bash
# Default flow (detects audio, uses style my-style-1)
python3 vpd-add-subtitles/vpd-add-subtitles.py project.vpd

# Specify style and highlight color
python3 vpd-add-subtitles/vpd-add-subtitles.py project.vpd --style my-style-1 --highlight-color "#00FF00"

# Use 1 track instead of 2
python3 vpd-add-subtitles/vpd-add-subtitles.py project.vpd --tracks 1

# Specify audio manually
python3 vpd-add-subtitles/vpd-add-subtitles.py project.vpd --audio my-audio.wav

# Force new transcription (delete the JSON cache)
rm project-folder/*-whisper.json
python3 vpd-add-subtitles/vpd-add-subtitles.py project.vpd

# ASS tags test (insert test block)
python3 vpd-add-subtitles/vpd-add-subtitles.py project.vpd --test-ass
```

## Options

### Audio

| Option | Description | Default |
|--------|-------------|---------|
| `--audio PATH` | Audio to transcribe | detects `*-enhanced.wav` |
| `--whisper-model MODEL` | tiny/base/small/medium/large | medium |
| `--language LANG` | Language code | pt |

### Layout

| Option | Description | Default |
|--------|-------------|---------|
| `--max-lines N` | Max lines per screen (1 or 2) | 2 |
| `--max-chars N` | Max characters per line | 28 |
| `--gap-threshold FLOAT` | Minimum pause (s) to break screen | 1.5 |
| `--tracks N` | Number of SubtitleTracks (1 or 2) | 2 |

### Style

| Option | Description | Default |
|--------|-------------|---------|
| `--style NAME` | VideoProc Vlogger style name | my-style-1 |
| `--highlight-color HEX` | Highlighted word color | #9B55FF (purple) |
| `--highlight-scale N` | Highlighted word scale % | 120 |
| `--position-y FLOAT` | Vertical position 0.0-1.0 | 0.70 |
| `--margin N` | Side margin in pixels | 100 |

The base style (font, color, border, shadow) is loaded from the VideoProc Vlogger JSON file at:
`/mnt/c/Users/vinia/AppData/Roaming/Digiarty/VideoProc Vlogger/sub_styles/{name}.json`

### Test

| Option | Description |
|--------|-------------|
| `--test-ass` | Insert test block with ASS tags and exit |

## Transcription Cache

Whisper saves the result as `{audio}-whisper.json` in the project folder. Subsequent runs reuse this file automatically, skipping Whisper. To force a new transcription, delete the JSON file.

## Dependencies

- **Python 3** (stdlib only)
- **whisper** CLI — available in the `pt-gpu` environment (active by default)

## Files

| File | Description |
|------|-------------|
| `vpd-add-subtitles.py` | Main script |
| `CLAUDE.md` | This documentation |

## Generated Files (not committed)

- `{audio}-whisper.json` — Whisper transcription cache (in the VPD project folder)
