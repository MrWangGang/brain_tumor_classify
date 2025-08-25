from ultralytics import YOLO, SAM
import cv2
import os
import numpy as np

# 检查 YOLO 模型文件是否存在
yolo_model_path = './model/best.pt'
if not os.path.exists(yolo_model_path):
    print(f"YOLO 模型文件 {yolo_model_path} 不存在，请检查路径。")
else:
    # 加载训练好的 YOLO 模型
    yolo_model = YOLO(yolo_model_path)

    # 检查图片文件是否存在
    image_path = './test_data/11.jpeg'
    if not os.path.exists(image_path):
        print(f"图片文件 {image_path} 不存在，请检查路径。")
    else:
        # 进行 YOLO 推理
        yolo_results = yolo_model(image_path)

        # Load a SAM model
        sam_model = SAM("./model/sam2_l.pt")
        # Display model information (optional)
        sam_model.info()

        # 读取原始图片
        image = cv2.imread(image_path)

        # 处理 YOLO 推理结果
        for result in yolo_results:
            boxes = result.boxes  # 提取边界框信息

            for box in boxes:
                # 获取边界框的坐标
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

                # 获取类别索引
                cls = int(box.cls[0].cpu().numpy())

                # 获取置信度
                conf = float(box.conf[0].cpu().numpy())

                # 在图片上绘制边界框
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # 在图片上显示类别和置信度
                text = f'{yolo_model.names[cls]} {conf:.2f}'
                cv2.putText(image, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                # 使用边界框作为提示进行 SAM 分割
                results = sam_model(image, bboxes=[x1, y1, x2, y2], save=False)

                # 获取分割掩码
                for r in results:
                    masks = r.masks
                    if masks is not None:
                        for mask_data in masks.data:
                            mask = mask_data.cpu().numpy().astype(np.uint8)
                            # 调整掩码大小以匹配图像大小
                            mask = cv2.resize(mask, (image.shape[1], image.shape[0]))
                            # 创建一个红色的蒙版
                            red_mask = cv2.merge([mask * 0, mask * 0, mask * 255])
                            # 将红色蒙版叠加到原始图片上
                            image = cv2.addWeighted(image, 1, red_mask, 0.5, 0)

        # 显示处理后的图片
        cv2.imshow('YOLO and SAM Results', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
