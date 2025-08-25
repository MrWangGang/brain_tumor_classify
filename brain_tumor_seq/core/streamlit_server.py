import streamlit as st
from ultralytics import YOLO, SAM
import cv2
import numpy as np
import tempfile
import torch

# 顶部标题
st.markdown("<h3>YOLO + SAM 实时图像分割演示</h3>", unsafe_allow_html=True)

# 上传图片
uploaded_file = st.file_uploader("上传一张图片", type=["jpg", "jpeg", "png"])

# 缓存模型加载
@st.cache_resource
def load_models():
    yolo_model = YOLO('./model/best.pt')
    sam_model = SAM('./model/sam2_l.pt')
    return yolo_model, sam_model

if uploaded_file:
    # 保存上传图像
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        temp_file.write(uploaded_file.read())
        image_path = temp_file.name

    image = cv2.imread(image_path)
    orig_image = image.copy()

    # 图像展示区域统一放在 container 中，避免高度错位
    with st.container():
        col1, col2 = st.columns(2)

        # 左侧显示原图
        with col1:
            st.markdown("#### 原始图像")
            st.image(orig_image[:, :, ::-1], caption="上传的原始图片", use_container_width=True)

        # 右侧：显示 spinner + 推理 + 显示处理图
        with col2:
            st.markdown("#### 处理后的图像")
            with st.spinner("正在处理中... 请稍等"):
                # 加载模型
                yolo_model, sam_model = load_models()

                # YOLO 推理
                yolo_results = yolo_model(image)

                for result in yolo_results:
                    boxes = result.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        cls = int(box.cls[0].cpu().numpy())
                        conf = float(box.conf[0].cpu().numpy())

                        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        label = f"{yolo_model.names[cls]} {conf:.2f}"
                        cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                        # SAM 分割
                        results = sam_model(orig_image, bboxes=[x1, y1, x2, y2], save=False)
                        for r in results:
                            masks = r.masks
                            if masks is not None:
                                for mask_data in masks.data:
                                    mask = mask_data.cpu().numpy().astype(np.uint8)
                                    mask = cv2.resize(mask, (image.shape[1], image.shape[0]))
                                    red_mask = cv2.merge([mask * 0, mask * 0, mask * 255])
                                    image = cv2.addWeighted(image, 1, red_mask, 0.5, 0)

                # 显示处理结果
                image_rgb = image[:, :, ::-1]
                st.image(image_rgb, caption="经过 YOLO 和 SAM 处理后的图像", use_container_width=True)
