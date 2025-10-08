# allergy_app/ml_model/load_model.py
import tensorflow as tf
import numpy as np
from PIL import Image
import os
import json

# Load model
model_path = os.path.join(os.path.dirname(__file__), 'food_model_full.h5')
model = tf.keras.models.load_model(model_path)

# Load class names
classes_path = os.path.join(os.path.dirname(__file__), 'food_classes.json')
with open(classes_path, 'r') as f:
    food_classes = json.load(f)
print(f"Loaded {len(food_classes)} food classes.")

def predict_food(image_path):
    """Predict food class and confidence from image path."""
    try:
        # Load and preprocess image
        img = Image.open(image_path).convert('RGB')  # Ensure 3-channel
        img = img.resize((224, 224))
        img_array = np.array(img) / 255.0  # Normalize to [0,1]
        img_array = np.expand_dims(img_array, axis=0)  # Add batch dim

        # Predict
        predictions = model.predict(img_array, verbose=0)
        class_idx = np.argmax(predictions, axis=1)[0]
        confidence = float(predictions[0][class_idx])

        # Convert snake_case to Title Case: 'apple_pie' → 'Apple Pie'
        class_name = food_classes[class_idx]
        display_name = ' '.join(word.capitalize() for word in class_name.split('_'))

        return display_name, confidence
    except Exception as e:
        print(f"Prediction error: {e}")
        return "Unknown", 0.0
