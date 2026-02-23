#!/usr/bin/env python3
"""
vpd-add-subtitles — Adiciona legendas palavra-por-palavra ao VPD

Transcreve o audio com Whisper, agrupa palavras em telas (1-2 linhas),
e insere TextEffectBlocks no SubtitleTrack do VPD com highlight por palavra
estilo OpusClip (cor + zoom de entrada via ASS override tags).

Uso:
    python3 vpd-add-subtitles.py projeto.vpd
    python3 vpd-add-subtitles.py projeto.vpd --style my-style-1 --highlight-color "#00FF00"
    python3 vpd-add-subtitles.py projeto.vpd --audio meu-audio.wav --whisper-model large
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid


# ---------------------------------------------------------------------------
# Helpers: cores e formatacao
# ---------------------------------------------------------------------------

def hex_to_argb(hex_color, alpha=255):
    """#RRGGBB -> ARGB uint32 (alpha default FF)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (alpha << 24) | (r << 16) | (g << 8) | b


def hex_to_ass_color(hex_color):
    """#RRGGBB -> &HBBGGRR& (formato ASS BGR)."""
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return "&H{}{}{}&".format(b.upper(), g.upper(), r.upper())


# ---------------------------------------------------------------------------
# Leitura de estilo do VideoProc Vlogger
# ---------------------------------------------------------------------------

VLOGGER_STYLES_DIR = "/mnt/c/Users/vinia/AppData/Roaming/Digiarty/VideoProc Vlogger/sub_styles"


def load_vlogger_style(style_name):
    """Le um estilo de subtitle do VideoProc Vlogger e retorna style_config.

    Mapeia campos do JSON do Vlogger para o formato usado pelo script.
    """
    style_path = os.path.join(VLOGGER_STYLES_DIR, f"{style_name}.json")
    if not os.path.exists(style_path):
        print(f"ERRO: estilo nao encontrado: {style_path}", file=sys.stderr)
        styles = [f.replace(".json", "") for f in os.listdir(VLOGGER_STYLES_DIR) if f.endswith(".json")]
        if styles:
            print(f"  Estilos disponiveis: {', '.join(sorted(styles))}", file=sys.stderr)
        sys.exit(1)

    with open(style_path, "r", encoding="utf-8") as f:
        s = json.load(f)

    return {
        "font": s.get("ffontname", "Arial"),
        "font_size": int(s.get("fsize", 65)),
        "bold": bool(s.get("fblod", 0)),
        "italic": s.get("fitalic", False),
        "underline": s.get("ful", False),
        "space": s.get("tspace", 0.0),
        "blend_mode": s.get("comp_bm", 0),
        "blend_opacity": s.get("comp_op", 100),
        "color_mode": s.get("cm_type", 0),
        "f_color": s.get("cmf_v", 4294967295),
        "f_opacity": s.get("cmf_op", 100),
        "g_start": s.get("cmg_b", 4294967295),
        "g_stop": s.get("cmg_e", 4294967295),
        "g_opacity": s.get("cmg_op", 100),
        "g_angle": s.get("cmg_a", 0),
        "bd_enable": s.get("bd_st", True),
        "bd_color": s.get("bd_c", 4278190080),
        "bd_size": s.get("bd_s", 4),
        "bd_opacity": s.get("bd_op", 100),
        "bd_blur": s.get("bd_b", 0),
        "sd_enable": s.get("sd_st", False),
        "sd_type": s.get("sd_t", 0),
        "sd_color": s.get("sd_c", 4278190080),
        "sd_opacity": s.get("sd_op", 100),
        "sd_dist": s.get("sd_d", 5),
    }


# ---------------------------------------------------------------------------
# Whisper transcription
# ---------------------------------------------------------------------------

def find_whisper():
    """Encontra o binario whisper."""
    for name in ["whisper", "whisper.exe"]:
        if shutil.which(name):
            return name
    return None


def parse_whisper_json(json_path):
    """Parse do JSON do whisper e retorna lista de {word, start, end}."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    words = []
    for segment in data.get("segments", []):
        for w in segment.get("words", []):
            text = w.get("word", "").strip()
            if text:
                words.append({
                    "word": text,
                    "start": w["start"],
                    "end": w["end"],
                })
    return words


def transcribe(audio_path, model, language, vpd_dir):
    """Roda whisper CLI (se necessario) e retorna lista de {word, start, end}.

    O JSON e salvo na pasta do projeto como <audio>-whisper.json.
    Se ja existir, reutiliza sem rodar o whisper novamente.
    """
    basename = os.path.splitext(os.path.basename(audio_path))[0]
    json_path = os.path.join(vpd_dir, f"{basename}-whisper.json")

    # Reutilizar transcricao existente
    if os.path.exists(json_path):
        print(f"  Transcricao existente: {os.path.basename(json_path)}")
        words = parse_whisper_json(json_path)
        print(f"  Palavras: {len(words)}")
        return words

    # Rodar whisper
    whisper_bin = find_whisper()
    if not whisper_bin:
        print("ERRO: whisper nao encontrado no PATH.", file=sys.stderr)
        print("  Instale: pip install openai-whisper", file=sys.stderr)
        sys.exit(1)

    print(f"  Whisper model: {model}")
    print(f"  Language: {language}")
    print(f"  Audio: {os.path.basename(audio_path)}")

    temp_dir = tempfile.mkdtemp(prefix="vpd_sub_", dir=vpd_dir)
    try:
        cmd = [whisper_bin, audio_path, "--model", model, "--language", language, "--word_timestamps", "True", "--output_format", "json", "--output_dir", temp_dir]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERRO: whisper falhou (exit {result.returncode})", file=sys.stderr)
            if result.stderr:
                print(result.stderr[:2000], file=sys.stderr)
            sys.exit(1)

        # Whisper salva <basename>.json no temp_dir
        whisper_out = os.path.join(temp_dir, f"{basename}.json")
        if not os.path.exists(whisper_out):
            print(f"ERRO: arquivo JSON do whisper nao encontrado: {whisper_out}", file=sys.stderr)
            sys.exit(1)

        # Copiar para a pasta do projeto com nome permanente
        shutil.copy2(whisper_out, json_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    words = parse_whisper_json(json_path)
    print(f"  Palavras transcritas: {len(words)}")
    print(f"  Salvo: {os.path.basename(json_path)}")
    return words


# ---------------------------------------------------------------------------
# Agrupamento de palavras em telas
# ---------------------------------------------------------------------------

def _is_sentence_end(word_text):
    """Verifica se a palavra termina uma frase (., ?, !)."""
    return word_text.rstrip().endswith((".", "?", "!"))


def group_words_into_screens(words, max_lines, max_chars, gap_threshold):
    """Agrupa palavras em telas respeitando limites de caracteres, linhas e pausas.

    Quando uma palavra termina frase (., ?, !), a proxima frase inicia em nova linha.
    Se max_lines ja foi atingido, inicia nova tela.
    """
    if not words:
        return []

    screens = []
    current_lines = [[]]  # lista de listas de palavras
    current_line_len = 0
    prev_end = words[0]["start"]
    force_new_line = False  # flag: proxima palavra deve iniciar nova linha

    for w in words:
        word_len = len(w["word"])

        # Gap grande -> nova tela
        if current_lines[0] and w["start"] - prev_end > gap_threshold:
            screens.append(_build_screen(current_lines))
            current_lines = [[]]
            current_line_len = 0
            force_new_line = False

        # Fim de frase anterior -> forcar nova linha
        if force_new_line and current_line_len > 0:
            if len(current_lines) >= max_lines:
                screens.append(_build_screen(current_lines))
                current_lines = [[]]
                current_line_len = 0
            else:
                current_lines.append([])
                current_line_len = 0
            force_new_line = False

        # Palavra excede max_chars na linha atual -> nova linha
        needed = word_len if current_line_len == 0 else current_line_len + 1 + word_len
        if current_line_len > 0 and needed > max_chars:
            # Nova linha
            if len(current_lines) >= max_lines:
                # Max linhas atingido -> nova tela
                screens.append(_build_screen(current_lines))
                current_lines = [[]]
                current_line_len = 0
            else:
                current_lines.append([])
                current_line_len = 0

        current_lines[-1].append(w)
        current_line_len = current_line_len + 1 + word_len if current_line_len > 0 else word_len
        prev_end = w["end"]

        # Marcar fim de frase para proxima palavra
        if _is_sentence_end(w["word"]):
            force_new_line = True

    # Ultima tela
    if current_lines[0]:
        screens.append(_build_screen(current_lines))

    return screens


def _build_screen(lines):
    """Constroi um objeto screen a partir de linhas de palavras."""
    all_words = []
    for line in lines:
        all_words.extend(line)
    return {
        "lines": lines,
        "words": all_words,
        "start": all_words[0]["start"],
        "end": all_words[-1]["end"],
    }


# ---------------------------------------------------------------------------
# Geracao de texto com ASS override tags
# ---------------------------------------------------------------------------

def build_highlight_text(screen, highlight_idx, ass_color, base_color, font_size, highlight_font_size):
    """Monta texto completo da tela com ASS tags na palavra highlight_idx.

    Usa \\fs (font size) para destaque e reset explicito (\\r causa tachado no Vlogger).
    """
    reset_tag = "{\\c" + base_color + "\\fs" + str(font_size) + "}"

    line_texts = []
    word_global_idx = 0
    for line in screen["lines"]:
        parts = []
        for w in line:
            if word_global_idx == highlight_idx:
                tag = "{\\c" + ass_color + "\\fs" + str(highlight_font_size) + "}"
                parts.append(tag + w["word"] + reset_tag)
            else:
                parts.append(w["word"])
            word_global_idx += 1
        line_texts.append(" ".join(parts))

    return "\\N".join(line_texts)


# ---------------------------------------------------------------------------
# Geracao de TextEffectBlocks
# ---------------------------------------------------------------------------

def create_text_effect_blocks(screen, style_config, project_width, project_height):
    """Cria um TextEffectBlock por palavra da tela.

    Cada bloco e independente na timeline, permitindo ajuste de timing na GUI.
    Todos mostram o texto completo da tela, com highlight na palavra correspondente.
    """
    sc = style_config
    ass_highlight = hex_to_ass_color(sc["highlight_color"])
    ass_base = hex_to_ass_color(sc["base_color"])
    highlight_font_size = int(sc["font_size"] * sc["highlight_scale"] / 100)

    # Style base (ASS) — valores fixos (dialogue sobrescreve tudo)
    base_style = {
        "idx": 0, "name": "style1", "fname": "Arial", "fsize": 20.0,
        "c1": 4294967295, "c2": 3690987520, "c3": 4278190080, "c4": 3690987520,
        "bold": False, "italic": False, "underline": False, "strikeOut": False,
        "scalex": 100, "scaley": 100, "spacing": 0, "angle": 0,
        "borderStyle": 1, "outline": 1.0, "shadow": 0.0, "alignment": 2,
        "ml": 10, "mr": 10, "mv": 10, "encoding": 1,
    }

    words = screen["words"]
    blocks = []

    for i, w in enumerate(words):
        # Timing absoluto na timeline
        start_ms = w["start"] * 1000
        if i + 1 < len(words):
            end_ms = words[i + 1]["start"] * 1000
        else:
            end_ms = w["end"] * 1000
        duration_ms = max(1, end_ms - start_ms)

        text = build_highlight_text(screen, i, ass_highlight, ass_base, sc["font_size"], highlight_font_size)

        dialogue = {
            "idx": 0, "layer": 0, "start": 0, "end": int(duration_ms),
            "style": "style1", "name": "",
            "ml": sc["margin"], "mr": sc["margin"], "mv": 0,
            "effect": "", "text": text, "animation": 0, "has_default": False,
            "animation_delay": 0, "animation_time": 0,
            "fontname": sc["font"], "fontsize": float(sc["font_size"]),
            "bold": 1 if sc["bold"] else 0,
            "italic": sc["italic"], "underline": sc["underline"],
            "textAlign": 1, "alignment": 5,
            "space": sc["space"], "rotation": 0.0, "scale": 100.0,
            "posX": 0.5, "posY": sc["position_y"],
            "blendMode": sc["blend_mode"], "blendOpacity": sc["blend_opacity"],
            "color_mode": sc["color_mode"],
            "fColor": sc["f_color"], "fOpacity": sc["f_opacity"],
            "gStart": sc["g_start"], "gStop": sc["g_stop"],
            "gOpacity": sc["g_opacity"], "gAngle": sc["g_angle"],
            "bdEnable": sc["bd_enable"], "bdColor": sc["bd_color"],
            "bdSize": sc["bd_size"], "bdOpacity": sc["bd_opacity"],
            "bdBlur": sc["bd_blur"],
            "sdEnable": sc["sd_enable"], "sdType": sc["sd_type"],
            "sdColor": sc["sd_color"], "sdOpacity": sc["sd_opacity"],
            "sdDist": sc["sd_dist"],
        }

        block_uuid = "{" + str(uuid.uuid4()).upper() + "}"
        blocks.append({
            "title": w["word"],
            "type": "TextEffectBlock",
            "background": 4229689855,
            "foreground": 1216461823,
            "status": 0,
            "uuid": block_uuid,
            "tstart": start_ms,
            "tduration": duration_ms,
            "restype": "TextEffectResource",
            "resid": "subtitle_001",
            "attribute": {
                "dialogues": [dialogue],
                "styles": [base_style],
                "width": project_width,
                "height": project_height,
                "version": 1,
                "leftTimestamp": -0.1,
                "rightTimestamp": duration_ms / 1000.0 + 0.1,
            },
        })

    return blocks


# ---------------------------------------------------------------------------
# Modificacao do VPD
# ---------------------------------------------------------------------------

def get_project_dimensions(vpd_data):
    """Extrai dimensoes do projeto do projinfo."""
    player = vpd_data.get("projinfo", {}).get("player", {})
    width = player.get("resolutionW", 1080)
    height = player.get("resolutionH", 1920)
    return width, height


def modify_vpd_subtitles(vpd_path, blocks_a, blocks_b):
    """Insere TextEffectBlocks em 2 SubtitleTracks (A e B) no VPD."""
    # Backup
    backup_path = vpd_path + ".bak"
    if not os.path.exists(backup_path):
        shutil.copy2(vpd_path, backup_path)
        print(f"  Backup: {os.path.basename(backup_path)}")

    with open(vpd_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    timeline = data["timeline"]
    tracks = timeline["subitems"]

    # Remover SubtitleTracks existentes
    old_count = 0
    tracks_to_keep = []
    for track in tracks:
        if track["type"] == "SubtitleTrack":
            old_count += len(track.get("subitems", []))
        else:
            tracks_to_keep.append(track)
    if old_count > 0:
        print(f"  SubtitleTracks limpos ({old_count} blocos removidos)")
    timeline["subitems"] = tracks_to_keep

    # Criar 2 SubtitleTracks
    for title, blocks in [("Subtitle A", blocks_a), ("Subtitle B", blocks_b)]:
        context_ms = 0
        if blocks:
            last = blocks[-1]
            context_ms = last["tstart"] + last["tduration"]
        timeline["subitems"].append({
            "title": title,
            "type": "SubtitleTrack",
            "status": 0,
            "subitems": blocks,
            "tstart": 0.0,
            "tduration": 1.7976931348623157e308,
            "context": context_ms,
            "opacity": 100,
            "mute": False,
        })

    # Salvar
    with open(vpd_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    # Reset playhead para o inicio (userdata)
    userdata_path = vpd_path.replace(".vpd", ".userdata")
    if os.path.exists(userdata_path):
        with open(userdata_path, "r", encoding="utf-8") as f:
            ud = json.load(f)
        env = ud.get("environment", {})
        env["timelinePlayPos"] = 0.0
        env["timelineVisibleStart"] = 0.0
        ud["environment"] = env
        with open(userdata_path, "w", encoding="utf-8") as f:
            json.dump(ud, f, indent=4, ensure_ascii=False)
        print(f"  Playhead resetado para inicio")

    total = len(blocks_a) + len(blocks_b)
    print(f"  {total} TextEffectBlocks inseridos (A: {len(blocks_a)}, B: {len(blocks_b)})")
    print(f"  VPD salvo: {os.path.basename(vpd_path)}")


# ---------------------------------------------------------------------------
# Teste de ASS tags
# ---------------------------------------------------------------------------

def create_ass_test_blocks(project_width, project_height):
    """Cria 3 TextEffectBlocks de teste para isolar qual ASS tag causa tachado."""
    tests = [
        ("Teste: cor + fs", 1000, "{\\c&H00FFFF&\\fs78}TESTE{\\c&HFFFFFF&\\fs65} de ASS tags"),
    ]

    base_style = {
        "idx": 0, "name": "style1", "fname": "Arial", "fsize": 20.0,
        "c1": 4294967295, "c2": 3690987520, "c3": 4278190080, "c4": 3690987520,
        "bold": False, "italic": False, "underline": False, "strikeOut": False,
        "scalex": 100, "scaley": 100, "spacing": 0, "angle": 0,
        "borderStyle": 1, "outline": 1.0, "shadow": 0.0, "alignment": 2,
        "ml": 10, "mr": 10, "mv": 10, "encoding": 1,
    }

    blocks = []
    for title, start_ms, text in tests:
        block_uuid = "{" + str(uuid.uuid4()).upper() + "}"
        dialogue = {
            "idx": 0, "layer": 0, "start": 0, "end": 3000,
            "style": "style1", "name": "", "ml": 0, "mr": 0, "mv": 0,
            "effect": "", "text": text, "animation": 0, "has_default": False,
            "animation_delay": 0, "animation_time": 0,
            "fontname": "Arial", "fontsize": 65.0, "bold": 1,
            "italic": False, "underline": False, "textAlign": 1,
            "alignment": 5, "space": 0.0, "rotation": 0.0, "scale": 100.0,
            "posX": 0.5, "posY": 0.50, "blendMode": 0, "blendOpacity": 100,
            "color_mode": 0, "fColor": 4294967295, "fOpacity": 100,
            "gStart": 4294967295, "gStop": 4294967295, "gOpacity": 100, "gAngle": 0,
            "bdEnable": True, "bdColor": 4278190080, "bdSize": 4,
            "bdOpacity": 80, "bdBlur": 0,
            "sdEnable": False, "sdType": 7, "sdColor": 4286611584,
            "sdOpacity": 57, "sdDist": 6,
        }
        blocks.append({
            "title": title, "type": "TextEffectBlock",
            "background": 4229689855, "foreground": 1216461823, "status": 0,
            "uuid": block_uuid, "tstart": float(start_ms), "tduration": 3000.0,
            "restype": "TextEffectResource", "resid": "subtitle_001",
            "attribute": {
                "version": 1, "width": project_width, "height": project_height,
                "leftTimestamp": -0.1, "rightTimestamp": 3.1,
                "dialogues": [dialogue], "styles": [base_style],
            },
        })
    return blocks


# ---------------------------------------------------------------------------
# Deteccao de audio
# ---------------------------------------------------------------------------

def detect_audio(vpd_path):
    """Detecta audio enhanced ou clean na pasta do projeto."""
    vpd_dir = os.path.dirname(vpd_path)
    project_name = os.path.splitext(os.path.basename(vpd_path))[0]

    candidates = [
        os.path.join(vpd_dir, f"{project_name}-enhanced.wav"),
        os.path.join(vpd_dir, f"{project_name}-clean.wav"),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Adiciona legendas palavra-por-palavra ao VPD a partir do audio"
    )
    parser.add_argument("vpd", help="Caminho para o arquivo .vpd do projeto")

    # Audio
    parser.add_argument("--audio", help="Audio para transcrever (default: detecta *-enhanced.wav)")
    parser.add_argument("--whisper-model", default="medium", help="Modelo whisper: tiny/base/small/medium/large (default: medium)")
    parser.add_argument("--language", default="pt", help="Codigo do idioma (default: pt)")

    # Layout
    parser.add_argument("--max-lines", type=int, default=1, help="Max linhas por tela: 1 ou 2 (default: 1)")
    parser.add_argument("--max-chars", type=int, default=28, help="Max caracteres por linha (default: 28)")
    parser.add_argument("--gap-threshold", type=float, default=1.5, help="Pausa minima (s) para quebrar tela (default: 1.5)")

    # Estilo
    parser.add_argument("--style", default="my-style-1", help="Nome do estilo do VideoProc Vlogger (default: my-style-1)")
    parser.add_argument("--highlight-color", default="#9B55FF", help="Cor da palavra em destaque hex (default: #9B55FF roxo)")
    parser.add_argument("--highlight-scale", type=int, default=120, help="Escala da palavra em destaque %% (default: 120)")
    parser.add_argument("--position-y", type=float, default=0.70, help="Posicao vertical 0.0-1.0 (default: 0.70)")
    parser.add_argument("--margin", type=int, default=100, help="Margem lateral em pixels (default: 100)")
    parser.add_argument("--tracks", type=int, default=2, choices=[1, 2], help="Numero de SubtitleTracks: 1 ou 2 (default: 2)")

    # Modo teste
    parser.add_argument("--test-ass", action="store_true", help="Inserir bloco de teste ASS e sair")

    args = parser.parse_args()

    vpd_path = os.path.abspath(args.vpd)
    if not os.path.exists(vpd_path):
        print(f"Arquivo nao encontrado: {vpd_path}", file=sys.stderr)
        sys.exit(1)

    # Ler VPD para dimensoes
    with open(vpd_path, "r", encoding="utf-8") as f:
        vpd_data = json.load(f)
    project_width, project_height = get_project_dimensions(vpd_data)

    print(f"=== vpd-add-subtitles ===")
    print(f"Projeto: {os.path.basename(vpd_path)}")
    print(f"Resolucao: {project_width}x{project_height}")

    # --- Modo teste ASS ---
    if args.test_ass:
        print(f"\n--- Teste de ASS override tags (3 blocos) ---")
        test_blocks = create_ass_test_blocks(project_width, project_height)
        modify_vpd_subtitles(vpd_path, test_blocks, [])
        print(f"\n1 bloco de teste inserido (1s-4s):")
        print(f"  TESTE em amarelo fs78 + resto branco fs65")
        print(f"  Sem tachado esperado.")
        return

    # --- Fluxo normal ---
    # 1. Detectar audio
    audio_path = args.audio
    if not audio_path:
        audio_path = detect_audio(vpd_path)
        if not audio_path:
            print("ERRO: audio nao encontrado. Use --audio para especificar.", file=sys.stderr)
            print(f"  Esperado: <projeto>-enhanced.wav ou <projeto>-clean.wav", file=sys.stderr)
            sys.exit(1)
    else:
        audio_path = os.path.abspath(audio_path)
        if not os.path.exists(audio_path):
            print(f"ERRO: audio nao encontrado: {audio_path}", file=sys.stderr)
            sys.exit(1)

    print(f"Audio: {os.path.basename(audio_path)}")

    # 2. Transcrever com Whisper
    print(f"\n--- Transcricao (Whisper) ---")
    vpd_dir = os.path.dirname(vpd_path)
    words = transcribe(audio_path, args.whisper_model, args.language, vpd_dir)

    if not words:
        print("ERRO: nenhuma palavra transcrita.", file=sys.stderr)
        sys.exit(1)

    # 3. Agrupar palavras em telas
    print(f"\n--- Agrupamento ---")
    screens = group_words_into_screens(words, args.max_lines, args.max_chars, args.gap_threshold)
    print(f"  Telas geradas: {len(screens)}")

    total_words = sum(len(s["words"]) for s in screens)
    print(f"  Palavras totais: {total_words}")

    # Mostrar preview das primeiras telas
    for i, s in enumerate(screens[:3]):
        line_strs = []
        for line in s["lines"]:
            line_strs.append(" ".join(w["word"] for w in line))
        preview = " | ".join(line_strs)
        print(f"  Tela {i}: [{s['start']:.1f}s-{s['end']:.1f}s] {preview}")
    if len(screens) > 3:
        print(f"  ... ({len(screens) - 3} telas restantes)")

    # 4. Gerar TextEffectBlocks
    print(f"\n--- Gerando TextEffectBlocks ---")
    style_config = load_vlogger_style(args.style)
    style_config["highlight_color"] = args.highlight_color
    style_config["highlight_scale"] = args.highlight_scale
    style_config["position_y"] = args.position_y
    style_config["margin"] = args.margin
    # base_color: cor do texto normal (derivada de f_color ARGB)
    fc = style_config["f_color"]
    r, g, b = (fc >> 16) & 0xFF, (fc >> 8) & 0xFF, fc & 0xFF
    style_config["base_color"] = "#{:02X}{:02X}{:02X}".format(r, g, b)
    print(f"  Estilo: {args.style} ({style_config['font']} {style_config['font_size']}pt)")

    text_blocks = []
    for screen in screens:
        blocks = create_text_effect_blocks(screen, style_config, project_width, project_height)
        text_blocks.extend(blocks)

    # 5. Inserir no VPD
    print(f"\n--- Modificando VPD ---")
    if args.tracks == 2:
        blocks_a = [b for i, b in enumerate(text_blocks) if i % 2 == 0]
        blocks_b = [b for i, b in enumerate(text_blocks) if i % 2 == 1]
        print(f"  Blocos: {len(text_blocks)} (A: {len(blocks_a)}, B: {len(blocks_b)})")
        modify_vpd_subtitles(vpd_path, blocks_a, blocks_b)
    else:
        print(f"  Blocos: {len(text_blocks)}")
        modify_vpd_subtitles(vpd_path, text_blocks, [])

    print(f"\nConcluido!")


if __name__ == "__main__":
    main()
