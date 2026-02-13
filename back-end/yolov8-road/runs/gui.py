import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np

from pred import pred

# 设置最大宽度和高度
MAX_WIDTH = 600
MAX_HEIGHT = 600

# 调整图像大小以适应最大宽度和高度
def resize_image(img, max_width, max_height):
    # 获取原始图片的宽度和高度
    width, height = img.size
    
    # 计算宽高比
    aspect_ratio = width / height
    
    if aspect_ratio > 1:  # 宽度大于高度
        # 按照宽度缩放
        new_width = min(width, max_width)
        new_height = int(new_width / aspect_ratio)
    else:  # 高度大于或等于宽度
        # 按照高度缩放
        new_height = min(height, max_height)
        new_width = int(new_height * aspect_ratio)
    
    # 调整图像大小
    img.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
    return img

# 加载图像文件并进行处理
def load_image():
    # 打开文件选择对话框
    file_path = filedialog.askopenfilename()
    if file_path:
        # 读取并解码图像文件
        img_ = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)
        process_frame(img_, stream=False)

# 加载视频文件并进行处理
def load_video():
    global cap, running
    # 打开文件选择对话框
    file_path = filedialog.askopenfilename()
    if file_path:
        # 打开视频文件
        cap = cv2.VideoCapture(file_path)
        running = True
        update_frame()

# 启动摄像头进行实时视频处理
def start_camera():
    global cap, running
    # 打开默认摄像头
    cap = cv2.VideoCapture(0)
    running = True
    update_frame()

# 停止摄像头
def stop_camera():
    global running
    running = False
    if cap:
        cap.release()

# 更新视频帧
def update_frame():
    global cap, running
    if running:
        ret, frame = cap.read()
        if ret:
            process_frame(frame, stream=True)
            # 每10毫秒更新一次帧
            root.after(10, update_frame)

# 处理图像帧
def process_frame(file_path, stream=False):
    # 进行预测，获取原始图像和处理后的图像
    orig, frame = pred(file_path, stream=stream)
    orig = cv2.cvtColor(orig, cv2.COLOR_BGR2RGB)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    orig_img = Image.fromarray(orig)
    image = Image.fromarray(frame)

    # 调整图像大小以适应最大宽度和高度
    orig_img = resize_image(orig_img, MAX_WIDTH, MAX_HEIGHT)
    orig_img = ImageTk.PhotoImage(orig_img)

    image = resize_image(image, MAX_WIDTH, MAX_HEIGHT)
    image = ImageTk.PhotoImage(image)

    # 更新原始图像标签
    orig_label.configure(
        image=orig_img, width=orig_img.width(), height=orig_img.height(), text=""
    )
    orig_label.image = orig_img
    orig_label.pack(side=tk.LEFT, expand=True)
    
    # 更新处理后图像标签
    pred_label.configure(
        image=image, width=image.width(), height=image.height(), text=""
    )
    pred_label.image = image
    pred_label.pack(side=tk.RIGHT, expand=True)

# 创建主窗口
root = tk.Tk()
root.title("yolov8火焰烟雾检测")

# 创建按钮框架
btn_frame = tk.Frame(root)
btn_frame.pack(side=tk.TOP, fill=tk.X)

# 创建加载图片按钮
load_img_btn = tk.Button(btn_frame, text="加载图片", command=load_image)
load_img_btn.pack(side=tk.LEFT, padx=10, pady=5)

# 创建加载视频按钮
load_video_btn = tk.Button(btn_frame, text="加载视频", command=load_video)
load_video_btn.pack(side=tk.LEFT, padx=10, pady=5)

# 创建启动摄像头按钮
start_cam_btn = tk.Button(btn_frame, text="启动摄像头", command=start_camera)
start_cam_btn.pack(side=tk.LEFT, padx=10, pady=5)

# 创建停止摄像头按钮
stop_cam_btn = tk.Button(btn_frame, text="停止摄像头", command=stop_camera)
stop_cam_btn.pack(side=tk.LEFT, padx=10, pady=5)

# 创建显示图像框架
show_fram = tk.Frame(root)
show_fram.pack(side=tk.BOTTOM)

# 创建一个固定大小的标签来显示原始图像，并在初始状态下显示说明文字
orig_label = tk.Label(
    show_fram,
    text="请加载图片或视频，或启动摄像头以开始检测火焰和烟雾。",
    justify="center",
    anchor="center",
)
orig_label.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=10)

# 创建一个固定大小的标签来显示处理后的图像，并在初始状态下显示说明文字
pred_label = tk.Label(show_fram, text="预测结果", justify="center", anchor="center")
pred_label.pack(side=tk.RIGHT, fill=tk.X, padx=10, pady=10)

# 初始化全局变量
cap = None
running = False

# 进入主循环
root.mainloop()
