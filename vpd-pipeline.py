#!/usr/bin/env python3
"""
vpd-pipeline — Pipeline completo: enhance audio + legendas

Encadeia vpd-enhance-audio e vpd-add-subtitles em um unico comando.
Requer conda env pt-gpu ativado para o whisper (vpd-add-subtitles).

Uso:
    conda activate pt-gpu
    python3 vpd-pipeline.py projeto.vpd
    python3 vpd-pipeline.py projeto.vpd --skip-enhance
    python3 vpd-pipeline.py projeto.vpd --skip-subtitles
"""

import argparse
import os
import subprocess
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENHANCE_SCRIPT = os.path.join(SCRIPT_DIR, "vpd-enhance-audio", "vpd-enhance-audio.py")
SUBTITLES_SCRIPT = os.path.join(SCRIPT_DIR, "vpd-add-subtitles", "vpd-add-subtitles.py")


def run_step(description, cmd):
    """Executa um passo do pipeline, herdando stdin/stdout/stderr."""
    print(f"\n{'=' * 60}")
    print(f"  {description}")
    print(f"{'=' * 60}\n")

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\nERRO: {description} falhou (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


def detect_audio(vpd_path, prefer_enhanced=True):
    """Detecta audio na pasta do projeto."""
    vpd_dir = os.path.dirname(vpd_path)
    project_name = os.path.splitext(os.path.basename(vpd_path))[0]

    if prefer_enhanced:
        candidates = [f"{project_name}-enhanced.wav", f"{project_name}-clean.wav"]
    else:
        candidates = [f"{project_name}-clean.wav", f"{project_name}-enhanced.wav"]

    for name in candidates:
        path = os.path.join(vpd_dir, name)
        if os.path.exists(path):
            return path

    return None


def main():
    parser = argparse.ArgumentParser(description="Pipeline completo: enhance audio + legendas para projetos VPD")
    parser.add_argument("vpd", help="Caminho para o arquivo .vpd do projeto")
    parser.add_argument("--skip-enhance", action="store_true", help="Pular etapa de enhance audio")
    parser.add_argument("--skip-subtitles", action="store_true", help="Pular etapa de legendas")

    # Opcoes de enhance
    parser.add_argument("--enhance-skip-adobe", action="store_true", help="Pular Adobe Enhance (usar audio clean)")
    parser.add_argument("--fade", type=float, help="Duracao do fade em ms (enhance)")

    # Opcoes de subtitles
    parser.add_argument("--audio", help="Audio para transcrever (default: detecta automaticamente)")
    parser.add_argument("--whisper-model", default="medium", help="Modelo whisper (default: medium)")
    parser.add_argument("--language", default="pt", help="Idioma (default: pt)")
    parser.add_argument("--max-lines", type=int, help="Max linhas por tela")
    parser.add_argument("--max-chars", type=int, help="Max caracteres por linha")
    parser.add_argument("--gap-threshold", type=float, help="Pausa minima (s) para quebrar tela")
    parser.add_argument("--style", help="Nome do estilo do VideoProc Vlogger")
    parser.add_argument("--highlight-color", help="Cor da palavra em destaque hex")
    parser.add_argument("--highlight-scale", type=int, help="Escala da palavra em destaque %%")
    parser.add_argument("--position-y", type=float, help="Posicao vertical 0.0-1.0")

    args = parser.parse_args()

    vpd_path = os.path.abspath(args.vpd)
    if not os.path.exists(vpd_path):
        print(f"Arquivo nao encontrado: {vpd_path}", file=sys.stderr)
        sys.exit(1)

    print(f"=== vpd-pipeline ===")
    print(f"Projeto: {os.path.basename(vpd_path)}")
    print(f"Enhance: {'SKIP' if args.skip_enhance else 'sim'}")
    print(f"Subtitles: {'SKIP' if args.skip_subtitles else 'sim'}")

    # --- Passo 1: Enhance Audio ---
    if not args.skip_enhance:
        enhance_cmd = [sys.executable, ENHANCE_SCRIPT, vpd_path]
        if args.enhance_skip_adobe:
            enhance_cmd.append("--skip-enhance")
        if args.fade is not None:
            enhance_cmd.extend(["--fade", str(args.fade)])

        run_step("vpd-enhance-audio", enhance_cmd)

    # --- Passo 2: Detectar audio ---
    audio_path = args.audio
    if not audio_path and not args.skip_subtitles:
        audio_path = detect_audio(vpd_path, prefer_enhanced=not args.skip_enhance)
        if not audio_path:
            print("ERRO: audio nao encontrado para legendas.", file=sys.stderr)
            print("  Use --audio para especificar ou rode enhance primeiro.", file=sys.stderr)
            sys.exit(1)
        print(f"\nAudio detectado: {os.path.basename(audio_path)}")

    # --- Passo 3: Subtitles ---
    if not args.skip_subtitles:
        sub_cmd = [sys.executable, SUBTITLES_SCRIPT, vpd_path, "--audio", audio_path, "--whisper-model", args.whisper_model, "--language", args.language]

        # Passar opcoes opcionais
        if args.max_lines is not None:
            sub_cmd.extend(["--max-lines", str(args.max_lines)])
        if args.max_chars is not None:
            sub_cmd.extend(["--max-chars", str(args.max_chars)])
        if args.gap_threshold is not None:
            sub_cmd.extend(["--gap-threshold", str(args.gap_threshold)])
        if args.style is not None:
            sub_cmd.extend(["--style", args.style])
        if args.highlight_color is not None:
            sub_cmd.extend(["--highlight-color", args.highlight_color])
        if args.highlight_scale is not None:
            sub_cmd.extend(["--highlight-scale", str(args.highlight_scale)])
        if args.position_y is not None:
            sub_cmd.extend(["--position-y", str(args.position_y)])

        run_step("vpd-add-subtitles", sub_cmd)

    print(f"\n{'=' * 60}")
    print(f"  Pipeline concluido!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
