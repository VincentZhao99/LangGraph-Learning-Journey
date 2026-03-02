import streamlit as st
import cv2
import numpy as np
import os
import tempfile
import warnings
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

warnings.filterwarnings("ignore")
load_dotenv()


# ==========================================
# 📐 核心数学公式
# ==========================================
def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0: angle = 360 - angle
    return angle


# ==========================================
# 👁️ 视觉底层引擎 (解耦为独立函数，方便网页实时显示)
# ==========================================
def process_video(input_path, output_path):
    import mediapipe as mp
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose

    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    if fps == 0: fps = 30  # 防止有的视频读不出帧率

    # 💡 架构师级避坑：使用 vp80 编码导出 WebM 格式，保证所有浏览器都能流畅播放！
    fourcc = cv2.VideoWriter_fourcc(*'vp80')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    min_angle = 360.0
    max_angle = 0.0

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark
                shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                            landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                         landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                         landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

                angle = calculate_angle(shoulder, elbow, wrist)

                if angle < min_angle: min_angle = angle
                if angle > max_angle: max_angle = angle

                # 把角度打在视频上
                cv2.putText(image, f"Elbow: {int(angle)}",
                            tuple(np.multiply(elbow, [width, height]).astype(int)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3, cv2.LINE_AA)
                # 画骨骼
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            except:
                pass

            out.write(image)

    cap.release()
    out.release()
    return min_angle, max_angle


# ==========================================
# 🧠 AI 大脑 (生成报告)
# ==========================================
def generate_coach_report(min_angle, max_angle):
    model = ChatOpenAI(
        model='deepseek-chat',
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        openai_api_base=os.getenv("DEEPSEEK_BASE_URL")
    )

    prompt = f"""你是一位拥有20年执教经验的羽毛球金牌私教。
    刚才的计算机视觉系统分析了学员的视频，得出以下绝对精准的骨骼数据：
    - 引拍最深处的手肘夹角：{int(min_angle)}度（优秀标准：45-70度）
    - 击球瞬间的手肘最大夹角：{int(max_angle)}度（优秀标准：160-180度）

    请根据这两个数据，给学员写一份【极其专业、毒舌但带有关怀】的诊断报告。
    指出他的动作问题，并给出3个分阶段的训练建议！使用丰富的 emoji 让排版精美。"""

    response = model.invoke([HumanMessage(content=prompt)])
    return response.content


# ==========================================
# 🖥️ Streamlit 炫酷前端
# ==========================================
st.set_page_config(page_title="AI 鹰眼私教", page_icon="🏸", layout="wide")

st.title("🏸 AI 鹰眼生物力学私教系统 (MVP)")
st.markdown("上传你的挥拍视频，AI 将进行逐帧骨骼追踪，并生成专属教练诊断报告！")
st.info("💡 拍摄建议：请站在学员正侧面（90度）进行拍摄，数据最精准！")

# 1. 文件上传区
uploaded_file = st.file_uploader("📂 请上传挥拍视频 (支持 mp4, mov)", type=['mp4', 'mov'])

if uploaded_file is not None:
    # 把上传的视频暂存到本地，好让 OpenCV 去读
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    input_video_path = tfile.name

    # 准备输出视频的路径 (强制使用 webm)
    output_video_path = input_video_path.replace('.mp4', '_analyzed.webm')

    if st.button("🚀 开始鹰眼诊断", type="primary"):
        # 左右分栏：左边放视频，右边放报告
        col1, col2 = st.columns([1, 1])

        with col1:
            with st.status("👁️ 正在启动鹰眼视觉引擎，逐帧抽离骨骼...", expanded=True) as status_cv:
                # 调用视觉函数
                min_a, max_a = process_video(input_video_path, output_video_path)
                status_cv.update(label="✅ 骨骼解析完毕！", state="complete", expanded=False)

            st.success(f"📊 提取成功：极限引拍 **{int(min_a)}°** | 击球伸展 **{int(max_a)}°**")
            # 💡 直接在网页上播放画好骨骼的慢动作视频！
            st.video(output_video_path)

        with col2:
            with st.status("🧠 金牌教练正在根据数据撰写报告...", expanded=True) as status_llm:
                # 调用大模型生成报告
                report = generate_coach_report(min_a, max_a)
                status_llm.update(label="✅ 诊断报告生成完毕！", state="complete", expanded=False)

            # 展示最终报告
            st.markdown(report)
            st.balloons()