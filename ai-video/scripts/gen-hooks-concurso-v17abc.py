#!/usr/bin/env python3
"""Generate images for video prompt options A, B, C using both models."""
import json, base64, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_KEY = os.environ.get("GEMINI_API_KEY") or ""
if not API_KEY:
    envfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    if os.path.exists(envfile):
        for line in open(envfile):
            if line.strip().startswith("GEMINI_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1].strip().strip('"').strip("'")

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "content", "hooks-concurso")
os.makedirs(OUTDIR, exist_ok=True)

PROMPTS = {
    "17a": (
        "Wide shot of a young man sitting at a desk in a bright white modern room with "
        "large windows and natural daylight. A massive translucent ice boulder sits on "
        "his hunched shoulders, slowly melting. Water streams down his arms, drips off "
        "the desk, forming growing puddles on the floor. His body trembles under the "
        "weight. Books and papers on the desk get soaked. The ice has small cracks. "
        "Camera angle slowly pushing in toward his strained face. Photorealistic, "
        "cinematic, shallow depth of field, bright high key lighting."
    ),
    "17b": (
        "Wide shot of a young man crushed under a giant melting ice boulder at a desk "
        "in a bright clean white room with large windows. Water dripping everywhere, "
        "puddles on the floor. The ice is cracking and splitting into pieces, water "
        "splashing dramatically across the desk and floor, soaking all the books and "
        "papers. The man collapses forward onto the desk in exhaustion. Dramatic slow "
        "motion water splash frozen in mid-air. Photorealistic, cinematic, bright "
        "lighting, high speed photography feel, sharp detail."
    ),
    "17c": (
        "Wide shot of a young man sitting at a desk in a bright white room with large "
        "windows. A massive ice boulder melts on his shoulders, water streaming down. "
        "The desk is soaked, papers ruined. He slowly lifts his head with determination, "
        "reaching for a warm glowing desk lamp. Where the warm golden light touches the "
        "ice, it melts faster with beautiful steam rising. A subtle hopeful smile on his "
        "face. The warm golden light contrasts with the cold blue ice and water. "
        "Photorealistic, cinematic, dramatic contrast between warm golden and cold blue "
        "color temperatures, shallow depth of field."
    ),
}

MODELS = [
    ("imagen", "imagen-4.0-generate-001"),
    ("gemini", "gemini-2.5-flash-image"),
]


def generate_imagen(key, model, prompt):
    outfile = os.path.join(OUTDIR, f"hook_{key}_imagen.png")
    if os.path.exists(outfile):
        return f"SKIP {key}_imagen (exists)"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict"
    body = json.dumps({
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "16:9", "personGeneration": "allow_all"}
    }).encode()
    req = Request(endpoint, data=body, headers={
        "x-goog-api-key": API_KEY, "Content-Type": "application/json"
    })
    resp = urlopen(req, timeout=120)
    data = json.loads(resp.read())
    b64 = data["predictions"][0]["bytesBase64Encoded"]
    with open(outfile, "wb") as f:
        f.write(base64.b64decode(b64))
    return f"OK {key}_imagen -> {outfile}"


def generate_native(key, model, prompt):
    outfile = os.path.join(OUTDIR, f"hook_{key}_gemini.png")
    if os.path.exists(outfile):
        return f"SKIP {key}_gemini (exists)"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "16:9"}
        }
    }).encode()
    req = Request(endpoint, data=body, headers={
        "x-goog-api-key": API_KEY, "Content-Type": "application/json"
    })
    resp = urlopen(req, timeout=120)
    data = json.loads(resp.read())
    for part in data["candidates"][0]["content"]["parts"]:
        if "inlineData" in part:
            with open(outfile, "wb") as f:
                f.write(base64.b64decode(part["inlineData"]["data"]))
            return f"OK {key}_gemini -> {outfile}"
    return f"FAIL {key}_gemini: no image"


if __name__ == "__main__":
    tasks = []
    for key, prompt in PROMPTS.items():
        for tag, model in MODELS:
            tasks.append((key, tag, model, prompt))

    print(f"Generating {len(tasks)} images (3 prompts x 2 models)\n")
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {}
        for key, tag, model, prompt in tasks:
            fn = generate_native if tag == "gemini" else generate_imagen
            futures[pool.submit(fn, key, model, prompt)] = f"{key}_{tag}"
        ok = fail = 0
        for future in as_completed(futures):
            try:
                result = future.result()
                print(result)
                if result.startswith("OK") or result.startswith("SKIP"):
                    ok += 1
                else:
                    fail += 1
            except Exception as e:
                print(f"ERROR {futures[future]}: {e}")
                fail += 1
    print(f"\nDone: {ok} success, {fail} failed")
