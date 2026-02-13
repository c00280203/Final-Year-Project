import os
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_file
from ultralytics import YOLO
import io
from PIL import Image
from flask_cors import CORS
import pillow_heif

app = Flask(__name__)
CORS(app)

pillow_heif.register_heif_opener()

# ---------- 加载你的 YOLO 模型 ----------
model = YOLO("./runs/detect/yolov8n_v8_200e/weights/best.pt")
classNames = ['cracks', 'pothole']

# ---------- 复用你原有的绘图函数 ----------
font = cv2.FONT_HERSHEY_DUPLEX

def add_text_with_background(image, text, position, font_face, font_scale,
                             text_color, bg_color, thickness=1, padding=5):
    (text_width, text_height), baseline = cv2.getTextSize(
        text, font_face, font_scale, thickness)
    box_width = text_width + 2 * padding
    box_height = text_height + 2 * padding + baseline
    x, y = position
    x = max(0, min(x, image.shape[1] - box_width))
    y = max(box_height, min(y, image.shape[0]))
    cv2.rectangle(image, (x, y - box_height), (x + box_width, y), bg_color, -1)
    text_position = (x + padding, y - padding - baseline)
    cv2.putText(image, text, text_position, font_face, font_scale, text_color, thickness)

def predict(img_array):
    """输入 numpy 数组 (BGR), 返回检测后的图像数组"""
    img = img_array.copy()
    img_height, img_width = img.shape[:2]
    results = model(img, stream=False)

    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            w, h = x2 - x1, y2 - y1
            conf = round(float(box.conf[0]), 2)
            cls = int(box.cls[0])
            name = classNames[cls]

            thick = 1 if w < 210 else 2
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)

            # 根据图像尺寸动态调整字体大小（可简化）
            if img_height < 600 or img_width < 600:
                font_scale = 0.5
            else:
                font_scale = 0.7

            add_text_with_background(
                img, f"{name} {conf}", (x1, y1),
                font, font_scale, (255, 255, 255), (0, 0, 255),
                thick, 5
            )
    return img

# ---------- Test --------
@app.route('/ping')
def ping():
    return 'pong'

# ---------- 定义 API 路由 ----------
@app.route('/detect', methods=['POST'])
def detect():
    print("收到检测请求")
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    # 读取原始字节
    img_bytes = file.read()
    if len(img_bytes) == 0:
        return jsonify({'error': 'Empty file content'}), 400

    # ---------- 图像解码（万能方案）----------
    try:
        # 1. 用 PIL 打开（自动识别格式）
        pil_image = Image.open(io.BytesIO(img_bytes))

        # 2. 统一转换为 RGB 模式（避免后续 OpenCV 处理异常）
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # 3. PIL Image → numpy array (RGB)
        img = np.array(pil_image)

    except Exception as e:
        print(f"PIL 解码失败: {e}")
        # 回退方案：直接使用 OpenCV 的 imdecode
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            # 此时图片彻底无法解析
            return jsonify({'error': 'Invalid image file - cannot decode with both PIL and OpenCV'}), 400
    # ---------- 执行 YOLO 检测 ----------
    try:
        result_img = predict(img)
    except Exception as e:
        print(f"YOLO 检测失败: {e}")
        return jsonify({'error': f'Detection failed: {str(e)}'}), 500

    # ---------- 返回处理后的图片 ----------
    _, encoded_img = cv2.imencode('.png', result_img)
    return send_file(
        io.BytesIO(encoded_img.tobytes()),
        mimetype='image/png',
        as_attachment=False
    )

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True)