from flask import Blueprint, request, jsonify
from extension import db
from models import IssueReport
from utils.image_utils import base64_to_image, image_to_base64
from utils.model_runner import run_inference
import os
import time
from auth import token_required

inference_bp = Blueprint("inference", __name__, url_prefix="/api/infer")

UPLOAD_FOLDER = "uploaded_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@token_required
@inference_bp.route("", methods=["POST"])
def infer_image():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    try:
        username = data["username"]
        location = data["location"]
        image_base64 = data["image"]

        #  Convert base64 → image
        image = base64_to_image(image_base64)

        #  Run AI inference
        segmented_img, confidence = run_inference(image)

        #  Convert segmented image → base64 (for DB + frontend)
        segmented_base64 = image_to_base64(segmented_img)

        # Save segmented image locally
        timestamp = int(time.time())
        filename = f"{username}_{timestamp}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        segmented_img.save(filepath)

        # Store in DB
        report = IssueReport(
            username=username,
            location=location,
            segmented_image=segmented_base64,
            confidence_score=confidence,
            is_resolved=False
        )
        db.session.add(report)
        db.session.commit()

        # Return JSON
        return jsonify({
            "message": "Inference successful",
            "segmented_image": segmented_base64,
            "confidence_score": confidence,
            "report_id": report.id,
            "saved_file": filepath
        }), 200

    except KeyError as e:
        return jsonify({"error": f"Missing field {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
