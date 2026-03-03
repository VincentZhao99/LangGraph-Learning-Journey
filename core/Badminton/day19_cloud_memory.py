import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import sqlite3  # 💡 新增：轻量级数据库
import pandas as pd  # 💡 新增：数据分析与画图神器
from datetime import datetime
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

warnings.filterwarnings("ignore")
load_dotenv()


# ==========================================
# 🗄️ 核心升级一：初始化本地数据库
# ==========================================
def init_db():
    """在项目目录下自动创建一个名叫 badminton_coach.db 的数据库"""
    conn = sqlite3.connect('badminton_coach.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS swing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            action_type TEXT,
            min_angle REAL,
            max_angle REAL,
            analyze_time TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def save_to_db(student_name, action_type, min_angle, max_angle):
    """把算出来的极限数据，连同时间和学员名字，存入数据库"""
    conn = sqlite3.connect('badminton_coach.db')
    c = conn.cursor()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO swing_history (student_name, action_type, min_angle, max_angle, analyze_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (student_name, action_type, min_angle, max_angle, current_time))
    conn.commit()
    conn.close()


def load_student_history(student_name):
    """把某个学员的历史数据全部捞出来，变成 Pandas 表格"""
    conn = sqlite3.connect('badminton_coach.db')
    df = pd.read_sql_query(
        f"SELECT analyze_time, action_type, min_angle, max_angle FROM swing_history WHERE student_name='{student_name}' ORDER BY analyze_time ASC",
        conn)
    conn.close()
    return df


# 确保启动时数据库已建立
init_db()


# ==========================================
# 📐 核心数学公式 & 👁️ 视觉底层 (保持不变)
# ==========================================
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0: angle = 360 - angle
    return angle


def process_video(input_path, output_path, action_type, start_sec, end_sec):
    import mediapipe as mp
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or np.isnan(fps): fps = 30

    start_frame, end_frame = int(start_sec * fps), int(end_sec * fps)
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'vp80'), int(fps), (width, height))
    metrics = {"min_angle": 360.0, "max_angle": 0.0}

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        current_frame = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            if current_frame < start_frame:
                current_frame += 1;
                continue
            if current_frame > end_frame: break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark

                # 防海报过滤网 (Day 18 战果)
                h = max([lm.y for lm in landmarks]) - min([lm.y for lm in landmarks])
                w = max([lm.x for lm in landmarks]) - min([lm.x for lm in landmarks])
                if h > 0.8 or w > 0.6:
                    out.write(image);
                    current_frame += 1;
                    continue

                if action_type == "高远球/杀球 (测上肢发力)":
                    p1, p2, p3 = [landmarks[12].x, landmarks[12].y], [landmarks[14].x, landmarks[14].y], [
                        landmarks[16].x, landmarks[16].y]
                    label = "Elbow"
                else:
                    p1, p2, p3 = [landmarks[24].x, landmarks[24].y], [landmarks[26].x, landmarks[26].y], [
                        landmarks[28].x, landmarks[28].y]
                    label = "Knee"

                angle = calculate_angle(p1, p2, p3)
                if angle < metrics["min_angle"]: metrics["min_angle"] = angle
                if angle > metrics["max_angle"]: metrics["max_angle"] = angle

                cv2.putText(image, f"{label}: {int(angle)}", tuple(np.multiply(p2, [width, height]).astype(int)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3, cv2.LINE_AA)
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            except:
                pass

            out.write(image)
            current_frame += 1

    cap.release()
    out.release()
    return metrics


# ==========================================
# 🧠 AI 大脑 (更新为青少儿温柔鼓励版)
# ==========================================
def generate_coach_report(student_name, action_type, metrics):
    model = ChatOpenAI(
        model='deepseek-chat',
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
    )

    prompt = f"""你是一位极具耐心、专门指导青少年的羽毛球亲子私教。
    你的学员【{student_name}】刚才进行了【{action_type}】训练。CV底层提取的数据如下：
    - 最小夹角（如引拍手肘/下蹲膝盖）：{int(metrics['min_angle'])}度
    - 最大夹角（如击球手肘/蹬地膝盖）：{int(metrics['max_angle'])}度

    请写一份【温柔、幽默、多鼓励】的专属诊断报告。
    1. 大力表扬【{student_name}】的努力。
    2. 用生动形象的比喻（比如拉弓射箭、超级玛丽起跳）指出动作可以优化的点。
    3. 给家长提供 1 个能在家里和孩子一起玩的纠正小游戏。
    排版活泼，多用 可爱/动物 emoji！"""

    response = model.invoke([HumanMessage(content=prompt)])
    return response.content


# ==========================================
# 🖥️ Streamlit 终极双引擎前端 (诊断 + 档案)
# ==========================================
st.set_page_config(page_title="Pro 鹰眼私教舱", page_icon="🏸", layout="wide")
st.title("🏸 AI 羽毛球私教系统 (终极版 🚀)")

# 💡 核心升级二：全局学员绑定
st.sidebar.header("👤 学员信息绑定")
current_student = st.sidebar.text_input("请输入当前学员姓名（用于建立专属档案）", value="天一")

# 💡 核心升级三：多页签布局
tab1, tab2 = st.tabs(["👁️ AI 实时动作诊断", "📈 专属成长档案库"])

# ----------------- 页签 1：干活的诊断舱 -----------------
with tab1:
    action_selection = st.selectbox("🎯 请选择技术动作：", ["高远球/杀球 (测上肢发力)", "网前挑球 (测下肢弓箭步)"])
    uploaded_file = st.file_uploader("📂 请上传挥拍视频", type=['mp4', 'mov'])

    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        input_video_path = tfile.name
        output_video_path = input_video_path.replace('.mp4', '_analyzed.webm')

        cap = cv2.VideoCapture(input_video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = total_frames / fps if fps > 0 else 10.0
        cap.release()

        start_time, end_time = st.slider("✂️ 截取击球前后 2-3 秒精华", 0.0, float(duration),
                                         (0.0, min(3.0, float(duration))), step=0.1)

        if st.button("🚀 开始精准诊断 & 存档", type="primary"):
            col1, col2 = st.columns([1, 1])

            with col1:
                with st.status("👁️ 视觉引擎剥离骨骼中...", expanded=True) as status_cv:
                    metrics = process_video(input_video_path, output_video_path, action_selection, start_time, end_time)
                    # 🗄️ 核心：把跑出来的数据存入本地数据库！
                    save_to_db(current_student, action_selection, metrics["min_angle"], metrics["max_angle"])
                    status_cv.update(label="✅ 骨骼解析并存入档案！", state="complete", expanded=False)

                st.success(
                    f"📊 提取成功：最小夹角 **{int(metrics['min_angle'])}°** | 最大夹角 **{int(metrics['max_angle'])}°**")
                st.video(output_video_path)

            with col2:
                with st.status("🧠 温柔教练撰写报告中...", expanded=True) as status_llm:
                    report = generate_coach_report(current_student, action_selection, metrics)
                    status_llm.update(label="✅ 专属诊断报告完成！", state="complete", expanded=False)
                st.markdown(report)
                st.balloons()

# ----------------- 页签 2：值百万的成长数据面板 -----------------
with tab2:
    st.header(f"🗂️ 【{current_student}】的专属成长轨迹")

    # 捞出当前学员的所有历史数据
    df = load_student_history(current_student)

    if df.empty:
        st.info(f"暂无【{current_student}】的历史数据，请先在左侧进行视频分析。")
    else:
        st.success(f"已检索到 {len(df)} 条历史训练记录！")

        # 筛选出高远球的数据画图
        df_lob = df[df['action_type'] == '高远球/杀球 (测上肢发力)'].copy()

        if not df_lob.empty:
            st.subheader("📉 高远球引拍角度追踪 (越接近 45°-70° 越标准)")
            # 为了画图好看，把时间设为索引
            df_lob['analyze_time'] = pd.to_datetime(df_lob['analyze_time']).dt.strftime('%m-%d %H:%M')
            df_lob.set_index('analyze_time', inplace=True)

            # 📈 绝杀：直接用 Streamlit 画出引拍角度的变化曲线！
            st.line_chart(df_lob['min_angle'], color="#00ff00")

        # 在最下方展示原始数据表格
        st.subheader("📑 原始体检数据表")
        st.dataframe(df, use_container_width=True)