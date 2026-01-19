import tensorflow as tf
import numpy as np
from PIL import Image

# Load your models once
CLASS_MODEL_PATH = "potholes-garbage-classifier.h5"
SEG_MODEL_PATH = "segmentation_model.h5"

class_model = tf.keras.models.load_model(CLASS_MODEL_PATH)
seg_model = tf.keras.models.load_model(SEG_MODEL_PATH)

# Preprocessing functions
def preprocess_class(image: Image.Image):
    # Resize and normalize as your model expects
    img = image.resize((224, 224))
    arr = np.array(img) / 255.0
    if arr.ndim == 2:  # grayscale → RGB
        arr = np.stack([arr]*3, axis=-1)
    arr = np.expand_dims(arr, 0)  # batch dimension
    return arr

def preprocess_seg(image: Image.Image):
    img = image.resize((256, 256)) 
    arr = np.array(img) / 255.0
    if arr.ndim == 2:  # grayscale → RGB
        arr = np.stack([arr]*3, axis=-1)
    arr = np.expand_dims(arr, 0)  # batch dimension
    return arr

def run_inference(image: Image.Image):
    """
    image: PIL Image
    returns:
        segmented_image: PIL Image
        confidence_score: float (from classification model)
    """

    # 1️⃣ Classification
    class_input = preprocess_class(image)
    class_pred = class_model.predict(class_input)
    confidence_score = float(np.max(class_pred))
    predicted_class = int(np.argmax(class_pred))

    # 2️⃣ Segmentation
    seg_input = preprocess_seg(image)
    seg_pred = seg_model.predict(seg_input)  # shape = (1,H,W,num_classes) or (1,H,W,1)
    
    # Convert seg_pred to mask
    seg_mask = np.argmax(seg_pred[0], axis=-1).astype(np.uint8) * 255  # shape (H,W)
    segmented_image = Image.fromarray(seg_mask)

    return segmented_image, confidence_score
