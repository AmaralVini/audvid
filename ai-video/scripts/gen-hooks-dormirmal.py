#!/usr/bin/env python3
"""Generate 20 hook images for DormirMal using Gemini Native (gemini-2.5-flash-image)."""
import json, base64, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

API_KEY = os.environ.get("GEMINI_API_KEY") or open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
).read().split("=", 1)[1].strip()

MODEL = "gemini-2.5-flash-image"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "content", "hooks-dormirmal")
os.makedirs(OUTDIR, exist_ok=True)

PROMPTS = {
    "01": "A person lying in bed at night with eyes wide open, dozens of glowing browser tabs floating above their head in the dark, each tab showing a different unfinished task, photorealistic, dramatic lighting",
    "02": "Split screen: left side shows a chaotic messy desk with papers flying, right side shows the same person tossing and turning in bed, connected by glowing neural pathways, cinematic",
    "03": "A brain made of tangled electrical wires sparking and overheating on a pillow at night, dark bedroom background, dramatic close-up, photorealistic",
    "04": "Person sitting on bed at 3AM staring at a giant floating to-do list that glows ominously in the dark room, overwhelmed expression, cinematic lighting",
    "05": "A clock melting Salvador Dali style on a nightstand while a person sleeps restlessly, surrounded by floating sticky notes and reminders, surreal photorealistic",
    "06": "Close-up of a person's face half-submerged in a pillow, one eye open in anxiety, with a transparent overlay of spinning gears and cogs inside their skull, dramatic",
    "07": "A bed covered in hundreds of crumpled papers and post-it notes instead of sheets, person trying to sleep on top of them, overhead shot, photorealistic",
    "08": "Person lying in bed with a phone charging cable plugged into their temple, showing battery at 3 percent that never charges, dark moody lighting",
    "09": "A peaceful bedroom scene where the pillow is replaced by a laptop with 47 open tabs, person resting their head on it uncomfortably, photorealistic",
    "10": "Giant hourglass on a nightstand with tasks and words falling instead of sand, person watching it anxiously from bed, cinematic blue lighting",
    "11": "Person in bed surrounded by floating holographic screens showing emails, messages, calendars, and alerts, all glowing in the dark, cyberpunk style photorealistic",
    "12": "A human silhouette in bed with the brain area glowing bright red like an overheated engine, steam rising from the head, dark room, dramatic contrast",
    "13": "An alarm clock showing 2:37 AM in sharp focus, background blurred showing a person sitting up in bed holding their head, exhausted expression, cinematic",
    "14": "A brain sitting on a desk chair working at a computer while the body lies empty in bed trying to sleep, surreal split composition, photorealistic",
    "15": "Person in bed being pulled by dozens of puppet strings attached to floating task icons, email, phone, calendar, work, dark dramatic lighting",
    "16": "Close-up of bloodshot exhausted eyes reflected in a phone screen showing the time 4:12 AM, dark bedroom, photorealistic macro shot",
    "17": "A switch on a wall labeled ON OFF next to a bed, but the switch is stuck on ON with sparks flying, person frustrated in bed, dramatic lighting",
    "18": "Person lying in bed with a thought bubble above showing a chaotic highway traffic jam of ideas and tasks crashing into each other, photorealistic surreal",
    "19": "A peaceful bed split in half, one side is calm with soft moonlight, the other side is chaotic with papers, screens and alarms, person stuck on the chaotic side",
    "20": "Overhead shot of a person in bed forming the center of a spiral of floating sticky notes, phone notifications, and calendar alerts spinning around them like a vortex, dramatic dark lighting",
}


def generate(num, prompt):
    outfile = os.path.join(OUTDIR, f"hook_{num}.png")
    if os.path.exists(outfile):
        return f"SKIP {num} (exists)"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": "16:9"
            }
        }
    }).encode()
    req = Request(ENDPOINT, data=body, headers={
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json",
    })
    try:
        resp = urlopen(req, timeout=120)
        data = json.loads(resp.read())
        candidates = data.get("candidates", [])
        if not candidates:
            return f"FAIL {num}: no candidates"
        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            if "inlineData" in part:
                b64 = part["inlineData"].get("data", "")
                if b64:
                    with open(outfile, "wb") as f:
                        f.write(base64.b64decode(b64))
                    return f"OK {num} -> {outfile}"
        return f"FAIL {num}: no image in response"
    except Exception as e:
        return f"ERROR {num}: {e}"


with ThreadPoolExecutor(max_workers=5) as pool:
    futures = {pool.submit(generate, num, prompt): num for num, prompt in PROMPTS.items()}
    for future in as_completed(futures):
        print(future.result())
