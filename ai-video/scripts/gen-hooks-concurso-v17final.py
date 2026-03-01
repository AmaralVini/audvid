#!/usr/bin/env python3
"""Generate final hook 17 variation: ice boulder, bright environment."""
import json, base64, os
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

PROMPT = (
    "Wide shot of a young person sitting alone at a minimalist desk in a bright, "
    "clean, white modern room with large windows and soft natural daylight flooding in. "
    "An enormous translucent melting ice boulder is balanced on their hunched shoulders "
    "and back, pressing them down. Water droplets and small streams of meltwater dripping "
    "down their arms and onto the desk and floor, forming small puddles. Their face shows "
    "strain and exhaustion. Books and papers on the desk getting wet from the melting ice. "
    "A warm desk lamp on the table. Photorealistic, cinematic wide angle, soft bright "
    "lighting, shallow depth of field, high key photography, film grain."
)

MODELS = {
    "17v5_imagen": ("imagen-4.0-generate-001", "imagen"),
    "17v5_gemini": ("gemini-2.5-flash-image", "native"),
}


def generate_imagen(key, model):
    outfile = os.path.join(OUTDIR, f"hook_{key}.png")
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict"
    body = json.dumps({
        "instances": [{"prompt": PROMPT}],
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
    return f"OK {key} -> {outfile}"


def generate_native(key, model):
    outfile = os.path.join(OUTDIR, f"hook_{key}.png")
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = json.dumps({
        "contents": [{"parts": [{"text": PROMPT}]}],
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
            return f"OK {key} -> {outfile}"
    return f"FAIL {key}: no image"


if __name__ == "__main__":
    print("Generating hook 17 final (ice boulder, bright room)\n")
    for key, (model, api) in MODELS.items():
        try:
            fn = generate_native if api == "native" else generate_imagen
            print(fn(key, model))
        except Exception as e:
            print(f"ERROR {key}: {e}")
