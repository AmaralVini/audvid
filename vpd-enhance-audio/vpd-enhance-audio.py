#!/usr/bin/env python3
"""
vpd-enhance-audio — Gera áudio limpo (sem cliques) a partir de projetos VideoProc Vlogger (.vpd)

Lê o arquivo .vpd, identifica os pontos de corte no videotrack, extrai os segmentos
de áudio correspondentes, aplica micro-fades nas bordas de cada corte para eliminar
cliques/ruídos, e monta o áudio final com a mesma duração do videotrack.

Uso:
    python3 vpd-enhance-audio.py projeto.vpd
    python3 vpd-enhance-audio.py projeto.vpd -f m4a --fade 10
    python3 vpd-enhance-audio.py projeto.vpd -o saida.wav
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid


SAMPLE_RATE = 44100
CHANNELS = 2
DEFAULT_FADE_MS = 5


def find_binary(name):
    """Encontra o binário (nativo ou .exe no WSL)."""
    if shutil.which(name):
        return name
    exe_name = f"{name}.exe"
    if shutil.which(exe_name):
        return exe_name
    return name


FFMPEG = find_binary("ffmpeg")
FFPROBE = find_binary("ffprobe")
# Se estamos usando .exe, os caminhos passados ao ffmpeg devem ser Windows
USE_WIN_PATHS = FFMPEG.endswith(".exe")


def wsl_to_win(path):
    """Converte caminho WSL /mnt/X/... para Windows X:/... se necessário."""
    if not USE_WIN_PATHS:
        return path
    if path.startswith("/mnt/"):
        # /mnt/c/Users/... → C:/Users/...
        parts = path[5:]  # remove /mnt/
        drive = parts[0].upper()
        rest = parts[1:]  # /Users/...
        return f"{drive}:{rest}"
    return path


def run_ffmpeg(args, description=""):
    """Executa um comando ffmpeg e retorna o resultado."""
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERRO ffmpeg ({description}): {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


def get_audio_duration(path):
    """Retorna a duração de um arquivo de áudio em segundos."""
    cmd = [
        FFPROBE, "-hide_banner", "-loglevel", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        wsl_to_win(path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def parse_vpd(vpd_path):
    """Lê e parseia o arquivo .vpd, retornando as estruturas necessárias."""
    with open(vpd_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    projinfo = data.get("projinfo", {})
    timeline = data["timeline"]
    tracks = timeline["subitems"]

    # Identificar tracks por tipo
    video_track = None
    audio_tracks = []
    for track in tracks:
        if track["type"] == "MainVideoTrack":
            video_track = track
        elif track["type"] == "AudioTrack":
            audio_tracks.append(track)

    # Extrair clips do videotrack
    video_clips = []
    if video_track and "subitems" in video_track:
        for block in video_track["subitems"]:
            if block["type"] == "MediaFileBlock":
                video_clips.append(extract_clip_info(block))

    # Extrair clips dos audiotracks
    audio_clips = []
    for atrack in audio_tracks:
        if "subitems" in atrack:
            for block in atrack["subitems"]:
                if block["type"] == "MediaFileBlock":
                    audio_clips.append(extract_clip_info(block))

    # Construir mapa de recursos (resid → path)
    resources = {}
    for listkey in ["videolist", "audiolist", "imagelist"]:
        reslist = data.get(listkey, {})
        for item in reslist.get("subitems", []):
            if "uuid" in item and "path" in item:
                resources[item["uuid"]] = {
                    "path": item["path"],
                    "duration": item.get("duration", 0)
                }

    # Timeline context (duração total em ms)
    context_ms = timeline.get("context", 0)

    return projinfo, video_clips, audio_clips, resources, context_ms


def extract_clip_info(block):
    """Extrai informações de timing de um MediaFileBlock."""
    attr = block.get("attribute", {})
    speed_attr = attr.get("SpeedAttribute", {})
    speed_data = speed_attr.get("Speed", {}).get("baseData", {})
    audio_attr = attr.get("AudioAttribute", {})

    file_cutted_start = speed_data.get("fileCuttedStart", 0)
    file_cutted_duration = speed_data.get("fileCuttedDuration", 0)
    handled_cutted_duration = speed_data.get("handledCuttedDuration", 0)

    # Speed factor
    if handled_cutted_duration > 0 and file_cutted_duration > 0:
        speed_factor = file_cutted_duration / handled_cutted_duration
    else:
        speed_factor = 1.0

    return {
        "title": block.get("title", ""),
        "uuid": block.get("uuid", ""),
        "tstart_ms": block.get("tstart", 0),
        "tduration_ms": block.get("tduration", 0),
        "resid": block.get("resid", ""),
        "file_cutted_start": file_cutted_start,
        "file_cutted_duration": file_cutted_duration,
        "handled_cutted_duration": handled_cutted_duration,
        "speed_factor": speed_factor,
        "mute": audio_attr.get("mute", False),
        "audio_speed_rate": speed_attr.get("audioSpeedRate", False),
    }


def resolve_resource_path(resid, resources, vpd_dir):
    """Resolve o caminho absoluto (WSL) de um recurso."""
    res = resources.get(resid)
    if not res:
        return None
    path = res["path"]
    # Converter caminho Windows para WSL
    if len(path) >= 2 and path[1] == ":":
        drive = path[0].lower()
        path = f"/mnt/{drive}" + path[2:].replace("\\", "/")
    elif not os.path.isabs(path):
        # Caminho relativo — relativo ao diretório do projeto
        path = os.path.join(vpd_dir, path)
    return path


def extract_source_audio(source_path, temp_dir, resid):
    """Extrai o áudio completo de um arquivo fonte para WAV temporário."""
    out_path = os.path.join(temp_dir, f"source_{resid}.wav")
    if os.path.exists(out_path):
        return out_path  # Já extraído (dedup)

    print(f"  Extraindo áudio de: {os.path.basename(source_path)}")
    ok = run_ffmpeg([
        "-i", wsl_to_win(source_path),
        "-vn", "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS),
        "-f", "wav", wsl_to_win(out_path)
    ], f"extrair áudio de {os.path.basename(source_path)}")

    return out_path if ok else None


def generate_silence(duration_s, temp_dir, label):
    """Gera um segmento de silêncio com duração específica."""
    out_path = os.path.join(temp_dir, f"silence_{label}.wav")
    ok = run_ffmpeg([
        "-f", "lavfi",
        "-i", f"anullsrc=r={SAMPLE_RATE}:cl=stereo",
        "-t", f"{duration_s:.6f}",
        "-f", "wav", wsl_to_win(out_path)
    ], f"silêncio {label}")
    return out_path if ok else None


def process_clip(clip, source_wav, temp_dir, clip_index, fade_ms):
    """Processa um clip individual: extrai, aplica speed e fade."""
    duration_s = clip["tduration_ms"] / 1000.0
    out_path = os.path.join(temp_dir, f"segment_{clip_index:04d}.wav")

    # Clip mutado → silêncio
    if clip["mute"]:
        print(f"  Clip {clip_index:3d}: MUTE ({duration_s:.3f}s)")
        return generate_silence(duration_s, temp_dir, f"mute_{clip_index:04d}")

    # Calcular fade (proteger clips muito curtos)
    fade_s = fade_ms / 1000.0
    if duration_s < fade_s * 4:
        fade_s = duration_s / 4.0

    speed = clip["speed_factor"]
    file_start = clip["file_cutted_start"]
    file_dur = clip["file_cutted_duration"]

    # Construir filtro de áudio
    filters = []

    # Speed change (atempo preserva o pitch original)
    if abs(speed - 1.0) > 0.001:
        # atempo aceita valores entre 0.5 e 100.0
        # Para valores > 2.0, encadear múltiplos filtros atempo
        remaining = speed
        while remaining > 1.001 or remaining < 0.999:
            if remaining > 2.0:
                filters.append("atempo=2.0")
                remaining /= 2.0
            elif remaining < 0.5:
                filters.append("atempo=0.5")
                remaining /= 0.5
            else:
                filters.append(f"atempo={remaining:.6f}")
                remaining = 1.0

    # Fade-in e fade-out
    # Calcular duração após speed para posicionar o fade-out
    after_speed_dur = file_dur / speed if speed > 0 else file_dur
    fade_out_start = max(0, after_speed_dur - fade_s)
    filters.append(f"afade=t=in:d={fade_s:.6f}")
    filters.append(f"afade=t=out:st={fade_out_start:.6f}:d={fade_s:.6f}")

    filter_str = ",".join(filters)

    speed_label = f" speed={speed:.1f}x" if abs(speed - 1.0) > 0.001 else ""
    print(f"  Clip {clip_index:3d}: [{file_start:.3f}s +{file_dur:.3f}s] → {duration_s:.3f}s{speed_label}")

    ok = run_ffmpeg([
        "-ss", f"{file_start:.6f}",
        "-t", f"{file_dur:.6f}",
        "-i", wsl_to_win(source_wav),
        "-af", filter_str,
        "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS),
        "-f", "wav", wsl_to_win(out_path)
    ], f"clip {clip_index}")

    if not ok:
        return None

    # Verificar e ajustar duração exata (truncar ou pad para match perfeito)
    actual_dur = get_audio_duration(out_path)
    if actual_dur is not None:
        diff = abs(actual_dur - duration_s)
        if diff > 0.002:  # Mais de 2ms de diferença
            adjusted_path = os.path.join(temp_dir, f"adjusted_{clip_index:04d}.wav")
            ok = run_ffmpeg([
                "-i", wsl_to_win(out_path),
                "-af", f"apad=whole_dur={duration_s:.6f},atrim=0:{duration_s:.6f}",
                "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS),
                "-f", "wav", wsl_to_win(adjusted_path)
            ], f"ajuste duração clip {clip_index}")
            if ok:
                os.replace(adjusted_path, out_path)

    return out_path


def concat_segments(segment_paths, temp_dir, output_name):
    """Concatena segmentos de áudio usando ffmpeg concat demuxer."""
    concat_list = os.path.join(temp_dir, f"{output_name}_list.txt")
    out_path = os.path.join(temp_dir, f"{output_name}.wav")

    with open(concat_list, "w") as f:
        for seg in segment_paths:
            win_seg = wsl_to_win(seg)
            escaped = win_seg.replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")

    ok = run_ffmpeg([
        "-f", "concat", "-safe", "0",
        "-i", wsl_to_win(concat_list),
        "-c", "copy",
        wsl_to_win(out_path)
    ], f"concatenar {output_name}")

    return out_path if ok else None


def build_audio_track(audio_clips, resources, vpd_dir, temp_dir, total_duration_s, fade_ms):
    """Constrói o áudio do AudioTrack posicionando clips nas posições corretas."""
    if not audio_clips:
        return None

    print(f"\n--- Processando AudioTrack ({len(audio_clips)} clips) ---")

    # Extrair fontes de áudio
    source_cache = {}
    for clip in audio_clips:
        resid = clip["resid"]
        if resid not in source_cache:
            src_path = resolve_resource_path(resid, resources, vpd_dir)
            if src_path and os.path.exists(src_path):
                extracted = extract_source_audio(src_path, temp_dir, resid)
                source_cache[resid] = extracted

    # Processar cada clip
    processed_clips = []
    for i, clip in enumerate(audio_clips):
        source_wav = source_cache.get(clip["resid"])
        if not source_wav:
            print(f"  AudioTrack clip {i}: fonte não encontrada ({clip['resid']})")
            continue

        seg_path = process_clip(clip, source_wav, temp_dir, 9000 + i, fade_ms)
        if seg_path:
            processed_clips.append({
                "path": seg_path,
                "start_s": clip["tstart_ms"] / 1000.0,
                "duration_s": clip["tduration_ms"] / 1000.0
            })

    if not processed_clips:
        return None

    # Criar base de silêncio com duração total
    base_silence = generate_silence(total_duration_s, temp_dir, "audiotrack_base")
    if not base_silence:
        return None

    # Mixar cada clip na posição correta usando adelay + amix
    current_base = base_silence
    for i, pc in enumerate(processed_clips):
        delay_ms = int(pc["start_s"] * 1000)
        mix_out = os.path.join(temp_dir, f"audiotrack_mix_{i}.wav")

        ok = run_ffmpeg([
            "-i", wsl_to_win(current_base),
            "-i", wsl_to_win(pc["path"]),
            "-filter_complex",
            f"[1:a]adelay={delay_ms}|{delay_ms}[delayed];[0:a][delayed]amix=inputs=2:duration=first:normalize=0",
            "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS),
            "-f", "wav", wsl_to_win(mix_out)
        ], f"mixar audiotrack clip {i}")

        if ok:
            current_base = mix_out
        else:
            print(f"  AVISO: falha ao mixar AudioTrack clip {i}", file=sys.stderr)

    return current_base


def mix_tracks(videotrack_path, audiotrack_path, temp_dir):
    """Mixa o áudio do videotrack com o audiotrack."""
    out_path = os.path.join(temp_dir, "mixed_final.wav")

    ok = run_ffmpeg([
        "-i", wsl_to_win(videotrack_path),
        "-i", wsl_to_win(audiotrack_path),
        "-filter_complex",
        "[0:a][1:a]amix=inputs=2:duration=first:normalize=0",
        "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS),
        "-f", "wav", wsl_to_win(out_path)
    ], "mixagem final")

    return out_path if ok else None


def convert_format(wav_path, output_path, fmt):
    """Converte o WAV final para o formato desejado."""
    if fmt == "wav":
        shutil.copy2(wav_path, output_path)
        return True
    elif fmt == "m4a":
        return run_ffmpeg([
            "-i", wsl_to_win(wav_path),
            "-c:a", "aac", "-b:a", "192k",
            wsl_to_win(output_path)
        ], "converter para M4A")
    elif fmt == "flac":
        return run_ffmpeg([
            "-i", wsl_to_win(wav_path),
            "-c:a", "flac",
            wsl_to_win(output_path)
        ], "converter para FLAC")
    else:
        print(f"Formato desconhecido: {fmt}", file=sys.stderr)
        return False


def enhance_audio(input_path, output_path):
    """Envia áudio ao Adobe Podcast Enhance via Playwright e baixa o resultado."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    enhance_script = os.path.join(script_dir, "adobe-enhance.js")

    if not os.path.exists(enhance_script):
        print(f"ERRO: Script não encontrado: {enhance_script}", file=sys.stderr)
        return False

    # Verificar se Node.js está disponível
    node_bin = shutil.which("node") or shutil.which("node.exe")
    if not node_bin:
        print("ERRO: Node.js não encontrado. Instale Node.js para usar o Adobe Enhance.", file=sys.stderr)
        return False

    print(f"  Input: {os.path.basename(input_path)}")

    try:
        # stderr vai direto para o terminal (progresso), stdout é capturado (JSON result)
        # NODE_PATH aponta para o node_modules compartilhado em playwright/
        node_modules_dir = os.path.join(script_dir, "..", "playwright", "node_modules")
        env = os.environ.copy()
        env["NODE_PATH"] = os.path.abspath(node_modules_dir)
        proc = subprocess.run(
            [node_bin, enhance_script, "--input", input_path, "--output", output_path],
            stdout=subprocess.PIPE, stderr=None,  # stderr herda do pai (exibe no terminal)
            text=True,
            cwd=script_dir,
            env=env,
            timeout=15 * 60  # 15 minutos
        )
    except subprocess.TimeoutExpired:
        print("ERRO: Timeout aguardando Adobe Enhance (15 min).", file=sys.stderr)
        return False

    if proc.returncode == 0:
        print(f"  Enhanced: {os.path.basename(output_path)}")
        return True

    # Parsear mensagem de erro do JSON stdout
    error_msg = ""
    stdout = proc.stdout or ""
    try:
        data = json.loads(stdout.strip().split('\n')[-1])
        error_msg = data.get("message", "")
    except (json.JSONDecodeError, IndexError):
        error_msg = stdout.strip()

    if proc.returncode == 2:
        print(f"ERRO: Arquivo de autenticação não encontrado.", file=sys.stderr)
        print(f"  Rode: cd vpd-enhance-audio && node save-session.js", file=sys.stderr)
    elif proc.returncode == 3:
        print(f"ERRO: Sessão Adobe expirada.", file=sys.stderr)
        print(f"  Rode: cd vpd-enhance-audio && node save-session.js", file=sys.stderr)
    else:
        print(f"ERRO: Adobe Enhance falhou (exit {proc.returncode}).", file=sys.stderr)
        if error_msg:
            print(f"  Detalhe: {error_msg}", file=sys.stderr)

    return False


def modify_vpd(vpd_path, clean_audio_path, total_duration_ms):
    """Modifica o VPD: adiciona áudio limpo em novo AudioTrack e muta os demais."""
    with open(vpd_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    timeline = data["timeline"]
    tracks = timeline["subitems"]

    clean_filename = os.path.basename(clean_audio_path)
    duration_s = total_duration_ms / 1000.0

    # Gerar IDs únicos para o novo recurso e bloco
    res_uuid = hashlib.md5(clean_filename.encode()).hexdigest().upper()
    block_uuid = "{" + str(uuid.uuid4()).upper() + "}"

    # --- 1. Mutar MainVideoTrack (track-level) ---
    for track in tracks:
        if track["type"] == "MainVideoTrack":
            track["mute"] = True
            print(f"  MainVideoTrack: mutada")

    # --- 2. Mutar AudioTracks existentes (track-level) ---
    for track in tracks:
        if track["type"] == "AudioTrack":
            track["mute"] = True
            count = len(track.get("subitems", []))
            print(f"  AudioTrack existente: mutada ({count} clips)")

    # --- 3. Adicionar recurso à audiolist ---
    audiolist = data.get("audiolist", {"title": "Music", "type": "ResourceLists", "status": 0})
    if "subitems" not in audiolist:
        audiolist["subitems"] = []
    audiolist["subitems"].append({
        "title": clean_filename.rsplit(".", 1)[0],
        "type": "MediaFileResource",
        "status": 0,
        "uuid": res_uuid,
        "path": clean_filename,
        "duration": duration_s
    })
    data["audiolist"] = audiolist

    # --- 4. Criar novo AudioTrack com o áudio limpo ---
    new_audio_block = {
        "title": clean_filename.rsplit(".", 1)[0],
        "type": "MediaFileBlock",
        "background": 4232007423,
        "foreground": 1216461823,
        "status": 0,
        "uuid": block_uuid,
        "tstart": 0.0,
        "tduration": total_duration_ms,
        "restype": "MediaFileResource",
        "resid": res_uuid,
        "attribute": {
            "version": 0,
            "type": 2,
            "videoIndex": -1,
            "audioIndex": 0,
            "videoEnabled": False,
            "audioEnabled": True,
            "VideoAttribute": None,
            "AudioAttribute": {
                "version": 0,
                "mute": False,
                "fadeInDuration": 0.0,
                "fadeOutDuration": 0.0,
                "multiple": 1.0,
                "pitch": 1.0,
                "pitchType": 1
            },
            "SpeedAttribute": {
                "version": 0,
                "reversePlay": False,
                "Speed": {
                    "version": 0,
                    "baseData": {
                        "version": 0,
                        "fileTotalDuration": duration_s,
                        "fileCuttedStart": 0.0,
                        "fileCuttedDuration": duration_s,
                        "handledTotalDuration": duration_s,
                        "handledCuttedStart": 0.0,
                        "handledCuttedDuration": duration_s
                    },
                    "curve": ""
                },
                "extraSpeed": 1.0,
                "audioSpeedRate": False
            }
        }
    }

    new_audio_track = {
        "title": "Audio Enhanced",
        "type": "AudioTrack",
        "status": 0,
        "subitems": [new_audio_block],
        "tstart": 0.0,
        "tduration": 1.7976931348623157e308,
        "context": total_duration_ms,
        "opacity": 100,
        "mute": False
    }

    # Inserir logo após o último AudioTrack existente
    insert_idx = len(tracks)
    for i, track in enumerate(tracks):
        if track["type"] == "AudioTrack":
            insert_idx = i + 1
    tracks.insert(insert_idx, new_audio_track)
    print(f"  Novo AudioTrack inserido com: {clean_filename}")

    # --- 5. Salvar (backup do original) ---
    backup_path = vpd_path + ".bak"
    if not os.path.exists(backup_path):
        shutil.copy2(vpd_path, backup_path)
        print(f"  Backup: {os.path.basename(backup_path)}")

    with open(vpd_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"  VPD salvo: {os.path.basename(vpd_path)}")


def main():
    parser = argparse.ArgumentParser(
        description="Gera áudio limpo (sem cliques nos cortes) a partir de projetos VideoProc Vlogger (.vpd)"
    )
    parser.add_argument("vpd", help="Caminho para o arquivo .vpd do projeto")
    parser.add_argument("-f", "--format", choices=["wav", "m4a", "flac"], default="wav",
                        help="Formato de saída (padrão: wav)")
    parser.add_argument("--fade", type=float, default=DEFAULT_FADE_MS,
                        help=f"Duração do fade em milissegundos (padrão: {DEFAULT_FADE_MS})")
    parser.add_argument("-o", "--output", help="Caminho do arquivo de saída (padrão: mesmo diretório do .vpd)")
    parser.add_argument("--skip-enhance", action="store_true",
                        help="Skip Adobe Enhance, use clean audio directly in VPD")
    args = parser.parse_args()

    vpd_path = os.path.abspath(args.vpd)
    if not os.path.exists(vpd_path):
        print(f"Arquivo não encontrado: {vpd_path}", file=sys.stderr)
        sys.exit(1)

    vpd_dir = os.path.dirname(vpd_path)
    project_name = os.path.splitext(os.path.basename(vpd_path))[0]

    # Determinar caminho de saída
    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        output_path = os.path.join(vpd_dir, f"{project_name}-clean.{args.format}")

    # Diretório temporário na mesma partição (acessível ao ffmpeg Windows/.exe)
    temp_dir = tempfile.mkdtemp(prefix="vpd_clean_", dir=vpd_dir)

    print(f"=== vpd-enhance-audio ===")
    print(f"Projeto: {project_name}")
    print(f"Fade: {args.fade}ms")
    print(f"Formato: {args.format}")
    print(f"Saída: {output_path}")
    if USE_WIN_PATHS:
        print(f"ffmpeg: {FFMPEG} (Windows, caminhos convertidos)")

    # Passo 1: Parse do VPD
    print(f"\n--- Parsing do VPD ---")
    projinfo, video_clips, audio_clips, resources, context_ms = parse_vpd(vpd_path)

    # Ordenar clips por tstart
    video_clips.sort(key=lambda c: c["tstart_ms"])
    audio_clips.sort(key=lambda c: c["tstart_ms"])

    total_duration_ms = context_ms
    if total_duration_ms <= 0 and video_clips:
        last = video_clips[-1]
        total_duration_ms = last["tstart_ms"] + last["tduration_ms"]
    total_duration_s = total_duration_ms / 1000.0

    # Estatísticas
    muted_count = sum(1 for c in video_clips if c["mute"])
    speed_count = sum(1 for c in video_clips if abs(c["speed_factor"] - 1.0) > 0.001)
    print(f"VideoTrack: {len(video_clips)} clips ({muted_count} mutados, {speed_count} com speed)")
    print(f"AudioTrack: {len(audio_clips)} clips")
    print(f"Duração total: {total_duration_s:.3f}s ({total_duration_ms:.2f}ms)")
    print(f"Recursos: {len(resources)} arquivos")

    try:
        # Passo 2: Extrair áudio das fontes
        print(f"\n--- Extraindo áudio das fontes ---")
        source_cache = {}
        for clip in video_clips:
            resid = clip["resid"]
            if resid not in source_cache:
                src_path = resolve_resource_path(resid, resources, vpd_dir)
                if src_path and os.path.exists(src_path):
                    extracted = extract_source_audio(src_path, temp_dir, resid)
                    source_cache[resid] = extracted
                else:
                    print(f"  AVISO: fonte não encontrada para resid={resid}: {src_path}")
                    source_cache[resid] = None

        # Passo 3: Processar cada clip do VideoTrack
        print(f"\n--- Processando {len(video_clips)} clips do VideoTrack ---")
        segments = []
        current_pos_ms = 0.0

        for i, clip in enumerate(video_clips):
            # Verificar gap antes deste clip
            gap_ms = clip["tstart_ms"] - current_pos_ms
            if gap_ms > 0.5:  # Gap > 0.5ms
                gap_s = gap_ms / 1000.0
                print(f"  Gap: {gap_s:.3f}s de silêncio")
                silence = generate_silence(gap_s, temp_dir, f"gap_{i:04d}")
                if silence:
                    segments.append(silence)

            # Processar o clip
            source_wav = source_cache.get(clip["resid"])
            if not source_wav:
                dur_s = clip["tduration_ms"] / 1000.0
                print(f"  Clip {i:3d}: fonte indisponível, inserindo silêncio ({dur_s:.3f}s)")
                silence = generate_silence(dur_s, temp_dir, f"nosrc_{i:04d}")
                if silence:
                    segments.append(silence)
            else:
                seg = process_clip(clip, source_wav, temp_dir, i, args.fade)
                if seg:
                    segments.append(seg)
                else:
                    dur_s = clip["tduration_ms"] / 1000.0
                    silence = generate_silence(dur_s, temp_dir, f"fail_{i:04d}")
                    if silence:
                        segments.append(silence)

            current_pos_ms = clip["tstart_ms"] + clip["tduration_ms"]

        if not segments:
            print("ERRO: nenhum segmento processado!", file=sys.stderr)
            sys.exit(1)

        # Passo 4: Concatenar segmentos do VideoTrack
        print(f"\n--- Concatenando {len(segments)} segmentos ---")
        videotrack_wav = concat_segments(segments, temp_dir, "videotrack")
        if not videotrack_wav:
            print("ERRO: falha na concatenação!", file=sys.stderr)
            sys.exit(1)

        # Passo 5: Processar AudioTrack e mixar
        final_wav = videotrack_wav
        if audio_clips:
            audiotrack_wav = build_audio_track(
                audio_clips, resources, vpd_dir, temp_dir,
                total_duration_s, args.fade
            )
            if audiotrack_wav:
                print(f"\n--- Mixando VideoTrack + AudioTrack ---")
                mixed = mix_tracks(videotrack_wav, audiotrack_wav, temp_dir)
                if mixed:
                    final_wav = mixed
                else:
                    print("  AVISO: falha na mixagem, usando só VideoTrack")

        # Passo 6: Converter formato e salvar
        print(f"\n--- Salvando resultado ---")
        ok = convert_format(final_wav, output_path, args.format)
        if not ok:
            print("ERRO: falha ao salvar arquivo final!", file=sys.stderr)
            sys.exit(1)

        # Passo 6.5: Adobe Podcast Enhance (padrão)
        if args.skip_enhance:
            vpd_audio_path = output_path
        else:
            enhanced_path = os.path.join(vpd_dir, f"{project_name}-enhanced.{args.format}")
            print(f"\n--- Adobe Podcast Enhance ---")
            if os.path.exists(enhanced_path):
                print(f"  Arquivo enhanced já existe: {os.path.basename(enhanced_path)}")
                print(f"  Pulando enhance.")
                ok = True
            else:
                ok = enhance_audio(output_path, enhanced_path)
            if ok and os.path.exists(enhanced_path):
                vpd_audio_path = enhanced_path
            else:
                print("ERRO: Enhancement falhou.", file=sys.stderr)
                print("  Opções:", file=sys.stderr)
                print(f"  1. Faça o enhance manualmente em https://podcast.adobe.com/en/enhance", file=sys.stderr)
                print(f"     e salve como: {enhanced_path}", file=sys.stderr)
                print(f"  2. Rode novamente com --skip-enhance para usar o áudio clean", file=sys.stderr)
                sys.exit(1)

        # Passo 7: Modificar o VPD (inserir áudio limpo + mutar demais)
        print(f"\n--- Modificando VPD ---")
        modify_vpd(vpd_path, vpd_audio_path, total_duration_ms)

        # Passo 8: Verificação
        final_duration = get_audio_duration(vpd_audio_path)
        if final_duration is not None:
            diff_ms = abs(final_duration * 1000 - total_duration_ms)
            status = "OK" if diff_ms < 50 else "AVISO"
            print(f"\n=== Resultado ===")
            print(f"Arquivo: {vpd_audio_path}")
            print(f"Duração esperada: {total_duration_s:.3f}s")
            print(f"Duração obtida:   {final_duration:.3f}s")
            print(f"Diferença:        {diff_ms:.1f}ms [{status}]")
            print(f"Clips processados: {len(video_clips)} video + {len(audio_clips)} audio")
            print(f"Clips mutados:     {muted_count}")
            print(f"Clips com speed:   {speed_count}")
        else:
            print(f"\nArquivo salvo: {vpd_audio_path}")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    print("Concluído!")


if __name__ == "__main__":
    main()
