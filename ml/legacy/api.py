from flask import Flask, request, jsonify
from flask_cors import CORS

import base64
import re
from io import BytesIO

import numpy as np
import cv2
from PIL import Image

from Detector import analyze_image

app = Flask(__name__)
CORS(app)


def decode_data_url_to_bgr(data_url: str) -> np.ndarray:
    """Decode base64 data URL (PNG/JPEG) into OpenCV BGR image."""
    b64 = re.sub(r"^data:image\/[a-zA-Z0-9.+-]+;base64,", "", data_url)
    raw = base64.b64decode(b64)
    pil = Image.open(BytesIO(raw)).convert("RGB")  # handles RGBA PNG too
    rgb = np.array(pil)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def decode_file_to_bgr(file_storage) -> np.ndarray:
    """Decode uploaded file (PNG/JPEG) into OpenCV BGR image."""
    raw = file_storage.read()
    pil = Image.open(BytesIO(raw)).convert("RGB")
    rgb = np.array(pil)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def bgr_to_jpeg_dataurl(img_bgr: np.ndarray, quality: int = 90) -> str | None:
    """Encode OpenCV BGR image to data:image/jpeg;base64,..."""
    if img_bgr is None:
        return None
    ok, buf = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        return None
    b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
    return "data:image/jpeg;base64," + b64


@app.route("/analyze", methods=["POST"])
def analyze():
    # --- Accept either multipart file upload or JSON dataURL ---
    if "image" in request.files:
        img_bgr = decode_file_to_bgr(request.files["image"])
    else:
        data = request.get_json(silent=True) or {}
        if "image" not in data:
            return jsonify({"error": "No image provided. Send multipart field 'image' or JSON {'image': dataURL}."}), 400
        img_bgr = decode_data_url_to_bgr(data["image"])

    # --- Run detector ---
    det_report = analyze_image(img_bgr)

    # Extract images dictionary from detector output
    images = det_report.get("_images", {}) or {}

    # --- Build UI response ---
    overall = det_report.get("overall", "")
    overall_ui = "All present and OK" if overall == "All present" else overall

    # Toolbox annotated image
    annotated_toolbox = bgr_to_jpeg_dataurl(images.get("toolbox"))

    # Tool name -> image key mapping (fixes Hook Sinskey Tip mismatch)
    name_to_image_key = {
        "Chop Phaco": "Chop Phaco",
        "Forceps Macpherson": "Forceps Macpherson",
        "Forceps Utrata": "Forceps Utrata",
        "Hook Sinskey Tip": "Hook Sinskey",   # <-- key fix
        "Hook Sinskey": "Hook Sinskey",
    }

    tools_out = []
    for t in det_report.get("tools", []):
        name = t.get("name", "")
        image_key = name_to_image_key.get(name, name)  # default to same name
        tool_img_bgr = images.get(image_key)

        tools_out.append({
            "name": name,
            "count": int(t.get("count", 0)),
            "status": t.get("status", ""),
            "image": bgr_to_jpeg_dataurl(tool_img_bgr)
        })

    resp = {
        "overall": overall_ui,
        "annotated_image": annotated_toolbox,
        "tools": tools_out
    }

    return jsonify(resp)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
