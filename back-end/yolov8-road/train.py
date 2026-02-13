from ultralytics import YOLO
import os

"""
import zipfile
with zipfile.ZipFile(f"./road_defect_detection_UNI.v14-yolo.yolov8.zip","r") as zip_ref:
    zip_ref.extractall("data")
"""

# Load the model.
model = YOLO(f'./yolov8n.pt')

# Training.
results = model.train(
   data=os.path.abspath(f"./data/data.yaml"),
   imgsz=416,
   epochs=300,
   batch=32,
   name='yolov8n_v8_300e'
)

val_result = model.val()
