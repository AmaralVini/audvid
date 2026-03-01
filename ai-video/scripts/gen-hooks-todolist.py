#!/usr/bin/env python3
"""Generate 20 hook images in parallel using Imagen 4 Fast."""
import json, base64, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen

API_KEY = os.environ["GEMINI_API_KEY"]
MODEL = "imagen-4.0-fast-generate-001"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:predict"
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "content", "hooks-todolist")
os.makedirs(OUTDIR, exist_ok=True)

PROMPTS = {
    "01": "Giant paper to-do list engulfed in slow-motion flames, glowing embers floating upward like fireflies, silhouetted person standing behind with relaxed arms, dark cinematic background",
    "02": "Close-up of a hand writing on an impossibly long to-do list that unrolls off the desk, falls to the floor, continues out the window and down the building exterior, dramatic perspective",
    "03": "Office worker at a desk being buried under an avalanche of colorful sticky notes falling from the ceiling like snow, overwhelmed expression, dramatic overhead lighting",
    "04": "Person crumpling a to-do list into a paper ball mid-throw toward a trash can, the ball exploding into colorful confetti, triumphant victory pose, dynamic action shot",
    "05": "To-do list with 50 items crossed out by a single bold red diagonal line, tropical beach visible through the window behind, split focus between list and paradise",
    "06": "Smartphone screen glowing with a to-do list app, dark paper tentacles emerging from the screen reaching toward a calm person closing the phone, horror-comedy style",
    "07": "Frustrated person flipping a to-do list paper over, the paper has impossibly dozens of visible layers each with more lists, infinite layers illusion, dramatic expression",
    "08": "Person in business suit in a dark room ceremonially holding a burning to-do list like an ancient scroll, fire illuminating their peaceful face, rising embers, chiaroscuro lighting",
    "09": "Whiteboard filled with checkboxes being unchecked in a cascading domino wave, checks disappearing one by one, person standing beside shrugging nonchalantly",
    "10": "Surrealist Dali-inspired scene with melting clocks draped over a desk covered in to-do lists, papers warping, person calmly drinking coffee amidst the chaos, dreamlike painterly style",
    "11": "Cute humanoid robot desperately trying to hold hundreds of post-it notes swirling around it like a tornado, papers flying everywhere, robot looking overwhelmed with glowing red eyes",
    "12": "Courtroom scene with a crumpled to-do list paper sitting in the defendant chair, stern judge pointing gavel at it, jury of office workers applauding, dramatic lighting",
    "13": "Dark comedy funeral with a small paper coffin with checkboxes printed on it being lowered into a grave, mourners smiling relieved instead of sad, tossing flowers, golden hour",
    "14": "Horror movie chase on a dark empty street at night, person running scared looking back, giant ghostly floating to-do list chasing them, motion blur, dramatic street lighting",
    "15": "Rocket on launch pad lifting off with dramatic smoke and fire, visible through the cockpit window is a to-do list paper strapped to the seat, epic wide angle",
    "16": "Magician hands pulling a silk cloth away from a crumpled to-do list, revealing it transformed into a golden airplane ticket, sparkles and magic dust, stage lighting",
    "17": "Person peacefully floating inside a giant aquarium, papers and sticky notes drifting around them like jellyfish, soft blue-green underwater lighting, serene closed eyes",
    "18": "Person at a vintage typewriter ripping an endless to-do list printout and folding paper airplanes, hundreds of paper airplanes visible through the window scattered on the ground below",
    "19": "Office desk covered in to-do lists being overtaken by lush green plants, vines and flowers growing through the papers, nature reclaiming the workspace, soft natural light",
    "20": "Person writing on a to-do list that is breaking apart into pixels and digital glitches, reality fragmenting, a beach paradise visible through the glitched cracks in reality",
}


def generate(num, prompt):
    outfile = os.path.join(OUTDIR, f"hook_{num}.png")
    if os.path.exists(outfile):
        return f"SKIP {num} (exists)"
    body = json.dumps({
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "16:9", "personGeneration": "allow_all"}
    }).encode()
    req = Request(ENDPOINT, data=body, headers={
        "x-goog-api-key": API_KEY,
        "Content-Type": "application/json",
    })
    try:
        resp = urlopen(req, timeout=60)
        data = json.loads(resp.read())
        preds = data.get("predictions", [])
        if not preds:
            return f"FAIL {num}: no predictions"
        b64 = preds[0].get("bytesBase64Encoded", "")
        if not b64:
            return f"FAIL {num}: no image data"
        with open(outfile, "wb") as f:
            f.write(base64.b64decode(b64))
        return f"OK {num} -> {outfile}"
    except Exception as e:
        return f"ERROR {num}: {e}"


with ThreadPoolExecutor(max_workers=10) as pool:
    futures = {pool.submit(generate, num, prompt): num for num, prompt in PROMPTS.items()}
    for future in as_completed(futures):
        print(future.result())
