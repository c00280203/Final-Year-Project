import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import os
import io  # 关键：必须导入 io

from pred import pred
from location import get_gps_coordinates, open_in_google_maps, open_in_apple_maps

# 设置最大显示尺寸
MAX_WIDTH = 600
MAX_HEIGHT = 600

current_image_path = None
current_gps = None

def resize_image(img, max_width, max_height):
    """调整 PIL Image 大小，保持宽高比"""
    width, height = img.size
    aspect_ratio = width / height
    if aspect_ratio > 1:
        new_width = min(width, max_width)
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = min(height, max_height)
        new_width = int(new_height * aspect_ratio)
    img.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
    return img

def load_image():
    global current_image_path, current_gps
    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    try:
        current_image_path = file_path

        # 读取文件字节
        with open(file_path, 'rb') as f:
            img_bytes = f.read()
        if len(img_bytes) == 0:
            print("❌ 文件为空")
            return

        file_ext = file_path.lower().split('.')[-1]
        img = None

        # 处理 HEIC/HEIF 格式
        if file_ext in ['heic', 'heif']:
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
                pil_img = Image.open(io.BytesIO(img_bytes))
                # 转换为 RGB（确保）
                if pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                print("✅ HEIC 解码成功")
            except Exception as e:
                print(f"❌ HEIC 解码失败: {e}")
                # HEIC 解码失败后不再尝试其他方法，因为 OpenCV 不支持 HEIC
                return
        else:
            # 非 HEIC：先用 OpenCV 解码
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                # OpenCV 失败，尝试用 PIL
                try:
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    if pil_img.mode != 'RGB':
                        pil_img = pil_img.convert('RGB')
                    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    print("✅ PIL 解码成功（OpenCV 后备）")
                except Exception as e:
                    print(f"❌ PIL 解码也失败: {e}")
                    return

        if img is None:
            print("❌ 无法解码图片")
            return

        # 进行缺陷检测
        process_frame(img)

        # 提取 GPS 坐标
        try:
            gps = get_gps_coordinates(file_path)
            if gps:
                current_gps = gps
                location_btn.config(state=tk.NORMAL)
                print(f"✅ GPS 坐标: {gps[0]:.6f}, {gps[1]:.6f}")
            else:
                current_gps = None
                location_btn.config(state=tk.DISABLED)
                print("ℹ️ 图片无 GPS 信息")
        except Exception as e:
            print(f"⚠️ GPS 提取失败: {e}")
            current_gps = None
            location_btn.config(state=tk.DISABLED)

    except Exception as e:
        print(f"❌ 加载图片时出错: {e}")
        import traceback
        traceback.print_exc()

def process_frame(img_bgr):
    """调用 pred 进行检测，并更新界面"""
    try:
        orig, result = pred(img_bgr, stream=False)
    except Exception as e:
        print(f"❌ 检测失败: {e}")
        return

    if orig is None or result is None:
        print("❌ 检测返回空结果")
        return

    # 转换为 RGB 用于显示
    orig_rgb = cv2.cvtColor(orig, cv2.COLOR_BGR2RGB)
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)

    orig_pil = Image.fromarray(orig_rgb)
    result_pil = Image.fromarray(result_rgb)

    orig_pil = resize_image(orig_pil, MAX_WIDTH, MAX_HEIGHT)
    result_pil = resize_image(result_pil, MAX_WIDTH, MAX_HEIGHT)

    orig_tk = ImageTk.PhotoImage(orig_pil)
    result_tk = ImageTk.PhotoImage(result_pil)

    # 更新左侧标签
    orig_label.configure(image=orig_tk, text="")
    orig_label.image = orig_tk

    # 更新右侧标签
    pred_label.configure(image=result_tk, text="")
    pred_label.image = result_tk

def go_to_location():
    if current_gps:
        lat, lon = current_gps
        open_in_google_maps(lat, lon)

# 创建主窗口
root = tk.Tk()
root.title("IntelliRoad Detect")

# 按钮框架
btn_frame = tk.Frame(root)
btn_frame.pack(side=tk.TOP, fill=tk.X)

load_img_btn = tk.Button(btn_frame, text="Upload image", command=load_image)
load_img_btn.pack(side=tk.LEFT, padx=10, pady=5)

location_btn = tk.Button(btn_frame, text="Go to location", command=go_to_location, state=tk.DISABLED)
location_btn.pack(side=tk.LEFT, padx=10, pady=5)

exit_btn = tk.Button(btn_frame, text="Exit", command=root.quit)
exit_btn.pack(side=tk.LEFT, padx=10, pady=5)

# 显示区域
show_frame = tk.Frame(root)
show_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

orig_label = tk.Label(show_frame, text="Please select image to detect", justify="center", anchor="center", bg="#f0f0f0")
orig_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

pred_label = tk.Label(show_frame, text="Results", justify="center", anchor="center", bg="#f0f0f0")
pred_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

root.mainloop()