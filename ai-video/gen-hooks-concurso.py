#!/usr/bin/env python3
"""Generate 20 hook images for concurso ad using Gemini 2.5 Flash Native."""
import json, base64, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_KEY = os.environ.get("GEMINI_API_KEY") or ""
if not API_KEY:
    envfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(envfile):
        for line in open(envfile):
            if line.strip().startswith("GEMINI_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1].strip().strip('"').strip("'")

MODEL = "gemini-2.5-flash-image"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hooks-concurso")
os.makedirs(OUTDIR, exist_ok=True)

PROMPTS = {
    "01_cerebro_sobrecarregado":
        "A person sitting at a desk overwhelmed by studying, head in hands, surrounded by floating clocks, scattered books, and glowing question marks. Dramatic overhead lighting casting harsh shadows. Photorealistic, cinematic mood, shallow depth of field. Dark moody atmosphere with warm desk lamp as only light source.",
    "02_encruzilhada_decisoes":
        "A tired young person standing at a crossroads with dozens of paths and arrows pointing in every direction, holding books and looking confused and exhausted. Dramatic fog, dark blue and orange cinematic lighting. Photorealistic, wide angle, epic scale. The paths have labels like clocks, books, and phones floating above them.",
    "03_relogio_derretendo":
        "Close-up of a stressed student at a desk with melting clocks dripping off the table like Salvador Dali, papers flying chaotically around. One side of the image is dark and chaotic, the other side is clean and organized with golden light. Split composition, photorealistic with surreal elements. Cinematic dramatic lighting.",
    "04_bateria_zerada":
        "A young person studying at a desk at night, above their head a glowing battery icon showing critically low at 5 percent red. Scattered papers, multiple open books, dim blue screen light on their face. Photorealistic, vertical composition for mobile, neon glow effects, dark background.",
    "05_contraste_caos_ordem":
        "Split image: left side shows a chaotic messy desk with scattered papers, multiple clocks showing different times, stressed person with head down, dark red lighting. Right side shows the same desk perfectly organized, clean schedule on wall, person studying focused and calm, warm golden lighting. Photorealistic, dramatic contrast, cinematic.",
    "06_labirinto_mental":
        "Aerial view of a person trapped inside a giant brain-shaped maze, holding books and looking lost. Dead ends everywhere with signs showing question marks and clocks. Foggy atmosphere, dramatic top-down cinematic lighting, photorealistic, dark teal and orange color grade.",
    "07_ampulheta_quebrando":
        "A giant hourglass cracking and shattering in the center of the frame, sand spilling everywhere onto open books and study materials. A student watches in shock from behind. Dramatic freeze-frame moment, glass shards suspended in air, golden sand particles catching light. Photorealistic, dark background, epic cinematic lighting.",
    "08_marionete_decisoes":
        "A young student being pulled in multiple directions by puppet strings attached to their arms, each string connected to a different object: a phone, a clock, a book, a coffee cup, a TV remote. Dramatic low-angle shot, dark theatrical stage lighting, photorealistic, moody atmosphere.",
    "09_afogando_postits":
        "A person drowning in a sea of colorful post-it notes and to-do lists, only their hand visible reaching up for help, holding a pen. Notes have scribbled text and question marks. Overhead dramatic shot, photorealistic, shallow depth of field, warm chaotic colors against dark background.",
    "10_cerebro_curtocircuito":
        "Close-up portrait of a student with eyes closed, electrical sparks and short circuits visually emanating from their head like an overloaded machine. Smoke rising slightly. Blue and orange electric arcs. Dark background, dramatic studio lighting, photorealistic with VFX elements, vertical composition.",
    "11_domino_erros":
        "A long line of black dominoes falling in chain reaction on a desk full of study materials. Each domino is labeled with small icons of clocks, phones, and books. The student watches helplessly from the end of the chain. Dramatic side lighting, slow-motion feel, photorealistic, cinematic shallow depth of field.",
    "12_dois_relogios":
        "Split portrait of the same person: left side showing them at 7AM fresh and motivated with a sunrise behind, right side showing them at 11PM exhausted, dark circles, messy hair, same desk but now chaotic. A clock visible on each side. Hard vertical split line, photorealistic, dramatic contrast in color temperature — warm vs cold blue.",
    "13_bussola_quebrada":
        "A hand holding a broken compass with the needle spinning wildly, background blurred showing a desk with scattered study materials and multiple open books. The compass glass is cracked. Macro close-up, cinematic bokeh, moody dark atmosphere, photorealistic, warm tungsten highlights.",
    "14_xadrez_contra_si":
        "A student playing chess against themselves on a desk covered with books, both sides losing. Knocked over pieces everywhere. The board is cracked down the middle. Dramatic overhead lighting casting long shadows, dark moody atmosphere, photorealistic, shallow depth of field.",
    "15_notificacoes_atacando":
        "A student trying to study while dozens of glowing smartphone notifications float aggressively around their head like a swarm of insects. Each notification shows alarms, messages, reminders, social media icons. The student shields their face with a book. Dark background, neon glow on face, photorealistic, vertical mobile composition.",
    "16_escada_infinita":
        "A student climbing an impossible Escher-like infinite staircase made of books, going nowhere, visibly exhausted. Other students on parallel staircases also stuck. Surreal architecture, dramatic fog, dark blue and purple atmosphere, cinematic wide angle, photorealistic with surreal geometry.",
    "17_peso_invisivel":
        "A student sitting at a clean desk trying to study, but visually crushed by a massive transparent glass boulder on their shoulders. Struggling posture, dramatic side lighting, photorealistic, emotional close-up, dark background.",
    "18_tela_rachada":
        "Extreme close-up of an exhausted student face reflected in a cracked phone screen showing 23:47 on the clock. Dark circles under eyes, books blurred in background. The crack pattern radiates from the clock display. Macro photography style, cold blue light from screen on face, photorealistic, moody, vertical composition.",
    "19_fabrica_mental":
        "Inside a person head visualized as a steampunk factory with gears, conveyor belts and machinery. Everything is overheating, smoking, gears jamming, red warning lights flashing. Small worker figures panicking. Cutaway illustration style but photorealistic rendering, dramatic industrial lighting, warm reds and oranges.",
    "20_areia_escapando":
        "Close-up of two cupped hands trying to hold sand that is pouring through the fingers. Mixed into the sand are tiny miniature books, clocks, and calendars falling away. Black background, single dramatic spotlight from above, golden sand catching light, photorealistic macro style, emotional and visceral.",
}


def generate(key, prompt):
    outfile = os.path.join(OUTDIR, f"hook_{key}.png")
    if os.path.exists(outfile):
        return f"SKIP {key} (exists)"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
                "aspectRatio": "9:16"
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
            return f"FAIL {key}: no candidates"
        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            if "inlineData" in part:
                b64 = part["inlineData"].get("data", "")
                if b64:
                    with open(outfile, "wb") as f:
                        f.write(base64.b64decode(b64))
                    return f"OK {key} -> {outfile}"
        return f"FAIL {key}: no image data in response"
    except HTTPError as e:
        body = e.read().decode() if e.readable() else ""
        return f"ERROR {key}: HTTP {e.code} - {body[:200]}"
    except Exception as e:
        return f"ERROR {key}: {e}"


if __name__ == "__main__":
    print(f"Generating {len(PROMPTS)} images with {MODEL}")
    print(f"Output: {OUTDIR}\n")
    # 5 workers to avoid rate limits
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(generate, key, prompt): key for key, prompt in PROMPTS.items()}
        ok = fail = 0
        for future in as_completed(futures):
            result = future.result()
            print(result)
            if result.startswith("OK") or result.startswith("SKIP"):
                ok += 1
            else:
                fail += 1
    print(f"\nDone: {ok} success, {fail} failed")
