#!/usr/bin/env python3
"""Generate variations of hook 17 (peso invisível) in landscape 16:9."""
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

VARIATIONS = [
    {
        "key": "17v1_gemini",
        "model": "gemini-2.5-flash-image",
        "api": "native",
        "prompt": "A student sitting at a desk struggling to study, crushed under a massive transparent glass boulder on their shoulders and back. The boulder has faint floating text inside: question marks, clock icons, and exclamation marks. Papers and books scattered on desk. Dramatic cinematic side lighting, dark moody background, photorealistic, wide landscape composition, shallow depth of field.",
    },
    {
        "key": "17v2_gemini",
        "model": "gemini-2.5-flash-image",
        "api": "native",
        "prompt": "Wide shot of a young person sitting alone at a desk in a vast dark empty room, an enormous translucent crystal rock balanced on their hunched shoulders, pressing them down. Their face shows strain and exhaustion. A single warm desk lamp illuminates the scene. Books and papers on the desk. Photorealistic, cinematic wide angle, dramatic chiaroscuro lighting, film grain, dark atmospheric mood.",
    },
    {
        "key": "17v3_imagen",
        "model": "imagen-4.0-generate-001",
        "api": "imagen",
        "prompt": "A student sitting at a desk struggling to study, crushed under a massive transparent glass boulder on their shoulders and back. The boulder has faint floating question marks and clock icons inside. Papers and books scattered on desk. Dramatic cinematic side lighting, dark moody background, photorealistic, wide landscape composition, shallow depth of field.",
    },
    {
        "key": "17v4_imagen",
        "model": "imagen-4.0-generate-001",
        "api": "imagen",
        "prompt": "Wide shot of a young person sitting alone at a desk in a vast dark empty room, an enormous translucent crystal rock balanced on their hunched shoulders, pressing them down. Their face shows strain and exhaustion. A single warm desk lamp illuminates the scene. Books and papers on the desk. Photorealistic, cinematic wide angle, dramatic chiaroscuro lighting, film grain, dark atmospheric mood.",
    },
]


def generate_native(key, model, prompt):
    """Gemini Native API (generateContent)."""
    outfile = os.path.join(OUTDIR, f"hook_{key}.png")
    if os.path.exists(outfile):
        return f"SKIP {key} (exists)"
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
    try:
        resp = urlopen(req, timeout=120)
        data = json.loads(resp.read())
        for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                with open(outfile, "wb") as f:
                    f.write(base64.b64decode(part["inlineData"]["data"]))
                return f"OK {key} -> {outfile}"
        return f"FAIL {key}: no image in response"
    except HTTPError as e:
        return f"ERROR {key}: HTTP {e.code} - {e.read().decode()[:200]}"
    except Exception as e:
        return f"ERROR {key}: {e}"


def generate_imagen(key, model, prompt):
    """Imagen API (predict)."""
    outfile = os.path.join(OUTDIR, f"hook_{key}.png")
    if os.path.exists(outfile):
        return f"SKIP {key} (exists)"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict"
    body = json.dumps({
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "16:9", "personGeneration": "allow_all"}
    }).encode()
    req = Request(endpoint, data=body, headers={
        "x-goog-api-key": API_KEY, "Content-Type": "application/json"
    })
    try:
        resp = urlopen(req, timeout=120)
        data = json.loads(resp.read())
        preds = data.get("predictions", [])
        if not preds:
            return f"FAIL {key}: no predictions"
        b64 = preds[0].get("bytesBase64Encoded", "")
        if not b64:
            return f"FAIL {key}: no image data"
        with open(outfile, "wb") as f:
            f.write(base64.b64decode(b64))
        return f"OK {key} -> {outfile}"
    except HTTPError as e:
        return f"ERROR {key}: HTTP {e.code} - {e.read().decode()[:200]}"
    except Exception as e:
        return f"ERROR {key}: {e}"


if __name__ == "__main__":
    print(f"Generating {len(VARIATIONS)} variations of hook 17 (peso invisível)")
    print(f"Output: {OUTDIR}\n")
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {}
        for v in VARIATIONS:
            fn = generate_native if v["api"] == "native" else generate_imagen
            futures[pool.submit(fn, v["key"], v["model"], v["prompt"])] = v["key"]
        ok = fail = 0
        for future in as_completed(futures):
            result = future.result()
            print(result)
            if result.startswith("OK") or result.startswith("SKIP"):
                ok += 1
            else:
                fail += 1
    print(f"\nDone: {ok} success, {fail} failed")
