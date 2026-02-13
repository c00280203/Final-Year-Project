from ultralytics import YOLO
import os


import zipfile
with zipfile.ZipFile(f"./fire-and-smoke-detection.zip","r") as zip_ref:
    zip_ref.extractall("data")

# Load the model.
model = YOLO(f'./yolov8n.pt')

# Training.
results = model.train(
   data=os.path.abspath(f"./data/fire-and-smoke-detection/data.yaml"),
   imgsz=640,
   epochs=300,
   batch=32,
   name='yolov8n_v8_300e'
)

val_result = model.val()