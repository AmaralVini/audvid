#!/usr/bin/env python3
"""Generate video using Veo API with polling and automatic download."""
import argparse, base64, json, os, sys, time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "veo-3.1-fast-generate-preview"


def load_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    print("ERROR: GEMINI_API_KEY not found in env or .env file", file=sys.stderr)
    sys.exit(1)


def read_file_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def mime_for(path):
    ext = os.path.splitext(path)[1].lower()
    return {"png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".mp4": "video/mp4"}.get(ext, "image/png")


def submit(api_key, model, prompt, negative_prompt, aspect_ratio, resolution, duration, person_generation, num_videos, seed, image_path, last_frame_path, video_path, ref_image_paths):
    url = f"{API_BASE}/models/{model}:predictLongRunning"
    instance = {"prompt": prompt}
    if negative_prompt:
        instance["negativePrompt"] = negative_prompt
    if image_path:
        instance["image"] = {"inlineData": {"mimeType": mime_for(image_path), "data": read_file_base64(image_path)}}
    if video_path:
        instance["video"] = {"inlineData": {"mimeType": "video/mp4", "data": read_file_base64(video_path)}}
    params = {"aspectRatio": aspect_ratio, "resolution": resolution, "durationSeconds": duration, "personGeneration": person_generation, "numberOfVideos": num_videos}
    if seed is not None:
        params["seed"] = seed
    if last_frame_path:
        params["lastFrame"] = {"inlineData": {"mimeType": mime_for(last_frame_path), "data": read_file_base64(last_frame_path)}}
    if ref_image_paths:
        params["referenceImages"] = [{"image": {"inlineData": {"mimeType": mime_for(p), "data": read_file_base64(p)}}, "referenceType": "asset"} for p in ref_image_paths]
    body = json.dumps({"instances": [instance], "parameters": params}).encode()
    req = Request(url, data=body, headers={"x-goog-api-key": api_key, "Content-Type": "application/json"})
    try:
        resp = urlopen(req, timeout=60)
        data = json.loads(resp.read())
    except HTTPError as e:
        err = e.read().decode()
        print(f"ERROR submitting: {e.code} {err}", file=sys.stderr)
        sys.exit(1)
    if "error" in data:
        print(f"ERROR: {data['error'].get('message', data['error'])}", file=sys.stderr)
        sys.exit(1)
    op_name = data["name"]
    print(f"Submitted. Operation: {op_name}")
    return op_name


def poll(api_key, op_name, interval=10, max_polls=60):
    url = f"{API_BASE}/{op_name}"
    for i in range(1, max_polls + 1):
        time.sleep(interval)
        req = Request(url, headers={"x-goog-api-key": api_key})
        resp = urlopen(req, timeout=30)
        data = json.loads(resp.read())
        done = data.get("done", False)
        print(f"  Poll {i}: done={done}")
        if done:
            if "error" in data:
                print(f"ERROR: {data['error']}", file=sys.stderr)
                sys.exit(1)
            samples = data["response"]["generateVideoResponse"]["generatedSamples"]
            return [s["video"]["uri"] for s in samples]
    print("ERROR: Timed out waiting for video generation", file=sys.stderr)
    sys.exit(1)


def download(api_key, uri, output_path):
    req = Request(uri, headers={"x-goog-api-key": api_key})
    resp = urlopen(req, timeout=120)
    with open(output_path, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Saved: {output_path} ({size_mb:.1f} MB)")


def main():
    p = argparse.ArgumentParser(description="Generate video with Veo API")
    p.add_argument("prompt", help="Video description prompt")
    p.add_argument("-o", "--output", default="output.mp4", help="Output file path (default: output.mp4)")
    p.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL})")
    p.add_argument("--negative-prompt", help="Elements to exclude from the video")
    p.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16"], help="Aspect ratio (default: 16:9)")
    p.add_argument("--resolution", default="720p", choices=["720p", "1080p", "4k"], help="Resolution (default: 720p)")
    p.add_argument("--duration", type=int, default=4, help="Duration in seconds (default: 4)")
    p.add_argument("--person-generation", default="allow_all", choices=["allow_all", "allow_adult", "dont_allow"], help="Person generation policy (default: allow_all)")
    p.add_argument("--num-videos", type=int, default=1, help="Number of videos to generate (default: 1)")
    p.add_argument("--seed", type=int, help="Seed for reproducibility (Veo 2/3 only)")
    p.add_argument("--image", help="First frame image path (image-to-video)")
    p.add_argument("--last-frame", help="Last frame image path (interpolation, Veo 3.1 only)")
    p.add_argument("--video", help="Previous video path for extension (Veo 3.1 only)")
    p.add_argument("--ref-images", nargs="+", help="Reference image paths for subject consistency (up to 3, Veo 3.1 only)")
    p.add_argument("--poll-interval", type=int, default=10, help="Polling interval in seconds (default: 10)")
    args = p.parse_args()

    api_key = load_api_key()
    print(f"Model: {args.model}")
    print(f"Resolution: {args.resolution} | Duration: {args.duration}s | Aspect: {args.aspect_ratio}")
    print(f"Prompt: {args.prompt[:100]}{'...' if len(args.prompt) > 100 else ''}")

    op_name = submit(api_key, args.model, args.prompt, args.negative_prompt, args.aspect_ratio, args.resolution, args.duration, args.person_generation, args.num_videos, args.seed, args.image, args.last_frame, args.video, args.ref_images)

    print("Waiting for generation...")
    uris = poll(api_key, op_name, interval=args.poll_interval)

    for i, uri in enumerate(uris):
        if len(uris) == 1:
            out = args.output
        else:
            base, ext = os.path.splitext(args.output)
            out = f"{base}_{i+1}{ext}"
        download(api_key, uri, out)

    print("Done!")


if __name__ == "__main__":
    main()
