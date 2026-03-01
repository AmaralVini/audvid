#!/usr/bin/env python3
"""Generic image generator using Gemini 2.5 Flash Native.

Usage:
    python3 ai-video/gen-images.py --prompts prompts.json --outdir ai-video/content/my-topic/
    python3 ai-video/gen-images.py --prompts prompts.json --outdir output/ --aspect-ratio 9:16 --workers 3

Input JSON format: {"key": "prompt text", ...}
Output: {outdir}/hook_{key}.png for each entry
"""
import argparse, json, base64, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.error import HTTPError

MODEL = "gemini-2.5-flash-image"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"


def load_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    envfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(envfile):
        with open(envfile) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("ERROR: GEMINI_API_KEY not found in env or .env file", file=sys.stderr)
    sys.exit(1)


def generate(api_key, key, prompt, outdir, aspect_ratio):
    outfile = os.path.join(outdir, f"hook_{key}.png")
    if os.path.exists(outfile):
        return "SKIP", key, outfile
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect_ratio
            }
        }
    }).encode()
    req = Request(ENDPOINT, data=body, headers={
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    })
    try:
        resp = urlopen(req, timeout=120)
        data = json.loads(resp.read())
        candidates = data.get("candidates", [])
        if not candidates:
            return "FAIL", key, "no candidates"
        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            if "inlineData" in part:
                b64 = part["inlineData"].get("data", "")
                if b64:
                    with open(outfile, "wb") as f:
                        f.write(base64.b64decode(b64))
                    return "OK", key, outfile
        return "FAIL", key, "no image data in response"
    except HTTPError as e:
        err_body = e.read().decode() if e.readable() else ""
        return "ERROR", key, f"HTTP {e.code} - {err_body[:200]}"
    except Exception as e:
        return "ERROR", key, str(e)


def main():
    p = argparse.ArgumentParser(description="Generate images from JSON prompts using Gemini Native")
    p.add_argument("--prompts", required=True, help="JSON file with {key: prompt} dict")
    p.add_argument("--outdir", required=True, help="Output directory for generated images")
    p.add_argument("--aspect-ratio", default="16:9", help="Aspect ratio (default: 16:9)")
    p.add_argument("--workers", type=int, default=5, help="Concurrent workers (default: 5)")
    args = p.parse_args()

    with open(args.prompts) as f:
        prompts = json.load(f)

    if not isinstance(prompts, dict) or not prompts:
        print("ERROR: prompts JSON must be a non-empty dict {key: prompt}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.outdir, exist_ok=True)
    api_key = load_api_key()

    print(f"Generating {len(prompts)} images with {MODEL}")
    print(f"Aspect ratio: {args.aspect_ratio} | Workers: {args.workers}")
    print(f"Output: {args.outdir}\n")

    counts = {"OK": 0, "SKIP": 0, "FAIL": 0, "ERROR": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(generate, api_key, key, prompt, args.outdir, args.aspect_ratio): key
            for key, prompt in prompts.items()
        }
        for future in as_completed(futures):
            status, key, detail = future.result()
            counts[status] += 1
            print(f"{status} {key} -> {detail}")

    print(f"\nDone: {counts['OK']} ok, {counts['SKIP']} skipped, {counts['FAIL']} failed, {counts['ERROR']} errors")
    cost = counts["OK"] * 0.039
    if cost > 0:
        print(f"Estimated cost: ${cost:.3f} ({counts['OK']} images x $0.039)")


if __name__ == "__main__":
    main()
