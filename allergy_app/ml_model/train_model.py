import os
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau

# --- Configuration ---
NUM_CLASSES = 101  # Food-101 has 101 classes
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 50  # More epochs due to larger dataset
DATA_DIR = 'data/food-101'  # Should contain images/, meta/
MODEL_PATH = 'allergy_app/ml_model/food_model_full.h5'

os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

# --- Load class names from Food-101 meta/classes.txt ---
classes_file = os.path.join(DATA_DIR, 'meta', 'classes.txt')
if not os.path.exists(classes_file):
    raise FileNotFoundError(f"Classes file not found: {classes_file}")

with open(classes_file, 'r') as f:
    class_names = [line.strip() for line in f.readlines()]
print(f"Loaded {len(class_names)} classes.")

# --- Data Preprocessing ---
train_datagen = ImageDataGenerator(
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True,
    zoom_range=0.2,
    shear_range=0.1,
    validation_split=0.2,  # Train/validation split from entire dataset
    preprocessing_function=tf.keras.applications.mobilenet_v2.preprocess_input
)

# Use train_dir=images/ and select subsets via train/val split
train_generator = train_datagen.flow_from_directory(
    os.path.join(DATA_DIR, 'images'),
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training',
    classes=class_names,  # Preserve class order
    seed=1337
)

validation_generator = train_datagen.flow_from_directory(
    os.path.join(DATA_DIR, 'images'),
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    classes=class_names,
    seed=1337
)

# --- Transfer Learning: Load MobileNetV2 ---
base_model = MobileNetV2(
    input_shape=(IMG_SIZE[0], IMG_SIZE[1], 3),
    include_top=False,
    weights='imagenet'
)
base_model.trainable = False

# --- Add Top Layers ---
x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dropout(0.5)(x)  # Slightly higher dropout for larger data
predictions = Dense(NUM_CLASSES, activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=predictions)

# --- Compile ---
model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=[
    'accuracy',
    tf.keras.metrics.TopKCategoricalAccuracy(k=5, name='top_5_accuracy')]
  # Track top-5 for Food-101
)

# --- Callbacks ---
callbacks = [
    EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True
    ),
    ModelCheckpoint(
        filepath=MODEL_PATH,
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    ),
    ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.2,
        patience=3,
        min_lr=1e-7,
        verbose=1
    )
]

# --- Train frozen base ---
print("🔹 Training top layers...")
history = model.fit(
    train_generator,
    epochs=EPOCHS,
    validation_data=validation_generator,
    callbacks=callbacks,
    verbose=1
)

# --- Fine-tuning ---
print("\n🔹 Starting fine-tuning...")
base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
    loss='categorical_crossentropy',
    metrics=[
    'accuracy',
    tf.keras.metrics.TopKCategoricalAccuracy(k=5, name='top_5_accuracy')]

)

history_fine = model.fit(
    train_generator,
    epochs=15,
    validation_data=validation_generator,
    callbacks=callbacks,
    verbose=1
)

# --- Save model ---
model.save(MODEL_PATH)
print(f"\n✅ Final model saved at: {MODEL_PATH}")

# Save class names for inference
import json
classes_path = os.path.join(os.path.dirname(MODEL_PATH), 'food_classes.json')
with open(classes_path, 'w') as f:
    json.dump(class_names, f)
print(f"✅ Class list saved for inference at: {classes_path}")
