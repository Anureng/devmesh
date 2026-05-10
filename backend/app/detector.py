import logging
import mediapipe as mp
from PIL import Image
from app.config import settings

logger = logging.getLogger(__name__)

_detector = mp.solutions.face_detection.FaceDetection(
    model_selection=0,
    min_detection_confidence=settings.FACE_CONFIDENCE_THRESHOLD,
)

def detect_face(image: Image.Image) -> dict | None:
    """
    Takes a PIL Image, returns ROI dict in pixel coords or None.
    Uses mediapipe — no OpenCV.
    """
    try:
        import numpy as np
        rgb = np.array(image.convert("RGB"))
        results = _detector.process(rgb)

        if not results.detections:
            return None

        detection = results.detections[0]  # only one face assumed
        bbox = detection.location_data.relative_bounding_box
        w, h = image.size

        x = max(0, int(bbox.xmin * w))
        y = max(0, int(bbox.ymin * h))
        width = int(bbox.width * w)
        height = int(bbox.height * h)
        confidence = float(detection.score[0])

        return {"x": x, "y": y, "width": width, "height": height, "confidence": confidence}

    except Exception as e:
        logger.error(f"Detection error: {e}")
        return None