import base64
import cv2
import numpy as np
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from volcenginesdkarkruntime import Ark
from ultralytics import YOLO, SAM
import mysql.connector

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app, origins=["*"])

# 加载模型
yolo_model = YOLO('./model/best.pt')
sam_model = SAM('./model/sam2_l.pt')

# 全局变量存储每个用户的消息列表
user_messages = {}


# 肿瘤类型映射字典
tumor_mapping = {
    'meningioma': '脑膜瘤',
    'glioma': '胶质瘤',
    'pituitoma': '垂体瘤'
}

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key="70350ebf-8687-4837-8b13-568d6a08203b",
)

system_message = {
    "role": "system",
    "content": """
        你现在是脑科专家。如果用户信息中包含 [upload] 指令，请使用如下诊断报告模板生成报告：
        诊断报告：
        姓名：{user_data['name']}
        性别：{user_data['sex']}
        年龄：{user_data['age']}
        就诊日期：{user_data['visit_date']}
        肿瘤类型：{', '.join(user_data['tumor_type'])}
        请根据以上信息进行医学分析，提供治疗建议及后续管理建议。

        当信息中没有包含[upload]指令时，作为脑科专家回答问题,不要生成诊断报告,只回答用户的问题,并且根据生成的诊断报告进行回答
    """
}

# 定义大模型交互函数
def get_medical_report(user_id, prompt, is_upload):
    try:
        # 尝试将 user_id 转换为数字
        user_id = int(user_id)
    except ValueError:
        print(f"无法将 user_id {user_id} 转换为数字类型，可能会影响后续处理。")
    # 若用户消息不存在则新建
    user_messages.setdefault(user_id, [system_message])
    user_messages[user_id].append({"role": "user", "content": prompt})

    # 这里假设client是已经正确初始化的对象
    completion = client.chat.completions.create(
        model="doubao-1-5-lite-32k-250115",
        messages=user_messages[user_id]
    )

    reply = completion.choices[0].message.content
    user_messages[user_id].append({"role": "assistant", "content": reply})

    return reply, user_messages[user_id]

@app.route('/upload_image', methods=['POST'])
def upload_image():
    file = request.files.get('image')
    user_id = request.form.get('user_id')
    if not user_id or not file:
        return jsonify({"error": "缺少 user_id 或 file 参数"}), 400

    user_data = get_user_data(user_id)

    file_bytes = np.asarray(bytearray(file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    yolo_results = yolo_model(image)
    tumor_types = []

    for result in yolo_results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            cls = int(box.cls[0].cpu().numpy())
            conf = float(box.conf[0].cpu().numpy())

            if conf < 0.5:
                continue

            label = f'{yolo_model.names[cls]} ({conf:.2f})'
            label1 = f'{tumor_mapping.get(yolo_model.names[cls])}'
            tumor_types.append(label1)

            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            results = sam_model(image, bboxes=[x1, y1, x2, y2], save=False)
            for r in results:
                if r.masks is not None:
                    for mask in r.masks.data:
                        mask = mask.cpu().numpy().astype(np.uint8)
                        mask = cv2.resize(mask, (image.shape[1], image.shape[0]))
                        red_mask = cv2.merge([mask * 0, mask * 0, mask * 255])
                        image = cv2.addWeighted(image, 1, red_mask, 0.5, 0)

    _, encoded_image = cv2.imencode('.png', image)
    image_base64 = base64.b64encode(encoded_image).decode('utf-8')

    if tumor_types:
        prompt = f"""
        姓名: {user_data['name']}
        性别: {user_data['sex']}
        年龄: {user_data['age']}
        就诊日期: {user_data['visit_date']}
        肿瘤类型: {', '.join(tumor_types)}
        [upload]
        """
        report, _ = get_medical_report(user_id, prompt, True)
        # 连接到 MySQL 数据库
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            # 插入新用户信息
            insert_query = "INSERT INTO t_report (user_id,content, create_time) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (user_id,report, user_data['visit_date']))
            connection.commit()
        except mysql.connector.Error as err:
            print(f"数据库错误: {err}")
            return jsonify({"message": "登录失败，请稍后重试"}), 500
        finally:
            if connection.is_connected():
               cursor.close()
               connection.close()
    else:
        report = "您的检查结果无明显问题，请继续保持健康的生活方式。"

    return jsonify({
        "processedImage": image_base64,
        "report": report
    }), 200

@app.route('/predict', methods=['POST'])
def ask_model():
    user_id = request.json.get('user_id')
    input_text = request.json.get('input_text')
    if not user_id or not input_text:
        return jsonify({"error": "缺少 user_id 或 input_text 参数"}), 400

    reply, messages = get_medical_report(user_id, input_text, False)
    return jsonify({
        "message": reply,
        "messages": messages
    }), 200





#下方的功能是注册和登录的实现
# 配置 MySQL 数据库连接
db_config = {
    'user': 'root',
    'password': 'Ww778899654321,./',
    'host': '127.0.0.1',
    'database': 'brain_tumor_seq'
}


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"message": "未接收到有效数据"}), 400
    account = data.get('account')
    password = data.get('password')

    # 简单的验证
    if not all([account, password]):
        return jsonify({"message": "用户名和密码均为必填项"}), 400

    try:
        # 连接到 MySQL 数据库
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 查询用户信息
        query = "SELECT id FROM t_user WHERE account = %s AND password = %s"
        cursor.execute(query, (account, password))
        user = cursor.fetchone()

        if user:
            user_id = user[0]
            return jsonify({"message": "登录成功", "id": user_id}), 200
        else:
            return jsonify({"message": "用户名或密码错误"}), 401
    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        return jsonify({"message": "登录失败，请稍后重试"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message": "未接收到有效数据"}), 400
    name = data.get('name')
    account = data.get('account')
    password = data.get('password')
    age = data.get('age')
    sex = data.get('sex')

    # 简单的验证
    if not all([name, account, password, age, sex]):
        return jsonify({"message": "所有字段均为必填项"}), 400

    try:
        # 连接到 MySQL 数据库
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # 检查用户名是否已存在
        check_query = "SELECT * FROM t_user WHERE account = %s"
        cursor.execute(check_query, (account,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({"message": "该用户名已被使用"}), 409

        # 插入新用户信息
        insert_query = "INSERT INTO t_user (name, account, password, age, sex) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (name, account, password, age, sex))
        connection.commit()

        return jsonify({"message": "注册成功"}), 201
    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        return jsonify({"message": "注册失败，请稍后重试"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/reports', methods=['GET'])
def get_reports():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "未接收到有效数据"}), 400
    try:
        # 连接到数据库
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 查询 t_report 表
        query = "SELECT create_time, content FROM t_report WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        reports = cursor.fetchall()

        return jsonify(reports)

    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        return jsonify({"error": "数据库错误"}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# 获取用户基础数据
def get_user_data(user_id):
    try:
        # 配置数据库连接
        # 连接到 MySQL 数据库
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # 编写 SQL 查询语句
        query = "SELECT id, name, sex, age FROM t_user WHERE id = %s"
        cursor.execute(query, (user_id,))

        # 获取查询结果
        user = cursor.fetchone()

        if user:
            # 若查询到用户数据，添加访问日期
            user["userId"] = user["id"]
            user["visit_date"] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            del user["id"]
            return user
        else:
            return None

    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)