import io
import shutil
import zipfile
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, send_file
import cv2
import numpy as np

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
SOURCE_DIR = BASE_DIR / "source_videos"
FRAMES_DIR = BASE_DIR / "frames"
EXPORT_DIR = BASE_DIR / "export"
OUTPUT_DIR = BASE_DIR / "output"

for d in [SOURCE_DIR, FRAMES_DIR, EXPORT_DIR, OUTPUT_DIR]:
    d.mkdir(exist_ok=True)


@app.route("/")
def index():
    return send_file(BASE_DIR / "index.html")


@app.route("/api/videos")
def list_videos():
    videos = []
    for ext in ("*.mp4", "*.avi", "*.mov", "*.webm"):
        for p in SOURCE_DIR.glob(ext):
            cap = cv2.VideoCapture(str(p))
            videos.append({
                "name": p.stem,
                "filename": p.name,
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            })
            cap.release()
    return jsonify(videos)


@app.route("/api/extract-frames", methods=["POST"])
def extract_frames():
    data = request.json
    video_name = data["video"]
    every_n = data.get("every_n", 1)

    video_path = SOURCE_DIR / video_name
    if not video_path.exists():
        return jsonify({"error": "Video not found"}), 404

    stem = video_path.stem
    out_dir = FRAMES_DIR / stem
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in out_dir.glob("*.png"):
        f.unlink()

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % every_n == 0:
            fname = f"frame_{idx:04d}.png"
            cv2.imwrite(str(out_dir / fname), frame)
            frames.append({
                "index": idx,
                "filename": fname,
                "time": round(idx / fps, 3) if fps else 0,
            })
        idx += 1

    cap.release()
    return jsonify({"video": stem, "total_frames": idx, "saved": len(frames), "frames": frames})


@app.route("/api/export-frames", methods=["POST"])
def export_frames():
    """Export selected frames as a zip with proper sprite naming."""
    data = request.json
    video_stem = data["video"]
    frame_files = data["frames"]
    char_name = data.get("char_name", "player1")
    direction = data.get("direction", "front")
    action = data.get("action", "idle")

    src_dir = FRAMES_DIR / video_stem
    prefix = f"{char_name}_{direction}_{action}"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, fname in enumerate(frame_files):
            src_path = src_dir / fname
            if not src_path.exists():
                continue
            sprite_name = f"{prefix}_{i + 1:02d}.png"
            zf.write(src_path, sprite_name)

    buf.seek(0)
    return send_file(buf, mimetype="application/zip",
                     as_attachment=True, download_name=f"{prefix}.zip")


@app.route("/api/import-frames", methods=["POST"])
def import_frames():
    """Import background-removed frames, save to output with original naming."""
    char_name = request.form.get("char_name", "player1")
    direction = request.form.get("direction", "front")
    action = request.form.get("action", "idle")

    prefix = f"{char_name}_{direction}_{action}"
    dst_dir = OUTPUT_DIR / prefix
    dst_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    files = request.files.getlist("files")
    for f in files:
        fname = f.filename
        dst_path = dst_dir / fname
        f.save(dst_path)
        saved.append(fname)

    saved.sort()
    return jsonify({"folder": prefix, "saved": len(saved), "files": saved})


@app.route("/frames/<path:filepath>")
def serve_frame(filepath):
    return send_from_directory(FRAMES_DIR, filepath)


@app.route("/output/<path:filepath>")
def serve_output(filepath):
    return send_from_directory(OUTPUT_DIR, filepath)


@app.route("/api/output-folders")
def list_output_folders():
    folders = []
    for d in sorted(OUTPUT_DIR.iterdir()):
        if not d.is_dir() or d.name.endswith("_normalized"):
            continue
        pngs = sorted(f.name for f in d.glob("*.png"))
        if not pngs:
            continue
        folders.append({"name": d.name, "files": pngs, "count": len(pngs)})
    return jsonify(folders)


@app.route("/api/apply-normalize", methods=["POST"])
def apply_normalize():
    """Scale sprites per-folder and place on a unified canvas with offset."""
    data = request.json
    canvas_size = data["canvas_size"]
    folders = data["folders"]

    results = {}
    for item in folders:
        folder_name = item["folder"]
        scale = item["scale"]
        offset_x = item.get("offset_x", 0)
        offset_y = item.get("offset_y", 0)
        src_dir = OUTPUT_DIR / folder_name
        if not src_dir.is_dir():
            continue

        dst_dir = OUTPUT_DIR / (folder_name + "_normalized")
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        dst_dir.mkdir(parents=True)

        processed = []
        for png in sorted(src_dir.glob("*.png")):
            img = cv2.imread(str(png), cv2.IMREAD_UNCHANGED)
            if img is None:
                continue

            h, w = img.shape[:2]
            new_w = int(w * scale)
            new_h = int(h * scale)
            if new_w < 1 or new_h < 1:
                continue
            scaled = cv2.resize(img, (new_w, new_h),
                                interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LANCZOS4)

            canvas = np.zeros((canvas_size, canvas_size, 4), dtype=np.uint8)
            cx = (canvas_size - new_w) // 2 + offset_x
            cy = (canvas_size - new_h) // 2 + offset_y
            x1 = max(0, cx)
            y1 = max(0, cy)
            x2 = min(canvas_size, cx + new_w)
            y2 = min(canvas_size, cy + new_h)
            sx1 = max(0, -cx)
            sy1 = max(0, -cy)
            sx2 = sx1 + (x2 - x1)
            sy2 = sy1 + (y2 - y1)
            canvas[y1:y2, x1:x2] = scaled[sy1:sy2, sx1:sx2]

            cv2.imwrite(str(dst_dir / png.name), canvas)
            processed.append(png.name)

        results[folder_name] = {
            "output_folder": folder_name + "_normalized",
            "processed": len(processed),
            "files": processed,
        }

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
